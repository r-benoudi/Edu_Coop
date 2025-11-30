from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from datetime import date

class Member(models.Model):
    MEMBER_TYPE_CHOICES = [
        ('active', 'Active Member'),
        ('passive', 'Passive Contributor (Public Employee)'),
    ]
    
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    member_type = models.CharField(max_length=10, choices=MEMBER_TYPE_CHOICES, default='active')
    capital_shares = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(Decimal('0'))])
    join_date = models.DateField(default=date.today)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    class Meta:
        ordering = ['last_name', 'first_name']


class Instructor(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    specialization = models.CharField(max_length=200)
    hourly_rate = models.DecimalField(max_digits=8, decimal_places=2, default=120)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    class Meta:
        ordering = ['last_name', 'first_name']


class Course(models.Model):
    COURSE_TYPE_CHOICES = [
        ('tutoring', 'Tutoring'),
        ('it_course', 'IT Course'),
    ]
    
    SUBJECT_CHOICES = [
        ('math', 'Mathematics'),
        ('physics', 'Physics'),
        ('life_sciences', 'Life Sciences'),
        ('it_training', 'IT Training'),
    ]
    
    name = models.CharField(max_length=200)
    course_type = models.CharField(max_length=20, choices=COURSE_TYPE_CHOICES)
    subject = models.CharField(max_length=20, choices=SUBJECT_CHOICES)
    description = models.TextField(blank=True)
    instructors = models.ManyToManyField(Instructor, related_name='courses', blank=True)
    monthly_fee = models.DecimalField(max_digits=8, decimal_places=2)
    enrollment_limit = models.PositiveIntegerField(default=30)
    duration_hours = models.PositiveIntegerField(default=8, help_text="Duration in hours per month")
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_course_type_display()})"
    
    @property
    def enrolled_count(self):
        return self.enrollments.filter(is_active=True).count()
    
    @property
    def available_slots(self):
        return self.enrollment_limit - self.enrolled_count
    
    class Meta:
        ordering = ['name']


class Student(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    parent_name = models.CharField(max_length=200, blank=True)
    parent_phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    registration_date = models.DateField(default=date.today)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def total_monthly_fees(self):
        return sum(e.course.monthly_fee for e in self.enrollments.filter(is_active=True))
    
    class Meta:
        ordering = ['last_name', 'first_name']


class Enrollment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrollment_date = models.DateField(default=date.today)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.student} - {self.course}"
    
    class Meta:
        unique_together = ['student', 'course']
        ordering = ['-enrollment_date']


class Attendance(models.Model):
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('excused', 'Excused'),
    ]
    
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='present')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.enrollment.student} - {self.date} - {self.status}"
    
    class Meta:
        unique_together = ['enrollment', 'date']
        ordering = ['-date']


class Payment(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('partial', 'Partial'),
        ('overdue', 'Overdue'),
    ]
    
    PAYMENT_TYPE_CHOICES = [
        ('student_fee', 'Student Fee'),
        ('instructor_payment', 'Instructor Payment'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='payments', null=True, blank=True)
    instructor = models.ForeignKey(Instructor, on_delete=models.CASCADE, related_name='payments', null=True, blank=True)
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    month = models.DateField(help_text="First day of the billing month")
    status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default='pending')
    payment_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        if self.student:
            return f"Payment: {self.student} - {self.month.strftime('%B %Y')}"
        return f"Payment: {self.instructor} - {self.month.strftime('%B %Y')}"
    
    @property
    def remaining_amount(self):
        return self.amount - self.amount_paid
    
    class Meta:
        ordering = ['-month', '-created_at']


class InstructorHours(models.Model):
    instructor = models.ForeignKey(Instructor, on_delete=models.CASCADE, related_name='hours')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='instructor_hours')
    month = models.DateField(help_text="First day of the month")
    hours_worked = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('8'))])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.instructor} - {self.course} - {self.month.strftime('%B %Y')}"
    
    class Meta:
        unique_together = ['instructor', 'course', 'month']
        ordering = ['-month']


class FinancialReport(models.Model):
    month = models.DateField(unique=True, help_text="First day of the reporting month")
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_instructor_payments = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_expenses = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    gross_profit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_profit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_finalized = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Financial Report - {self.month.strftime('%B %Y')}"
    
    class Meta:
        ordering = ['-month']


class ProfitDistribution(models.Model):
    financial_report = models.ForeignKey(FinancialReport, on_delete=models.CASCADE, related_name='distributions')
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='profit_distributions')
    share_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    is_paid = models.BooleanField(default=False)
    payment_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.member} - {self.financial_report.month.strftime('%B %Y')} - {self.amount} DH"
    
    class Meta:
        unique_together = ['financial_report', 'member']
        ordering = ['-created_at']

# ==============================================================================
# AUTHENTICATION & EXPENSE TRACKING MODELS
# Add these to your core/models.py file
# ==============================================================================

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from datetime import date

# ==============================================================================
# CUSTOM USER MODEL WITH ROLES
# ==============================================================================

class User(AbstractUser):
    """
    Custom User model with role-based access control
    """
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
        'Instructor', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='user_account'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"
    
    @property
    def is_admin(self):
        return self.role == 'admin' or self.is_superuser
    
    @property
    def is_manager(self):
        return self.role in ['admin', 'manager'] or self.is_superuser
    
    @property
    def is_accountant(self):
        return self.role in ['admin', 'accountant'] or self.is_superuser
    
    @property
    def can_view_financials(self):
        return self.role in ['admin', 'manager', 'accountant'] or self.is_superuser
    
    class Meta:
        ordering = ['-date_joined']


# ==============================================================================
# EXPENSE TRACKING
# ==============================================================================

class ExpenseCategory(models.Model):
    """
    Categories for operational expenses
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Expense Categories'


class Expense(models.Model):
    """
    Track all operational expenses: rent, utilities, supplies, etc.
    """
    EXPENSE_TYPE_CHOICES = [
        ('rent', 'Rent'),
        ('utilities', 'Utilities'),
        ('supplies', 'Supplies (Papers, etc.)'),
        ('maintenance', 'Maintenance'),
        ('marketing', 'Marketing'),
        ('insurance', 'Insurance'),
        ('salaries', 'Administrative Salaries'),
        ('technology', 'Technology/Software'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('paid', 'Paid'),
        ('rejected', 'Rejected'),
    ]
    
    expense_type = models.CharField(max_length=20, choices=EXPENSE_TYPE_CHOICES)
    category = models.ForeignKey(
        ExpenseCategory, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='expenses'
    )
    description = models.TextField()
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    expense_date = models.DateField(default=date.today)
    month = models.DateField(help_text="First day of the billing month")
    
    # Approval workflow
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    submitted_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='submitted_expenses'
    )
    approved_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='approved_expenses'
    )
    approval_date = models.DateField(null=True, blank=True)
    
    # Payment tracking
    paid_date = models.DateField(null=True, blank=True)
    payment_method = models.CharField(max_length=50, blank=True)
    receipt_number = models.CharField(max_length=100, blank=True)
    
    # Supporting documents
    receipt_file = models.FileField(upload_to='expenses/receipts/', null=True, blank=True)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.get_expense_type_display()} - {self.amount} DH - {self.expense_date}"
    
    @property
    def is_paid(self):
        return self.status == 'paid'
    
    @property
    def needs_approval(self):
        return self.status == 'pending'
    
    class Meta:
        ordering = ['-expense_date', '-created_at']


class RecurringExpense(models.Model):
    """
    Manage recurring expenses (rent, utilities, etc.)
    """
    FREQUENCY_CHOICES = [
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ]
    
    name = models.CharField(max_length=200)
    expense_type = models.CharField(max_length=20, choices=Expense.EXPENSE_TYPE_CHOICES)
    category = models.ForeignKey(
        ExpenseCategory, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='monthly')
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    auto_generate = models.BooleanField(
        default=True,
        help_text="Automatically generate expense records"
    )
    last_generated = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.amount} DH ({self.get_frequency_display()})"
    
    class Meta:
        ordering = ['name']


# ==============================================================================
# AUDIT LOG
# ==============================================================================

class AuditLog(models.Model):
    """
    Track all important actions in the system
    """
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('approve', 'Approve'),
        ('reject', 'Reject'),
        ('payment', 'Payment'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user} - {self.action} - {self.model_name} - {self.timestamp}"
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
