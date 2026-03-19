from django.contrib import admin

from .models import MaintenanceRequest, StaffNote, SupportMessage, UserProfile

admin.site.register(UserProfile)
admin.site.register(MaintenanceRequest)
admin.site.register(SupportMessage)
admin.site.register(StaffNote)
