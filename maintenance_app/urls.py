from django.urls import path

from . import views

urlpatterns = [
    # --- Page views (server-rendered dashboards) ---
    path("", views.login, name="login"),
    path("login/", views.login, name="login"),
    path("register/", views.register, name="register"),
    path("maintenance_admin/", views.maintenance_admin, name="maintenance_admin"),
    path("staff/", views.staff, name="staff"),
    path("tenant/", views.tenant, name="tenant"),
    path("logout/", views.logout_view, name="logout"),

    # --- API endpoints (POST-only, return JSON) ---
    # User management (admin only)
    path("api/users/add/", views.api_users_add, name="api_users_add"),
    path("api/users/<int:user_id>/edit/", views.api_users_edit, name="api_users_edit"),
    path("api/users/<int:user_id>/delete/", views.api_users_delete, name="api_users_delete"),
    # Maintenance requests
    path("api/requests/create/", views.api_request_create, name="api_request_create"),
    path("api/requests/<int:request_id>/delete/", views.api_requests_delete, name="api_requests_delete"),
    path("api/requests/<int:request_id>/cancel/", views.api_request_cancel, name="api_request_cancel"),
    path("api/requests/<int:request_id>/status/", views.api_request_status, name="api_request_status"),
    # Support messages
    path("api/messages/send/", views.api_message_send, name="api_message_send"),
    path("api/messages/clear/", views.api_messages_clear, name="api_messages_clear"),
    # Profile and staff notes
    path("api/profile/update/", views.api_profile_update, name="api_profile_update"),
    path("api/notes/save/", views.api_notes_save, name="api_notes_save"),
]
