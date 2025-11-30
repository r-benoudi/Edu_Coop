from django.contrib import admin
from .models import (
    Student, Instructor, Course, Enrollment, Attendance,
    Payment, Member, InstructorHours, FinancialReport, ProfitDistribution
)

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'phone', 'registration_date', 'is_active']
    list_filter = ['is_active', 'registration_date']
    search_fields = ['first_name', 'last_name', 'email']
    date_hierarchy = 'registration_date'


@admin.register(Instructor)
class InstructorAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'specialization', 'hourly_rate', 'is_active']
    list_filter = ['is_active', 'specialization']
    search_fields = ['first_name', 'last_name', 'email', 'specialization']


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['name', 'course_type', 'subject', 'monthly_fee', 'enrolled_count', 'enrollment_limit', 'is_active']
    list_filter = ['course_type', 'subject', 'is_active']
    search_fields = ['name', 'description']
    filter_horizontal = ['instructors']


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'enrollment_date', 'is_active']
    list_filter = ['is_active', 'enrollment_date', 'course']
    search_fields = ['student__first_name', 'student__last_name', 'course__name']
    date_hierarchy = 'enrollment_date'


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['enrollment', 'date', 'status']
    list_filter = ['status', 'date']
    date_hierarchy = 'date'


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['payment_type', 'student', 'instructor', 'amount', 'amount_paid', 'status', 'month']
    list_filter = ['payment_type', 'status', 'month']
    search_fields = ['student__first_name', 'student__last_name', 'instructor__first_name', 'instructor__last_name']
    date_hierarchy = 'month'


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'member_type', 'capital_shares', 'join_date', 'is_active']
    list_filter = ['member_type', 'is_active']
    search_fields = ['first_name', 'last_name', 'email']


@admin.register(InstructorHours)
class InstructorHoursAdmin(admin.ModelAdmin):
    list_display = ['instructor', 'course', 'month', 'hours_worked']
    list_filter = ['month', 'instructor', 'course']
    date_hierarchy = 'month'


@admin.register(FinancialReport)
class FinancialReportAdmin(admin.ModelAdmin):
    list_display = ['month', 'total_revenue', 'total_instructor_payments', 'net_profit', 'is_finalized']
    list_filter = ['is_finalized', 'month']
    date_hierarchy = 'month'


@admin.register(ProfitDistribution)
class ProfitDistributionAdmin(admin.ModelAdmin):
    list_display = ['member', 'financial_report', 'share_percentage', 'amount', 'is_paid']
    list_filter = ['is_paid', 'financial_report']
