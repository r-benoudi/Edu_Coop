from django.db import models
from decimal import Decimal
from datetime import date

class Member(models.Model):
    """Cooperative member"""
    MEMBER_TYPE_CHOICES = [
        ('active', 'Active Member'),
        ('passive', 'Passive Contributor'),
    ]
    
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    member_type = models.CharField(max_length=10, choices=MEMBER_TYPE_CHOICES)
    capital_shares = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    join_date = models.DateField(default=date.today)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

class ProfitDistribution(models.Model):
    """Profit distribution to members"""
    financial_report = models.ForeignKey('finance.FinancialReport', on_delete=models.CASCADE)
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    share_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    is_paid = models.BooleanField(default=False)
    payment_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)