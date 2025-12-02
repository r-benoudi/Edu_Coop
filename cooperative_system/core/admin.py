# from django.contrib import admin
# from .models import (
#     Student, Instructor, Course, Enrollment, Attendance,
#     Payment, Member, InstructorHours, FinancialReport, ProfitDistribution
# )

# @admin.register(Student)
# class StudentAdmin(admin.ModelAdmin):
#     list_display = ['full_name', 'email', 'phone', 'registration_date', 'is_active']
#     list_filter = ['is_active', 'registration_date']
#     search_fields = ['first_name', 'last_name', 'email']
#     date_hierarchy = 'registration_date'


# @admin.register(Instructor)
# class InstructorAdmin(admin.ModelAdmin):
#     list_display = ['full_name', 'email', 'specialization', 'hourly_rate', 'is_active']
#     list_filter = ['is_active', 'specialization']
#     search_fields = ['first_name', 'last_name', 'email', 'specialization']


# @admin.register(Course)
# class CourseAdmin(admin.ModelAdmin):
#     list_display = ['name', 'course_type', 'subject', 'monthly_fee', 'enrolled_count', 'enrollment_limit', 'is_active']
#     list_filter = ['course_type', 'subject', 'is_active']
#     search_fields = ['name', 'description']
#     filter_horizontal = ['instructors']


# @admin.register(Enrollment)
# class EnrollmentAdmin(admin.ModelAdmin):
#     list_display = ['student', 'course', 'enrollment_date', 'is_active']
#     list_filter = ['is_active', 'enrollment_date', 'course']
#     search_fields = ['student__first_name', 'student__last_name', 'course__name']
#     date_hierarchy = 'enrollment_date'


# @admin.register(Attendance)
# class AttendanceAdmin(admin.ModelAdmin):
#     list_display = ['enrollment', 'date', 'status']
#     list_filter = ['status', 'date']
#     date_hierarchy = 'date'


# @admin.register(Payment)
# class PaymentAdmin(admin.ModelAdmin):
#     list_display = ['payment_type', 'student', 'instructor', 'amount', 'amount_paid', 'status', 'month']
#     list_filter = ['payment_type', 'status', 'month']
#     search_fields = ['student__first_name', 'student__last_name', 'instructor__first_name', 'instructor__last_name']
#     date_hierarchy = 'month'


# @admin.register(Member)
# class MemberAdmin(admin.ModelAdmin):
#     list_display = ['full_name', 'email', 'member_type', 'capital_shares', 'join_date', 'is_active']
#     list_filter = ['member_type', 'is_active']
#     search_fields = ['first_name', 'last_name', 'email']


# @admin.register(InstructorHours)
# class InstructorHoursAdmin(admin.ModelAdmin):
#     list_display = ['instructor', 'course', 'month', 'hours_worked']
#     list_filter = ['month', 'instructor', 'course']
#     date_hierarchy = 'month'


# @admin.register(FinancialReport)
# class FinancialReportAdmin(admin.ModelAdmin):
#     list_display = ['month', 'total_revenue', 'total_instructor_payments', 'net_profit', 'is_finalized']
#     list_filter = ['is_finalized', 'month']
#     date_hierarchy = 'month'


# @admin.register(ProfitDistribution)
# class ProfitDistributionAdmin(admin.ModelAdmin):
#     list_display = ['member', 'financial_report', 'share_percentage', 'amount', 'is_paid']
#     list_filter = ['is_paid', 'financial_report']

# ==============================================================================
# COMPLETE ADMIN.PY WITH AUTHENTICATION & EXPENSE MODELS
# Replace your entire core/admin.py with this file
# ==============================================================================

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User
)
from academics.models import Student, Instructor, Course, Enrollment, Attendance, InstructorHours
from audit.models import AuditLog
from finance.models import Payment, FinancialReport, Expense, RecurringExpense, ExpenseCategory
from cooperative.models import Member, ProfitDistribution

# ==============================================================================
# AUTHENTICATION & USER MANAGEMENT
# ==============================================================================

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Enhanced User admin with role management"""
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'is_active', 'date_joined']
    list_filter = ['role', 'is_active', 'is_staff', 'is_superuser', 'date_joined']
    search_fields = ['username', 'first_name', 'last_name', 'email']
    ordering = ['-date_joined']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Information', {
            'fields': ('role', 'phone', 'instructor_profile')
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Information', {
            'fields': ('role', 'phone', 'email', 'first_name', 'last_name')
        }),
    )


# ==============================================================================
# STUDENT & COURSE MANAGEMENT
# ==============================================================================

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'phone', 'registration_date', 'is_active']
    list_filter = ['is_active', 'registration_date']
    search_fields = ['first_name', 'last_name', 'email', 'phone']
    date_hierarchy = 'registration_date'
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Instructor)
class InstructorAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'specialization', 'hourly_rate', 'is_active']
    list_filter = ['is_active', 'specialization']
    search_fields = ['first_name', 'last_name', 'email', 'specialization']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['name', 'course_type', 'subject', 'monthly_fee', 'enrollment_limit', 'is_active']
    list_filter = ['course_type', 'subject', 'is_active']
    search_fields = ['name', 'description']
    filter_horizontal = ['instructors']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'enrollment_date', 'is_active']
    list_filter = ['is_active', 'enrollment_date', 'course']
    search_fields = ['student__first_name', 'student__last_name', 'course__name']
    date_hierarchy = 'enrollment_date'
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['enrollment', 'date', 'status']
    list_filter = ['status', 'date']
    search_fields = ['enrollment__student__first_name', 'enrollment__student__last_name']
    date_hierarchy = 'date'
    readonly_fields = ['created_at', 'updated_at']


# ==============================================================================
# FINANCIAL MANAGEMENT
# ==============================================================================

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['payment_type', 'student', 'instructor', 'amount', 'amount_paid', 'status', 'month']
    list_filter = ['payment_type', 'status', 'month']
    search_fields = ['student__first_name', 'student__last_name', 'instructor__first_name', 'instructor__last_name']
    date_hierarchy = 'month'
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'member_type', 'capital_shares', 'join_date', 'is_active']
    list_filter = ['member_type', 'is_active', 'join_date']
    search_fields = ['first_name', 'last_name', 'email']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(InstructorHours)
class InstructorHoursAdmin(admin.ModelAdmin):
    list_display = ['instructor', 'course', 'month', 'hours_worked']
    list_filter = ['month', 'instructor', 'course']
    search_fields = ['instructor__first_name', 'instructor__last_name', 'course__name']
    date_hierarchy = 'month'
    readonly_fields = ['created_at', 'updated_at']


@admin.register(FinancialReport)
class FinancialReportAdmin(admin.ModelAdmin):
    list_display = ['month', 'total_revenue', 'total_instructor_payments', 'net_profit', 'is_finalized']
    list_filter = ['is_finalized', 'month']
    date_hierarchy = 'month'
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ProfitDistribution)
class ProfitDistributionAdmin(admin.ModelAdmin):
    list_display = ['member', 'financial_report', 'share_percentage', 'amount', 'is_paid']
    list_filter = ['is_paid', 'financial_report']
    search_fields = ['member__first_name', 'member__last_name']
    readonly_fields = ['created_at', 'updated_at']


# ==============================================================================
# EXPENSE MANAGEMENT
# ==============================================================================

@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at']


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['expense_type', 'description_preview', 'amount', 'expense_date', 'status', 'submitted_by', 'approved_by']
    list_filter = ['expense_type', 'status', 'expense_date', 'month']
    search_fields = ['description', 'notes']
    date_hierarchy = 'expense_date'
    readonly_fields = ['submitted_by', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Expense Details', {
            'fields': ('expense_type', 'category', 'description', 'amount', 'expense_date', 'month')
        }),
        ('Approval', {
            'fields': ('status', 'submitted_by', 'approved_by', 'approval_date')
        }),
        ('Payment', {
            'fields': ('paid_date', 'payment_method', 'receipt_number', 'receipt_file')
        }),
        ('Additional Info', {
            'fields': ('notes', 'created_at', 'updated_at')
        }),
    )
    
    def description_preview(self, obj):
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    description_preview.short_description = 'Description'


@admin.register(RecurringExpense)
class RecurringExpenseAdmin(admin.ModelAdmin):
    list_display = ['name', 'expense_type', 'amount', 'frequency', 'is_active', 'auto_generate', 'last_generated']
    list_filter = ['expense_type', 'frequency', 'is_active', 'auto_generate']
    search_fields = ['name', 'description']
    readonly_fields = ['last_generated', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Recurring Expense Details', {
            'fields': ('name', 'expense_type', 'category', 'amount', 'frequency')
        }),
        ('Schedule', {
            'fields': ('start_date', 'end_date', 'is_active', 'auto_generate', 'last_generated')
        }),
        ('Description', {
            'fields': ('description',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# ==============================================================================
# AUDIT & LOGGING
# ==============================================================================

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'model_name', 'timestamp', 'ip_address']
    list_filter = ['action', 'model_name', 'timestamp']
    search_fields = ['user__username', 'user__email', 'description', 'model_name']
    date_hierarchy = 'timestamp'
    readonly_fields = ['user', 'action', 'model_name', 'object_id', 'description', 'ip_address', 'timestamp']
    
    def has_add_permission(self, request):
        # Audit logs should only be created programmatically
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Only superusers can delete audit logs
        return request.user.is_superuser


# ==============================================================================
# ADMIN SITE CUSTOMIZATION
# ==============================================================================

admin.site.site_header = "Educational Cooperative Administration"
admin.site.site_title = "EduCoop Admin"
admin.site.index_title = "System Management Dashboard"
