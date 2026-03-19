import json

from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .models import MaintenanceRequest, StaffNote, SupportMessage, UserProfile


# ---------------------------------------------------------------------------
# Page views
#
# Role-based access pattern: each dashboard view checks the user's role via
# UserProfile and raises PermissionDenied for any mismatch. This keeps
# authorisation logic co-located with the view rather than in middleware.
#
# Data delivery: rather than separate AJAX calls on page load, each dashboard
# view serialises the required querysets to JSON and embeds them directly in
# the template context. This means a single HTTP request fully loads the page
# and the JS can render the SPA-style views without additional round trips.
# ---------------------------------------------------------------------------

def login(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        user = authenticate(request, username=email, password=password)
        if user:
            auth_login(request, user)
            role = user.userprofile.role
            if role == 'admin':
                return redirect('maintenance_admin')
            elif role == 'tenant':
                return redirect('tenant')
            elif role == 'worker':
                return redirect('staff')
        return render(request, 'maintenance_app/login.html', {'error': 'Incorrect email or password.'})
    return render(request, 'maintenance_app/login.html')


def logout_view(request):
    auth_logout(request)
    return redirect('login')


def register(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid request.'}, status=400)
        name = data.get('name', '')
        email = data.get('email', '')
        password = data.get('password', '')
        role = data.get('role', 'tenant')
        if User.objects.filter(username=email).exists():
            return JsonResponse({'error': 'This email is already registered.'}, status=400)
        user = User.objects.create_user(username=email, email=email, password=password, first_name=name)
        UserProfile.objects.create(user=user, role=role)
        return JsonResponse({'ok': True})
    return render(request, 'maintenance_app/login.html')


@login_required(login_url='login')
def maintenance_admin(request):
    if request.user.userprofile.role != 'admin':
        raise PermissionDenied

    users_data = [
        {'id': p.user.id, 'name': p.user.get_full_name() or p.user.username, 'email': p.user.email, 'role': p.role}
        for p in UserProfile.objects.select_related('user').all()
    ]
    requests_data = [
        {'id': r.id, 'title': r.title, 'owner': r.owner.email, 'urgency': r.urgency,
         'status': r.status, 'location': r.location, 'date': str(r.date)}
        for r in MaintenanceRequest.objects.select_related('owner').all()
    ]
    messages_data = [
        {'id': m.id, 'from': (m.sender.get_full_name() or m.sender.username) + ' (Tenant)',
         'date': m.date.strftime('%Y-%m-%d %H:%M'), 'msg': m.body}
        for m in SupportMessage.objects.select_related('sender').order_by('-date')
    ]

    return render(request, 'maintenance_app/admin.html', {
        'user_name': request.user.get_full_name() or request.user.username,
        'user_email': request.user.email,
        'user_avatar': request.user.userprofile.avatar,
        'users_json': json.dumps(users_data),
        'requests_json': json.dumps(requests_data),
        'messages_json': json.dumps(messages_data),
    })


@login_required(login_url='login')
def staff(request):
    if request.user.userprofile.role != 'worker':
        raise PermissionDenied

    requests_data = [
        {'id': r.id, 'title': r.title, 'owner': r.owner.email, 'urgency': r.urgency,
         'status': r.status, 'location': r.location, 'date': str(r.date), 'detail': r.detail}
        for r in MaintenanceRequest.objects.select_related('owner').all()
    ]
    try:
        note_body = request.user.note.body
    except StaffNote.DoesNotExist:
        note_body = ''

    return render(request, 'maintenance_app/staff.html', {
        'user_name': request.user.get_full_name() or request.user.username,
        'user_email': request.user.email,
        'user_phone': request.user.userprofile.phone,
        'user_avatar': request.user.userprofile.avatar,
        'requests_json': json.dumps(requests_data),
        'note_body_json': json.dumps(note_body),
    })


@login_required(login_url='login')
def tenant(request):
    if request.user.userprofile.role != 'tenant':
        raise PermissionDenied

    requests_data = [
        {'id': r.id, 'title': r.title, 'urgency': r.urgency,
         'status': r.status, 'location': r.location, 'date': str(r.date)}
        for r in MaintenanceRequest.objects.filter(owner=request.user).order_by('-date')
    ]

    return render(request, 'maintenance_app/tenant.html', {
        'user_name': request.user.get_full_name() or request.user.username,
        'user_email': request.user.email,
        'user_phone': request.user.userprofile.phone,
        'user_avatar': request.user.userprofile.avatar,
        'requests_json': json.dumps(requests_data),
    })


# ---------------------------------------------------------------------------
# API endpoints (all POST, return JSON)
#
# All mutation endpoints are POST-only and protected by @login_required so
# they cannot be triggered by unauthenticated cross-site requests. CSRF
# protection is handled by Django middleware; the JS helper in base.js
# includes the csrftoken cookie value in the X-CSRFToken request header.
# ---------------------------------------------------------------------------

@login_required
@require_POST
def api_users_add(request):
    data = json.loads(request.body)
    email = data.get('email', '')
    if User.objects.filter(username=email).exists():
        return JsonResponse({'error': 'Email already in use.'}, status=400)
    user = User.objects.create_user(
        username=email, email=email,
        password='changeme123',
        first_name=data.get('name', ''),
    )
    UserProfile.objects.create(user=user, role=data.get('role', 'tenant'))
    return JsonResponse({'user': {'id': user.id, 'name': data.get('name', ''), 'email': email, 'role': data.get('role', 'tenant')}})


@login_required
@require_POST
def api_users_edit(request, user_id):
    data = json.loads(request.body)
    try:
        user = User.objects.select_related('userprofile').get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found.'}, status=404)
    user.first_name = data.get('name', user.first_name)
    email = data.get('email', user.email)
    user.email = email
    user.username = email
    user.save()
    user.userprofile.role = data.get('role', user.userprofile.role)
    user.userprofile.save()
    return JsonResponse({'ok': True})


@login_required
@require_POST
def api_users_delete(request, user_id):
    User.objects.filter(id=user_id).delete()
    return JsonResponse({'ok': True})


@login_required
@require_POST
def api_requests_delete(request, request_id):
    MaintenanceRequest.objects.filter(id=request_id).delete()
    return JsonResponse({'ok': True})


@login_required
@require_POST
def api_messages_clear(request):
    SupportMessage.objects.all().delete()
    return JsonResponse({'ok': True})


@login_required
@require_POST
def api_request_create(request):
    data = json.loads(request.body)
    req = MaintenanceRequest.objects.create(
        owner=request.user,
        title=data['title'],
        location=data['location'],
        urgency=data.get('urgency', 'Normal'),
        detail=data.get('detail', ''),
    )
    return JsonResponse({'request': {
        'id': req.id, 'title': req.title, 'urgency': req.urgency,
        'status': req.status, 'location': req.location, 'date': str(req.date),
    }})


@login_required
@require_POST
def api_request_cancel(request, request_id):
    deleted, _ = MaintenanceRequest.objects.filter(
        id=request_id, owner=request.user, status='Pending'
    ).delete()
    if not deleted:
        return JsonResponse({'error': 'Request not found or cannot be cancelled.'}, status=404)
    return JsonResponse({'ok': True})


@login_required
@require_POST
def api_request_status(request, request_id):
    data = json.loads(request.body)
    updated = MaintenanceRequest.objects.filter(id=request_id).update(status=data['status'])
    if not updated:
        return JsonResponse({'error': 'Request not found.'}, status=404)
    return JsonResponse({'ok': True})


@login_required
@require_POST
def api_profile_update(request):
    data = json.loads(request.body)
    user = request.user
    if 'name' in data:
        user.first_name = data['name']
        user.save()
    profile_dirty = False
    if 'phone' in data:
        user.userprofile.phone = data['phone']
        profile_dirty = True
    if 'avatar' in data:
        user.userprofile.avatar = data['avatar']
        profile_dirty = True
    if profile_dirty:
        user.userprofile.save()
    return JsonResponse({'ok': True})


@login_required
@require_POST
def api_message_send(request):
    data = json.loads(request.body)
    SupportMessage.objects.create(sender=request.user, body=data['msg'])
    return JsonResponse({'ok': True})


@login_required
@require_POST
def api_notes_save(request):
    data = json.loads(request.body)
    note, _ = StaffNote.objects.get_or_create(author=request.user)
    note.body = data.get('body', '')
    note.save()
    return JsonResponse({'ok': True})
