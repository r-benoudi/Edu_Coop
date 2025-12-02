from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """Custom User with role-based access"""
    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('manager', 'Manager'),
        ('accountant', 'Accountant'),
        ('instructor', 'Instructor'),
        ('staff', 'Staff'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='staff')
    phone = models.CharField(max_length=20, blank=True)
    instructor_profile = models.OneToOneField(
        'academics.Instructor', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='user_account'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    @property
    def is_admin(self):
        return self.role == 'admin' or self.is_superuser
    
    @property
    def is_manager(self):
        return self.role in ['admin', 'manager'] or self.is_superuser
    
    @property
    def can_view_financials(self):
        return self.role in ['admin', 'manager', 'accountant'] or self.is_superuser