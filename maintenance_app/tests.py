import json

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from .models import MaintenanceRequest, StaffNote, SupportMessage, UserProfile


class SetUpMixin:
    """Shared helper to create test users."""

    def make_user(self, email, role, name='Test User'):
        user = User.objects.create_user(
            username=email, email=email,
            password='testpass123', first_name=name,
        )
        UserProfile.objects.create(user=user, role=role)
        return user


# ---------------------------------------------------------------------------
# 1. Model tests
# ---------------------------------------------------------------------------

class ModelTests(SetUpMixin, TestCase):

    def test_userprofile_created(self):
        user = self.make_user('admin@test.com', 'admin')
        self.assertEqual(user.userprofile.role, 'admin')

    def test_maintenance_request_defaults(self):
        tenant = self.make_user('tenant@test.com', 'tenant')
        req = MaintenanceRequest.objects.create(
            owner=tenant, title='Broken tap',
            location='Kitchen', urgency='Normal',
        )
        self.assertEqual(req.status, 'Pending')
        self.assertIsNotNone(req.date)

    def test_support_message_saved(self):
        tenant = self.make_user('tenant@test.com', 'tenant')
        msg = SupportMessage.objects.create(sender=tenant, body='Hello')
        self.assertEqual(SupportMessage.objects.count(), 1)
        self.assertEqual(msg.sender, tenant)

    def test_staff_note_one_per_user(self):
        worker = self.make_user('staff@test.com', 'worker')
        StaffNote.objects.create(author=worker, body='My note')
        with self.assertRaises(Exception):
            StaffNote.objects.create(author=worker, body='Duplicate')


# ---------------------------------------------------------------------------
# 2. Page access / auth tests
# ---------------------------------------------------------------------------

class PageAccessTests(SetUpMixin, TestCase):

    def setUp(self):
        self.client = Client()
        self.admin  = self.make_user('admin@test.com',  'admin',  'Admin User')
        self.worker = self.make_user('staff@test.com',  'worker', 'Staff User')
        self.tenant = self.make_user('tenant@test.com', 'tenant', 'Tenant User')

    def test_unauthenticated_redirected_from_staff(self):
        response = self.client.get(reverse('staff'))
        self.assertRedirects(response, '/login/?next=/staff/')

    def test_unauthenticated_redirected_from_admin(self):
        response = self.client.get(reverse('maintenance_admin'))
        self.assertRedirects(response, '/login/?next=/maintenance_admin/')

    def test_tenant_cannot_access_admin_page(self):
        self.client.force_login(self.tenant)
        response = self.client.get(reverse('maintenance_admin'))
        self.assertEqual(response.status_code, 403)

    def test_worker_cannot_access_tenant_page(self):
        self.client.force_login(self.worker)
        response = self.client.get(reverse('tenant'))
        self.assertEqual(response.status_code, 403)

    def test_admin_can_access_admin_page(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse('maintenance_admin'))
        self.assertEqual(response.status_code, 200)

    def test_login_redirects_tenant_to_dashboard(self):
        response = self.client.post(reverse('login'), {
            'email': 'tenant@test.com', 'password': 'testpass123',
        })
        self.assertRedirects(response, reverse('tenant'))

    def test_login_redirects_worker_to_staff(self):
        response = self.client.post(reverse('login'), {
            'email': 'staff@test.com', 'password': 'testpass123',
        })
        self.assertRedirects(response, reverse('staff'))

    def test_login_redirects_admin_to_admin(self):
        response = self.client.post(reverse('login'), {
            'email': 'admin@test.com', 'password': 'testpass123',
        })
        self.assertRedirects(response, reverse('maintenance_admin'))

    def test_login_wrong_password_shows_error(self):
        response = self.client.post(reverse('login'), {
            'email': 'tenant@test.com', 'password': 'wrongpass',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Incorrect email or password')

    def test_logout_redirects_to_login(self):
        self.client.force_login(self.tenant)
        response = self.client.get(reverse('logout'))
        self.assertRedirects(response, reverse('login'))

    def test_register_creates_user_and_redirects(self):
        response = self.client.post(reverse('register'),
            json.dumps({'name': 'New Tenant', 'email': 'new@test.com',
                        'password': 'pass123', 'role': 'tenant'}),
            content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(email='new@test.com').exists())

    def test_register_duplicate_email_shows_error(self):
        response = self.client.post(reverse('register'),
            json.dumps({'name': 'Dup', 'email': 'tenant@test.com',
                        'password': 'pass123', 'role': 'tenant'}),
            content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('already registered', response.json()['error'])


# ---------------------------------------------------------------------------
# 3. API endpoint tests
# ---------------------------------------------------------------------------

class ApiTests(SetUpMixin, TestCase):

    def setUp(self):
        self.client = Client()
        self.admin  = self.make_user('admin@test.com',  'admin',  'Admin User')
        self.worker = self.make_user('staff@test.com',  'worker', 'Staff User')
        self.tenant = self.make_user('tenant@test.com', 'tenant', 'Tenant User')

    def _post(self, url_name, data, user=None, **url_kwargs):
        if user:
            self.client.force_login(user)
        return self.client.post(
            reverse(url_name, kwargs=url_kwargs or None),
            data=json.dumps(data),
            content_type='application/json',
        )

    # --- Maintenance requests ---

    def test_tenant_can_create_request(self):
        response = self._post('api_request_create', {
            'title': 'Leaky pipe', 'location': 'Bathroom',
            'urgency': 'High', 'detail': 'Water everywhere',
        }, user=self.tenant)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('request', data)
        self.assertEqual(data['request']['title'], 'Leaky pipe')
        self.assertEqual(MaintenanceRequest.objects.count(), 1)

    def test_unauthenticated_cannot_create_request(self):
        response = self.client.post(
            reverse('api_request_create'),
            data=json.dumps({'title': 'Test'}),
            content_type='application/json',
        )
        self.assertNotEqual(response.status_code, 200)

    def test_staff_can_update_request_status(self):
        req = MaintenanceRequest.objects.create(
            owner=self.tenant, title='Broken boiler',
            location='Kitchen', urgency='High',
        )
        response = self._post(
            'api_request_status', {'status': 'In Progress'},
            user=self.worker, request_id=req.id,
        )
        self.assertEqual(response.status_code, 200)
        req.refresh_from_db()
        self.assertEqual(req.status, 'In Progress')

    def test_staff_can_mark_request_fixed(self):
        req = MaintenanceRequest.objects.create(
            owner=self.tenant, title='Broken boiler',
            location='Kitchen', urgency='High', status='In Progress',
        )
        self._post('api_request_status', {'status': 'Fixed'}, user=self.worker, request_id=req.id)
        req.refresh_from_db()
        self.assertEqual(req.status, 'Fixed')

    def test_tenant_can_cancel_pending_request(self):
        req = MaintenanceRequest.objects.create(
            owner=self.tenant, title='Old issue',
            location='Bedroom', urgency='Normal',
        )
        response = self._post('api_request_cancel', {}, user=self.tenant, request_id=req.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(MaintenanceRequest.objects.count(), 0)

    def test_tenant_cannot_cancel_fixed_request(self):
        req = MaintenanceRequest.objects.create(
            owner=self.tenant, title='Fixed issue',
            location='Bedroom', urgency='Normal', status='Fixed',
        )
        response = self._post('api_request_cancel', {}, user=self.tenant, request_id=req.id)
        self.assertEqual(response.status_code, 404)

    def test_tenant_cannot_cancel_another_tenants_request(self):
        other = self.make_user('other@test.com', 'tenant')
        req = MaintenanceRequest.objects.create(
            owner=other, title='Their issue',
            location='Kitchen', urgency='Normal',
        )
        response = self._post('api_request_cancel', {}, user=self.tenant, request_id=req.id)
        self.assertEqual(response.status_code, 404)

    def test_admin_can_delete_request(self):
        req = MaintenanceRequest.objects.create(
            owner=self.tenant, title='To delete',
            location='Kitchen', urgency='Normal',
        )
        response = self._post('api_requests_delete', {}, user=self.admin, request_id=req.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(MaintenanceRequest.objects.count(), 0)

    # --- Users ---

    def test_admin_can_add_user(self):
        response = self._post('api_users_add', {
            'name': 'New Worker', 'email': 'newworker@test.com', 'role': 'worker',
        }, user=self.admin)
        self.assertEqual(response.status_code, 200)
        self.assertIn('user', response.json())
        self.assertTrue(User.objects.filter(email='newworker@test.com').exists())

    def test_add_user_duplicate_email_returns_error(self):
        response = self._post('api_users_add', {
            'name': 'Dup', 'email': 'tenant@test.com', 'role': 'tenant',
        }, user=self.admin)
        self.assertIn('error', response.json())

    def test_admin_can_edit_user(self):
        response = self._post(
            'api_users_edit', {'name': 'Updated Name', 'email': 'tenant@test.com', 'role': 'tenant'},
            user=self.admin, user_id=self.tenant.id,
        )
        self.assertEqual(response.status_code, 200)
        self.tenant.refresh_from_db()
        self.assertEqual(self.tenant.first_name, 'Updated Name')

    def test_admin_can_delete_user(self):
        target = self.make_user('todelete@test.com', 'tenant')
        response = self._post('api_users_delete', {}, user=self.admin, user_id=target.id)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(email='todelete@test.com').exists())

    # --- Messages ---

    def test_tenant_can_send_support_message(self):
        response = self._post('api_message_send', {'msg': 'Need help urgently'}, user=self.tenant)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(SupportMessage.objects.count(), 1)
        self.assertEqual(SupportMessage.objects.first().body, 'Need help urgently')

    def test_admin_can_clear_messages(self):
        SupportMessage.objects.create(sender=self.tenant, body='msg1')
        SupportMessage.objects.create(sender=self.tenant, body='msg2')
        response = self._post('api_messages_clear', {}, user=self.admin)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(SupportMessage.objects.count(), 0)

    # --- Profile ---

    def test_profile_update_saves_name(self):
        self._post('api_profile_update', {'name': 'New Name'}, user=self.tenant)
        self.tenant.refresh_from_db()
        self.assertEqual(self.tenant.first_name, 'New Name')

    def test_profile_update_saves_phone(self):
        self._post('api_profile_update', {'phone': '07700900000'}, user=self.tenant)
        self.tenant.userprofile.refresh_from_db()
        self.assertEqual(self.tenant.userprofile.phone, '07700900000')

    # --- Staff notes ---

    def test_staff_note_created_on_save(self):
        self._post('api_notes_save', {'body': 'First note'}, user=self.worker)
        self.assertEqual(StaffNote.objects.get(author=self.worker).body, 'First note')

    def test_staff_note_updated_not_duplicated(self):
        self._post('api_notes_save', {'body': 'First note'}, user=self.worker)
        self._post('api_notes_save', {'body': 'Updated note'}, user=self.worker)
        self.assertEqual(StaffNote.objects.filter(author=self.worker).count(), 1)
        self.assertEqual(StaffNote.objects.get(author=self.worker).body, 'Updated note')
