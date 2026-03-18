from django.contrib.auth.models import User
from django.db import models


class UserProfile(models.Model):
    ROLE_CHOICES = [('admin', 'Admin'), ('worker', 'Worker'), ('tenant', 'Tenant')]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    phone = models.CharField(max_length=20, blank=True)
    avatar = models.TextField(blank=True)  # base64 data URL


class MaintenanceRequest(models.Model):
    URGENCY_CHOICES = [('Normal', 'Normal'), ('High', 'High')]
    STATUS_CHOICES = [('Pending', 'Pending'), ('In Progress', 'In Progress'), ('Fixed', 'Fixed')]
    LOCATION_CHOICES = [
        ('Living Room', 'Living Room'), ('Kitchen', 'Kitchen'),
        ('Bedroom', 'Bedroom'), ('Bathroom', 'Bathroom'), ('Balcony', 'Balcony'),
    ]
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='requests')
    title = models.CharField(max_length=200)
    detail = models.TextField(blank=True)
    location = models.CharField(max_length=50, choices=LOCATION_CHOICES)
    urgency = models.CharField(max_length=10, choices=URGENCY_CHOICES, default='Normal')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    date = models.DateField(auto_now_add=True)


class SupportMessage(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='support_messages')
    body = models.TextField()
    date = models.DateTimeField(auto_now_add=True)


class StaffNote(models.Model):
    # Per-worker scratchpad, one note per worker
    author = models.OneToOneField(User, on_delete=models.CASCADE, related_name='note')
    body = models.TextField(blank=True)
    updated = models.DateTimeField(auto_now=True)
