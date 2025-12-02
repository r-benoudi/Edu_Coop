from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.http import HttpResponse
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal
from dateutil.relativedelta import relativedelta

from .models import (
    Student, Instructor, Course, Enrollment, Attendance,
    Payment, Member, InstructorHours, FinancialReport, ProfitDistribution
)
from .forms import (
    StudentForm, InstructorForm, CourseForm, EnrollmentForm,
    AttendanceForm, BulkAttendanceForm, PaymentRecordForm,
    MemberForm, InstructorHoursForm, GeneratePaymentsForm
)
from .pdf_generator import generate_invoice, generate_contract, generate_financial_report

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from datetime import date, timedelta, datetime
from decimal import Decimal
from dateutil.relativedelta import relativedelta
from collections import defaultdict

from .models import (
    Student, Instructor, Course, Enrollment, Attendance,
    Payment, Member, InstructorHours, FinancialReport, ProfitDistribution
)

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.http import JsonResponse
from datetime import date, timedelta
from decimal import Decimal
from functools import wraps

from .models import User, Expense, ExpenseCategory, RecurringExpense, AuditLog

from .decorators import (
    admin_required,
    manager_required,
    accountant_required,
    instructor_required,
    can_manage_students,
    can_manage_courses,
    can_manage_enrollments,
    can_record_attendance,
    can_view_payments,
    can_manage_payments,
    can_view_financials,
)


@login_required
@can_view_financials
def generate_financial_report(request):
    if request.method == 'POST':
        month_str = request.POST.get('month')
        if month_str:
            try:
                year, month_num = month_str.split('-')
                month = date(int(year), int(month_num), 1)
            except:
                month = date.today().replace(day=1)
        else:
            month = date.today().replace(day=1)
        
        # Calculate total revenue from paid student fees
        total_revenue = Payment.objects.filter(
            payment_type='student_fee',
            month=month,
            status='paid'
        ).aggregate(total=Sum('amount_paid'))['total'] or Decimal('0')
        
        # Calculate total instructor payments
        total_instructor = Payment.objects.filter(
            payment_type='instructor_payment',
            month=month,
            status='paid'
        ).aggregate(total=Sum('amount_paid'))['total'] or Decimal('0')
        
        # Calculate total operational expenses (NEW)
        total_expenses = Expense.objects.filter(
            month=month,
            status='paid'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        # Calculate profits
        gross_profit = total_revenue - total_instructor
        net_profit = gross_profit - total_expenses  # Now includes expenses
        
        # Create or update the financial report
        report, created = FinancialReport.objects.update_or_create(
            month=month,
            defaults={
                'total_revenue': total_revenue,
                'total_instructor_payments': total_instructor,
                'total_expenses': total_expenses,  # Now properly set
                'gross_profit': gross_profit,
                'net_profit': net_profit,
            }
        )
        
        # Log the action
        AuditLog.objects.create(
            user=request.user,
            action='create' if created else 'update',
            model_name='FinancialReport',
            object_id=report.pk,
            description=f'{"Generated" if created else "Updated"} financial report for {month.strftime("%B %Y")}',
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        action = 'generated' if created else 'updated'
        messages.success(request, f'Financial report for {month.strftime("%B %Y")} {action}. Total expenses: {total_expenses} DH included.')
        return redirect('core:financial_report_detail', pk=report.pk)
    
    return render(request, 'core/generate_financial_report.html')


@login_required
@can_view_financials
def financial_report_detail(request, pk):
    report = get_object_or_404(FinancialReport, pk=pk)
    distributions = report.distributions.select_related('member').all()
    
    # Get expense breakdown for this month
    expense_breakdown = Expense.objects.filter(
        month=report.month,
        status='paid'
    ).values('expense_type').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')
    
    # Get individual expenses for this month
    expenses = Expense.objects.filter(
        month=report.month,
        status='paid'
    ).select_related('submitted_by', 'approved_by').order_by('-expense_date')
    
    context = {
        'report': report,
        'distributions': distributions,
        'expense_breakdown': expense_breakdown,
        'expenses': expenses,
    }
    return render(request, 'core/financial_report_detail.html', context)


@login_required
@can_view_financials
def financial_overview(request):
    reports = FinancialReport.objects.all()[:12]
    
    today = date.today()
    first_of_month = today.replace(day=1)
    
    # Current month revenue
    current_revenue = Payment.objects.filter(
        payment_type='student_fee',
        month=first_of_month
    ).aggregate(
        total=Sum('amount'),
        paid=Sum('amount_paid')
    )
    
    # Current month instructor payments
    current_expenses = Payment.objects.filter(
        payment_type='instructor_payment',
        month=first_of_month
    ).aggregate(
        total=Sum('amount'),
        paid=Sum('amount_paid')
    )
    
    # Current month operational expenses (NEW)
    current_operational_expenses = Expense.objects.filter(
        month=first_of_month,
        status='paid'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    # Total expenses = instructor payments + operational expenses
    total_current_expenses = (current_expenses.get('paid') or Decimal('0')) + current_operational_expenses
    
    # Member capital
    total_capital = Member.objects.filter(is_active=True).aggregate(total=Sum('capital_shares'))['total'] or Decimal('0')
    
    context = {
        'reports': reports,
        'current_revenue': current_revenue,
        'current_expenses': current_expenses,
        'current_operational_expenses': current_operational_expenses,
        'total_current_expenses': total_current_expenses,
        'total_capital': total_capital,
        'current_month': first_of_month,
    }
    return render(request, 'core/financial_overview.html', context)


@login_required
def dashboard(request):
    today = date.today()
    first_of_month = today.replace(day=1)
    
    total_students = Student.objects.filter(is_active=True).count()
    total_instructors = Instructor.objects.filter(is_active=True).count()
    total_courses = Course.objects.filter(is_active=True).count()
    total_enrollments = Enrollment.objects.filter(is_active=True).count()
    
    # Revenue
    monthly_revenue = Payment.objects.filter(
        payment_type='student_fee',
        month=first_of_month,
        status='paid'
    ).aggregate(total=Sum('amount_paid'))['total'] or Decimal('0')
    
    expected_revenue = Payment.objects.filter(
        payment_type='student_fee',
        month=first_of_month
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    pending_payments = Payment.objects.filter(
        payment_type='student_fee',
        status__in=['pending', 'partial', 'overdue']
    ).count()
    
    # Instructor payments
    monthly_instructor_payments = Payment.objects.filter(
        payment_type='instructor_payment',
        month=first_of_month,
        status='paid'
    ).aggregate(total=Sum('amount_paid'))['total'] or Decimal('0')
    
    # Operational expenses (NEW)
    monthly_operational_expenses = Expense.objects.filter(
        month=first_of_month,
        status='paid'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    # Total expenses = instructor payments + operational expenses
    monthly_expenses = monthly_instructor_payments + monthly_operational_expenses
    
    # Profit calculation now includes operational expenses
    estimated_profit = monthly_revenue - monthly_expenses
    
    recent_enrollments = Enrollment.objects.select_related('student', 'course').order_by('-enrollment_date')[:5]
    recent_payments = Payment.objects.filter(payment_type='student_fee').select_related('student').order_by('-created_at')[:5]
    courses_by_subject = Course.objects.filter(is_active=True).values('subject').annotate(count=Count('id'))
    
    # Top courses
    top_courses = []
    for course in Course.objects.filter(is_active=True):
        top_courses.append({
            'name': course.name,
            'enrolled_count': course.enrolled_count,
            'enrollment_limit': course.enrollment_limit,
            'monthly_fee': course.monthly_fee,
            'course_type': course.get_course_type_display(),
            'pk': course.pk
        })
    top_courses.sort(key=lambda x: x['enrolled_count'], reverse=True)
    top_courses = top_courses[:5]
    
    context = {
        'total_students': total_students,
        'total_instructors': total_instructors,
        'total_courses': total_courses,
        'total_enrollments': total_enrollments,
        'monthly_revenue': monthly_revenue,
        'expected_revenue': expected_revenue,
        'pending_payments': pending_payments,
        'monthly_instructor_payments': monthly_instructor_payments,
        'monthly_operational_expenses': monthly_operational_expenses,
        'monthly_expenses': monthly_expenses,
        'estimated_profit': estimated_profit,
        'recent_enrollments': recent_enrollments,
        'recent_payments': recent_payments,
        'courses_by_subject': courses_by_subject,
        'top_courses': top_courses,
    }
    return render(request, 'core/dashboard.html', context)

# ==============================================================================
# ROLE-BASED ACCESS DECORATORS
# ==============================================================================

# def admin_required(view_func):
#     """Decorator to require admin role"""
#     @wraps(view_func)
#     def wrapper(request, *args, **kwargs):
#         if not request.user.is_authenticated:
#             return redirect('core:login')
#         if not request.user.is_admin:
#             messages.error(request, 'You do not have permission to access this page.')
#             return redirect('core:dashboard')
#         return view_func(request, *args, **kwargs)
#     return wrapper


# def manager_required(view_func):
#     """Decorator to require manager or admin role"""
#     @wraps(view_func)
#     def wrapper(request, *args, **kwargs):
#         if not request.user.is_authenticated:
#             return redirect('core:login')
#         if not request.user.is_manager:
#             messages.error(request, 'You do not have permission to access this page.')
#             return redirect('core:dashboard')
#         return view_func(request, *args, **kwargs)
#     return wrapper


# def accountant_required(view_func):
#     """Decorator to require accountant, manager, or admin role"""
#     @wraps(view_func)
#     def wrapper(request, *args, **kwargs):
#         if not request.user.is_authenticated:
#             return redirect('core:login')
#         if not request.user.can_view_financials:
#             messages.error(request, 'You do not have permission to access this page.')
#             return redirect('core:dashboard')
#         return view_func(request, *args, **kwargs)
#     return wrapper

# def dashboard(request):
#     today = date.today()
#     first_of_month = today.replace(day=1)
    
#     total_students = Student.objects.filter(is_active=True).count()
#     total_instructors = Instructor.objects.filter(is_active=True).count()
#     total_courses = Course.objects.filter(is_active=True).count()
#     total_enrollments = Enrollment.objects.filter(is_active=True).count()
    
#     monthly_revenue = Payment.objects.filter(
#         payment_type='student_fee',
#         month=first_of_month,
#         status='paid'
#     ).aggregate(total=Sum('amount_paid'))['total'] or Decimal('0')
    
#     pending_payments = Payment.objects.filter(
#         payment_type='student_fee',
#         status__in=['pending', 'partial', 'overdue']
#     ).count()
    
#     monthly_expenses = Payment.objects.filter(
#         payment_type='instructor_payment',
#         month=first_of_month,
#         status='paid'
#     ).aggregate(total=Sum('amount_paid'))['total'] or Decimal('0')
    
#     estimated_profit = monthly_revenue - monthly_expenses
    
#     recent_enrollments = Enrollment.objects.select_related('student', 'course').order_by('-enrollment_date')[:5]
#     recent_payments = Payment.objects.filter(payment_type='student_fee').select_related('student').order_by('-created_at')[:5]
    
#     courses_by_subject = Course.objects.filter(is_active=True).values('subject').annotate(count=Count('id'))
    
#     context = {
#         'total_students': total_students,
#         'total_instructors': total_instructors,
#         'total_courses': total_courses,
#         'total_enrollments': total_enrollments,
#         'monthly_revenue': monthly_revenue,
#         'pending_payments': pending_payments,
#         'monthly_expenses': monthly_expenses,
#         'estimated_profit': estimated_profit,
#         'recent_enrollments': recent_enrollments,
#         'recent_payments': recent_payments,
#         'courses_by_subject': courses_by_subject,
#     }
#     return render(request, 'core/dashboard.html', context)
# @login_required
# def dashboard(request):
#     today = date.today()
#     first_of_month = today.replace(day=1)
    
#     total_students = Student.objects.filter(is_active=True).count()
#     total_instructors = Instructor.objects.filter(is_active=True).count()
#     total_courses = Course.objects.filter(is_active=True).count()
#     total_enrollments = Enrollment.objects.filter(is_active=True).count()
    
#     monthly_revenue = Payment.objects.filter(
#         payment_type='student_fee',
#         month=first_of_month,
#         status='paid'
#     ).aggregate(total=Sum('amount_paid'))['total'] or Decimal('0')
    
#     expected_revenue = Payment.objects.filter(
#         payment_type='student_fee',
#         month=first_of_month
#     ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
#     pending_payments = Payment.objects.filter(
#         payment_type='student_fee',
#         status__in=['pending', 'partial', 'overdue']
#     ).count()
    
#     monthly_expenses = Payment.objects.filter(
#         payment_type='instructor_payment',
#         month=first_of_month,
#         status='paid'
#     ).aggregate(total=Sum('amount_paid'))['total'] or Decimal('0')
    
#     estimated_profit = monthly_revenue - monthly_expenses
    
#     recent_enrollments = Enrollment.objects.select_related('student', 'course').order_by('-enrollment_date')[:5]
#     recent_payments = Payment.objects.filter(payment_type='student_fee').select_related('student').order_by('-created_at')[:5]
#     courses_by_subject = Course.objects.filter(is_active=True).values('subject').annotate(count=Count('id'))
    
#     # FIX: Build top_courses list manually to use the property
#     top_courses = []
#     for course in Course.objects.filter(is_active=True):
#         top_courses.append({
#             'name': course.name,
#             'enrolled_count': course.enrolled_count,  # Use property
#             'enrollment_limit': course.enrollment_limit,
#             'monthly_fee': course.monthly_fee,
#             'course_type': course.get_course_type_display(),
#             'pk': course.pk
#         })
#     top_courses.sort(key=lambda x: x['enrolled_count'], reverse=True)
#     top_courses = top_courses[:5]
    
#     context = {
#         'total_students': total_students,
#         'total_instructors': total_instructors,
#         'total_courses': total_courses,
#         'total_enrollments': total_enrollments,
#         'monthly_revenue': monthly_revenue,
#         'expected_revenue': expected_revenue,
#         'pending_payments': pending_payments,
#         'monthly_expenses': monthly_expenses,
#         'estimated_profit': estimated_profit,
#         'recent_enrollments': recent_enrollments,
#         'recent_payments': recent_payments,
#         'courses_by_subject': courses_by_subject,
#         'top_courses': top_courses,
#     }
#     return render(request, 'core/dashboard.html', context)

@login_required
def student_list(request):
    students = Student.objects.all()
    search = request.GET.get('search', '')
    if search:
        students = students.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search)
        )
    return render(request, 'core/student_list.html', {'students': students, 'search': search})


@login_required
def student_detail(request, pk):
    student = get_object_or_404(Student, pk=pk)
    enrollments = student.enrollments.select_related('course').all()
    payments = student.payments.all()[:10]
    return render(request, 'core/student_detail.html', {
        'student': student,
        'enrollments': enrollments,
        'payments': payments
    })

@login_required
@can_manage_students
def student_create(request):
    if request.method == 'POST':
        form = StudentForm(request.POST)
        if form.is_valid():
            student = form.save()
            messages.success(request, f'Student {student.full_name} created successfully.')
            return redirect('core:student_list')
    else:
        form = StudentForm()
    return render(request, 'core/student_form.html', {'form': form, 'title': 'Add New Student'})


@login_required
@can_manage_students
def student_edit(request, pk):
    student = get_object_or_404(Student, pk=pk)
    if request.method == 'POST':
        form = StudentForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, f'Student {student.full_name} updated successfully.')
            return redirect('core:student_detail', pk=pk)
    else:
        form = StudentForm(instance=student)
    return render(request, 'core/student_form.html', {'form': form, 'title': 'Edit Student', 'student': student})


@login_required
@manager_required
def student_delete(request, pk):
    student = get_object_or_404(Student, pk=pk)
    if request.method == 'POST':
        name = student.full_name
        student.delete()
        messages.success(request, f'Student {name} deleted successfully.')
        return redirect('core:student_list')
    return render(request, 'core/confirm_delete.html', {'object': student, 'type': 'student'})


@login_required
def instructor_list(request):
    instructors = Instructor.objects.all()
    search = request.GET.get('search', '')
    if search:
        instructors = instructors.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(specialization__icontains=search)
        )
    return render(request, 'core/instructor_list.html', {'instructors': instructors, 'search': search})


@login_required
def instructor_detail(request, pk):
    instructor = get_object_or_404(Instructor, pk=pk)
    courses = instructor.courses.all()
    payments = instructor.payments.all()[:10]
    hours = instructor.hours.all()[:10]
    return render(request, 'core/instructor_detail.html', {
        'instructor': instructor,
        'courses': courses,
        'payments': payments,
        'hours': hours
    })

@login_required
@manager_required
def instructor_create(request):
    if request.method == 'POST':
        form = InstructorForm(request.POST)
        if form.is_valid():
            instructor = form.save()
            messages.success(request, f'Instructor {instructor.full_name} created successfully.')
            return redirect('core:instructor_list')
    else:
        form = InstructorForm()
    return render(request, 'core/instructor_form.html', {'form': form, 'title': 'Add New Instructor'})


@login_required
@manager_required
def instructor_edit(request, pk):
    instructor = get_object_or_404(Instructor, pk=pk)
    if request.method == 'POST':
        form = InstructorForm(request.POST, instance=instructor)
        if form.is_valid():
            form.save()
            messages.success(request, f'Instructor {instructor.full_name} updated successfully.')
            return redirect('core:instructor_detail', pk=pk)
    else:
        form = InstructorForm(instance=instructor)
    return render(request, 'core/instructor_form.html', {'form': form, 'title': 'Edit Instructor', 'instructor': instructor})


@login_required
@manager_required
def instructor_delete(request, pk):
    instructor = get_object_or_404(Instructor, pk=pk)
    if request.method == 'POST':
        name = instructor.full_name
        instructor.delete()
        messages.success(request, f'Instructor {name} deleted successfully.')
        return redirect('core:instructor_list')
    return render(request, 'core/confirm_delete.html', {'object': instructor, 'type': 'instructor'})


@login_required
def course_list(request):
    courses = Course.objects.all()
    course_type = request.GET.get('type', '')
    subject = request.GET.get('subject', '')
    if course_type:
        courses = courses.filter(course_type=course_type)
    if subject:
        courses = courses.filter(subject=subject)
    return render(request, 'core/course_list.html', {
        'courses': courses,
        'course_type': course_type,
        'subject': subject,
        'course_types': Course.COURSE_TYPE_CHOICES,
        'subjects': Course.SUBJECT_CHOICES
    })

@login_required
def course_detail(request, pk):
    course = get_object_or_404(Course, pk=pk)
    enrollments = course.enrollments.filter(is_active=True).select_related('student')
    instructors = course.instructors.all()
    return render(request, 'core/course_detail.html', {
        'course': course,
        'enrollments': enrollments,
        'instructors': instructors
    })


@login_required
@can_manage_courses
def course_create(request):
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save()
            messages.success(request, f'Course {course.name} created successfully.')
            return redirect('core:course_list')
    else:
        form = CourseForm()
    return render(request, 'core/course_form.html', {'form': form, 'title': 'Add New Course'})


@login_required
@can_manage_courses
def course_edit(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, f'Course {course.name} updated successfully.')
            return redirect('core:course_detail', pk=pk)
    else:
        form = CourseForm(instance=course)
    return render(request, 'core/course_form.html', {'form': form, 'title': 'Edit Course', 'course': course})


@login_required
@manager_required
def course_delete(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if request.method == 'POST':
        name = course.name
        course.delete()
        messages.success(request, f'Course {name} deleted successfully.')
        return redirect('core:course_list')
    return render(request, 'core/confirm_delete.html', {'object': course, 'type': 'course'})


@login_required
def enrollment_list(request):
    enrollments = Enrollment.objects.select_related('student', 'course').all()
    course_id = request.GET.get('course', '')
    if course_id:
        enrollments = enrollments.filter(course_id=course_id)
    courses = Course.objects.filter(is_active=True)
    return render(request, 'core/enrollment_list.html', {
        'enrollments': enrollments,
        'courses': courses,
        'selected_course': course_id
    })

@login_required
@can_manage_enrollments
def enrollment_create(request):
    if request.method == 'POST':
        form = EnrollmentForm(request.POST)
        if form.is_valid():
            enrollment = form.save()
            messages.success(request, f'{enrollment.student.full_name} enrolled in {enrollment.course.name}.')
            return redirect('core:enrollment_list')
    else:
        form = EnrollmentForm()
    return render(request, 'core/enrollment_form.html', {'form': form, 'title': 'New Enrollment'})


@login_required
@manager_required
def enrollment_delete(request, pk):
    enrollment = get_object_or_404(Enrollment, pk=pk)
    if request.method == 'POST':
        enrollment.delete()
        messages.success(request, 'Enrollment deleted successfully.')
        return redirect('core:enrollment_list')
    return render(request, 'core/confirm_delete.html', {'object': enrollment, 'type': 'enrollment'})


@login_required
def attendance_list(request):
    attendances = Attendance.objects.select_related('enrollment__student', 'enrollment__course').order_by('-date')[:100]
    return render(request, 'core/attendance_list.html', {'attendances': attendances})


@login_required
@can_record_attendance
def attendance_record(request):
    if request.method == 'POST':
        form = BulkAttendanceForm(request.POST)
        if form.is_valid():
            course = form.cleaned_data['course']
            att_date = form.cleaned_data['date']
            enrollments = Enrollment.objects.filter(course=course, is_active=True)
            
            for enrollment in enrollments:
                status = request.POST.get(f'status_{enrollment.id}', 'present')
                Attendance.objects.update_or_create(
                    enrollment=enrollment,
                    date=att_date,
                    defaults={'status': status}
                )
            messages.success(request, f'Attendance recorded for {course.name} on {att_date}.')
            return redirect('core:attendance_list')
    else:
        form = BulkAttendanceForm()
    
    course_id = request.GET.get('course')
    enrollments = []
    if course_id:
        enrollments = Enrollment.objects.filter(course_id=course_id, is_active=True).select_related('student')
    
    return render(request, 'core/attendance_record.html', {
        'form': form,
        'enrollments': enrollments,
        'selected_course': course_id
    })

@login_required
def attendance_report(request):
    course_id = request.GET.get('course')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    attendances = Attendance.objects.select_related('enrollment__student', 'enrollment__course')
    
    if course_id:
        attendances = attendances.filter(enrollment__course_id=course_id)
    if start_date:
        attendances = attendances.filter(date__gte=start_date)
    if end_date:
        attendances = attendances.filter(date__lte=end_date)
    
    courses = Course.objects.filter(is_active=True)
    
    stats = attendances.values('status').annotate(count=Count('id'))
    
    return render(request, 'core/attendance_report.html', {
        'attendances': attendances[:200],
        'courses': courses,
        'stats': stats,
        'selected_course': course_id,
        'start_date': start_date,
        'end_date': end_date
    })

@login_required
@can_view_payments
def payment_list(request):
    payments = Payment.objects.select_related('student', 'instructor').order_by('-month', '-created_at')[:100]
    return render(request, 'core/payment_list.html', {'payments': payments})


@login_required
@can_view_payments
def student_payment_list(request):
    payments = Payment.objects.filter(payment_type='student_fee').select_related('student').order_by('-month')
    status = request.GET.get('status')
    if status:
        payments = payments.filter(status=status)
    return render(request, 'core/student_payment_list.html', {'payments': payments, 'selected_status': status})


@login_required
def instructor_payment_list(request):
    payments = Payment.objects.filter(payment_type='instructor_payment').select_related('instructor').order_by('-month')
    return render(request, 'core/instructor_payment_list.html', {'payments': payments})


@login_required
@can_view_financials
def generate_monthly_payments(request):
    if request.method == 'POST':
        form = GeneratePaymentsForm(request.POST)
        if form.is_valid():
            month = form.cleaned_data['month'].replace(day=1)
            
            created_student_payments = 0
            for enrollment in Enrollment.objects.filter(is_active=True).select_related('student', 'course'):
                payment, created = Payment.objects.get_or_create(
                    student=enrollment.student,
                    payment_type='student_fee',
                    month=month,
                    defaults={
                        'amount': enrollment.course.monthly_fee,
                        'status': 'pending'
                    }
                )
                if created:
                    created_student_payments += 1
            
            created_instructor_payments = 0
            instructor_totals = {}
            
            for course in Course.objects.filter(is_active=True).prefetch_related('instructors', 'enrollments'):
                for instructor in course.instructors.all():
                    if instructor.pk not in instructor_totals:
                        instructor_totals[instructor.pk] = {'instructor': instructor, 'amount': Decimal('0')}
                    
                    if course.course_type == 'tutoring':
                        student_count = course.enrollments.filter(is_active=True).count()
                        amount = Decimal('100') * student_count
                    else:
                        hours_record = InstructorHours.objects.filter(
                            instructor=instructor,
                            course=course,
                            month=month
                        ).first()
                        
                        if hours_record:
                            hours = min(hours_record.hours_worked, 8)
                        else:
                            hours = min(course.duration_hours, 8)
                            InstructorHours.objects.create(
                                instructor=instructor,
                                course=course,
                                month=month,
                                hours_worked=hours
                            )
                        
                        amount = Decimal('120') * hours
                    
                    instructor_totals[instructor.pk]['amount'] += amount
            
            for data in instructor_totals.values():
                if data['amount'] > 0:
                    payment, created = Payment.objects.get_or_create(
                        instructor=data['instructor'],
                        payment_type='instructor_payment',
                        month=month,
                        defaults={
                            'amount': data['amount'],
                            'status': 'pending'
                        }
                    )
                    if created:
                        created_instructor_payments += 1
            
            messages.success(request, f'Generated {created_student_payments} student payments and {created_instructor_payments} instructor payments for {month.strftime("%B %Y")}.')
            return redirect('core:payment_list')
    else:
        form = GeneratePaymentsForm(initial={'month': date.today().replace(day=1)})
    
    return render(request, 'core/generate_payments.html', {'form': form})


@login_required
@can_manage_payments
def record_payment(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    if request.method == 'POST':
        form = PaymentRecordForm(request.POST)
        if form.is_valid():
            payment.amount_paid += form.cleaned_data['amount_paid']
            payment.payment_date = form.cleaned_data['payment_date']
            if form.cleaned_data['notes']:
                payment.notes = form.cleaned_data['notes']
            
            if payment.amount_paid >= payment.amount:
                payment.status = 'paid'
            elif payment.amount_paid > 0:
                payment.status = 'partial'
            
            payment.save()
            messages.success(request, f'Payment of {form.cleaned_data["amount_paid"]} DH recorded.')
            return redirect('core:payment_list')
    else:
        form = PaymentRecordForm(initial={'payment_date': date.today()})
    
    return render(request, 'core/record_payment.html', {'form': form, 'payment': payment})


@login_required
@admin_required
def member_list(request):
    members = Member.objects.all()
    member_type = request.GET.get('type')
    if member_type:
        members = members.filter(member_type=member_type)
    return render(request, 'core/member_list.html', {'members': members, 'selected_type': member_type})


@login_required
@admin_required
def member_detail(request, pk):
    member = get_object_or_404(Member, pk=pk)
    distributions = member.profit_distributions.select_related('financial_report').all()[:10]
    return render(request, 'core/member_detail.html', {'member': member, 'distributions': distributions})

@login_required
@admin_required
def member_create(request):
    if request.method == 'POST':
        form = MemberForm(request.POST)
        if form.is_valid():
            member = form.save()
            messages.success(request, f'Member {member.full_name} created successfully.')
            return redirect('core:member_list')
    else:
        form = MemberForm()
    return render(request, 'core/member_form.html', {'form': form, 'title': 'Add New Member'})


@login_required
@admin_required
def member_edit(request, pk):
    member = get_object_or_404(Member, pk=pk)
    if request.method == 'POST':
        form = MemberForm(request.POST, instance=member)
        if form.is_valid():
            form.save()
            messages.success(request, f'Member {member.full_name} updated successfully.')
            return redirect('core:member_detail', pk=pk)
    else:
        form = MemberForm(instance=member)
    return render(request, 'core/member_form.html', {'form': form, 'title': 'Edit Member', 'member': member})


@login_required
@admin_required
def member_delete(request, pk):
    member = get_object_or_404(Member, pk=pk)
    if request.method == 'POST':
        name = member.full_name
        member.delete()
        messages.success(request, f'Member {name} deleted successfully.')
        return redirect('core:member_list')
    return render(request, 'core/confirm_delete.html', {'object': member, 'type': 'member'})



# @login_required
# @can_view_financials
# def financial_report_detail(request, pk):
#     report = get_object_or_404(FinancialReport, pk=pk)
#     distributions = report.distributions.select_related('member').all()
#     return render(request, 'core/financial_report_detail.html', {'report': report, 'distributions': distributions})


# @login_required
# @can_view_financials
# def generate_financial_report(request):
#     if request.method == 'POST':
#         month_str = request.POST.get('month')
#         if month_str:
#             try:
#                 year, month_num = month_str.split('-')
#                 month = date(int(year), int(month_num), 1)
#             except:
#                 month = date.today().replace(day=1)
#         else:
#             month = date.today().replace(day=1)
        
#         total_revenue = Payment.objects.filter(
#             payment_type='student_fee',
#             month=month,
#             status='paid'
#         ).aggregate(total=Sum('amount_paid'))['total'] or Decimal('0')
        
#         total_instructor = Payment.objects.filter(
#             payment_type='instructor_payment',
#             month=month,
#             status='paid'
#         ).aggregate(total=Sum('amount_paid'))['total'] or Decimal('0')
        
#         gross_profit = total_revenue - total_instructor
#         net_profit = gross_profit
        
#         report, created = FinancialReport.objects.update_or_create(
#             month=month,
#             defaults={
#                 'total_revenue': total_revenue,
#                 'total_instructor_payments': total_instructor,
#                 'gross_profit': gross_profit,
#                 'net_profit': net_profit,
#             }
#         )
        
#         action = 'generated' if created else 'updated'
#         messages.success(request, f'Financial report for {month.strftime("%B %Y")} {action}.')
#         return redirect('core:financial_report_detail', pk=report.pk)
    
#     return render(request, 'core/generate_financial_report.html')


@login_required
@admin_required
def distribute_profits(request, pk):
    report = get_object_or_404(FinancialReport, pk=pk)
    
    if request.method == 'POST':
        members = Member.objects.filter(is_active=True)
        total_shares = members.aggregate(total=Sum('capital_shares'))['total'] or Decimal('1')
        
        for member in members:
            if total_shares > 0:
                share_pct = (member.capital_shares / total_shares) * 100
                amount = (member.capital_shares / total_shares) * report.net_profit
            else:
                share_pct = Decimal('0')
                amount = Decimal('0')
            
            ProfitDistribution.objects.update_or_create(
                financial_report=report,
                member=member,
                defaults={
                    'share_percentage': share_pct,
                    'amount': amount,
                }
            )
        
        report.is_finalized = True
        report.save()
        
        messages.success(request, f'Profits distributed to {members.count()} members.')
        return redirect('core:financial_report_detail', pk=pk)
    
    return render(request, 'core/distribute_profits.html', {'report': report})


@login_required
@manager_required
def generate_invoice_pdf(request, payment_pk):
    payment = get_object_or_404(Payment, pk=payment_pk)
    response = generate_invoice(payment)
    return response


@login_required
@manager_required
def generate_contract_pdf(request, instructor_pk):
    instructor = get_object_or_404(Instructor, pk=instructor_pk)
    course_id = request.GET.get('course')
    course = None
    if course_id:
        course = get_object_or_404(Course, pk=course_id)
    response = generate_contract(instructor, course)
    return response


@login_required
@can_view_financials
def generate_report_pdf(request, report_pk):
    report = get_object_or_404(FinancialReport, pk=report_pk)
    response = generate_financial_report(report)
    return response

# Enhanced views.py with Intelligence & Automation Features
# Add these new views to your existing core/views.py file


# INTELLIGENCE & AUTOMATION FEATURES
@login_required
@manager_required
def system_intelligence_dashboard(request):
    """
    Dashboard showing automated suggestions and conflict detection
    """
    # Detect instructor availability conflicts
    conflicts = detect_instructor_conflicts()
    
    # Suggest optimal schedules
    suggestions = generate_schedule_suggestions()
    
    # Calculate financial projections
    projections = calculate_financial_projections()
    
    # Course optimization recommendations
    course_recommendations = analyze_course_performance()
    
    context = {
        'conflicts': conflicts,
        'suggestions': suggestions,
        'projections': projections,
        'course_recommendations': course_recommendations,
    }
    return render(request, 'core/intelligence_dashboard.html', context)


def detect_instructor_conflicts():
    """
    Detect conflicts in instructor availability and course overlaps
    """
    conflicts = []
    
    # Check if instructors are assigned to too many courses
    for instructor in Instructor.objects.filter(is_active=True):
        course_count = instructor.courses.filter(is_active=True).count()
        if course_count > 5:  # Threshold for too many courses
            conflicts.append({
                'type': 'workload',
                'severity': 'high',
                'instructor': instructor,
                'message': f'{instructor.full_name} is assigned to {course_count} courses (recommended max: 5)',
                'recommendation': 'Consider redistributing some courses to other instructors'
            })
    
    # Check for courses without instructors
    courses_without_instructors = Course.objects.filter(
        is_active=True,
        instructors__isnull=True
    )
    for course in courses_without_instructors:
        conflicts.append({
            'type': 'staffing',
            'severity': 'critical',
            'course': course,
            'message': f'{course.name} has no assigned instructor',
            'recommendation': 'Assign an instructor immediately'
        })
    
    # Check for overfilled courses
    overfilled_courses = Course.objects.filter(is_active=True)
    for course in overfilled_courses:
        if course.enrolled_count >= course.enrollment_limit:
            conflicts.append({
                'type': 'capacity',
                'severity': 'medium',
                'course': course,
                'message': f'{course.name} is at full capacity ({course.enrolled_count}/{course.enrollment_limit})',
                'recommendation': 'Consider opening a new section or increasing capacity'
            })
    
    return conflicts


# def generate_schedule_suggestions():
#     """
#     Generate optimal course schedule suggestions
#     """
#     suggestions = []
    
#     # Analyze enrollment patterns
#     popular_subjects = Course.objects.filter(is_active=True).annotate(
#         enrollment_count=Count('enrollments', filter=Q(enrollments__is_active=True))
#     ).order_by('-enrollment_count')[:3]
    
#     for course in popular_subjects:
#         if course.enrollment_count >= course.enrollment_limit * 0.8:
#             suggestions.append({
#                 'type': 'expansion',
#                 'priority': 'high',
#                 'course': course,
#                 'message': f'{course.name} is {int(course.enrollment_count/course.enrollment_limit*100)}% full',
#                 'recommendation': f'Consider opening another section. Potential revenue: {course.monthly_fee * course.enrollment_limit} DH/month'
#             })
    
#     # Suggest underperforming course actions
#     underperforming = Course.objects.filter(is_active=True).annotate(
#         enrollment_count=Count('enrollments', filter=Q(enrollments__is_active=True))
#     ).filter(enrollment_count__lt=5)
    
#     for course in underperforming:
#         suggestions.append({
#             'type': 'optimization',
#             'priority': 'medium',
#             'course': course,
#             'message': f'{course.name} has only {course.enrollment_count} students',
#             'recommendation': 'Consider marketing efforts or merging with similar courses'
#         })
    
#     return suggestions


def generate_schedule_suggestions():
    suggestions = []
    
    # FIX: Use property instead of annotation
    popular_courses = Course.objects.filter(is_active=True)
    course_list = []
    for course in popular_courses:
        course_list.append({
            'course': course,
            'count': course.enrolled_count
        })
    course_list.sort(key=lambda x: x['count'], reverse=True)
    popular_subjects = course_list[:3]
    
    for item in popular_subjects:
        course = item['course']
        count = item['count']
        if count >= course.enrollment_limit * 0.8:
            suggestions.append({
                'type': 'expansion',
                'priority': 'high',
                'course': course,
                'message': f'{course.name} is {int(count/course.enrollment_limit*100)}% full',
                'recommendation': f'Consider opening another section. Potential revenue: {course.monthly_fee * course.enrollment_limit} DH/month'
            })
    
    # Underperforming courses
    for course in Course.objects.filter(is_active=True):
        if course.enrolled_count < 5:
            suggestions.append({
                'type': 'optimization',
                'priority': 'medium',
                'course': course,
                'message': f'{course.name} has only {course.enrolled_count} students',
                'recommendation': 'Consider marketing efforts or merging with similar courses'
            })
    
    return suggestions

def calculate_financial_projections():
    """
    Calculate financial projections for different scenarios
    """
    scenarios = []
    
    # Current state
    current_students = Student.objects.filter(is_active=True).count()
    current_revenue = Enrollment.objects.filter(is_active=True).aggregate(
        total=Sum('course__monthly_fee')
    )['total'] or Decimal('0')
    
    # Scenario 1: 50 students
    scenario_50 = {
        'name': '50 Students Scenario',
        'students': 50,
        'estimated_revenue': calculate_scenario_revenue(50),
        'estimated_costs': calculate_scenario_costs(50),
        'estimated_profit': None
    }
    scenario_50['estimated_profit'] = scenario_50['estimated_revenue'] - scenario_50['estimated_costs']
    scenarios.append(scenario_50)
    
    # Scenario 2: 100 students
    scenario_100 = {
        'name': '100 Students Scenario',
        'students': 100,
        'estimated_revenue': calculate_scenario_revenue(100),
        'estimated_costs': calculate_scenario_costs(100),
        'estimated_profit': None
    }
    scenario_100['estimated_profit'] = scenario_100['estimated_revenue'] - scenario_100['estimated_costs']
    scenarios.append(scenario_100)
    
    # Scenario 3: Multiple courses expansion
    avg_fee = Decimal('350')  # Average between tutoring (250) and IT (500)
    scenario_multi = {
        'name': 'Multi-Course Expansion',
        'students': current_students,
        'estimated_revenue': current_revenue * Decimal('1.5'),  # 50% increase
        'estimated_costs': calculate_scenario_costs(int(current_students * 1.3)),
        'estimated_profit': None
    }
    scenario_multi['estimated_profit'] = scenario_multi['estimated_revenue'] - scenario_multi['estimated_costs']
    scenarios.append(scenario_multi)
    
    return {
        'current_students': current_students,
        'current_monthly_revenue': current_revenue,
        'scenarios': scenarios
    }


def calculate_scenario_revenue(student_count):
    """Calculate estimated revenue for a given number of students"""
    # Assuming 70% tutoring (250 DH) and 30% IT (500 DH) mix
    tutoring_students = int(student_count * 0.7)
    it_students = int(student_count * 0.3)
    return Decimal(tutoring_students * 250 + it_students * 500)



def calculate_scenario_costs(student_count):
    """Calculate estimated instructor costs for a given number of students"""
    # Tutoring: 100 DH per student
    # IT: Assume 120 DH * 8 hours = 960 DH per instructor per course
    # Assume 15 students per tutoring course, 20 students per IT course
    
    tutoring_students = int(student_count * 0.7)
    it_students = int(student_count * 0.3)
    
    tutoring_cost = Decimal(tutoring_students * 100)
    it_courses = max(1, it_students // 20)
    it_cost = Decimal(it_courses * 960)
    
    return tutoring_cost + it_cost


# def analyze_course_performance():
#     """Analyze course performance and provide recommendations"""
#     recommendations = []
    
#     courses = Course.objects.filter(is_active=True).annotate(
#         enrollment_count=Count('enrollments', filter=Q(enrollments__is_active=True))
#     )
    
#     for course in courses:
#         # Calculate revenue per course
#         revenue = course.monthly_fee * course.enrollment_count
        
#         # Calculate cost
#         if course.course_type == 'tutoring':
#             cost = Decimal('100') * course.enrollment_count
#         else:
#             # IT courses
#             cost = Decimal('120') * min(8, course.duration_hours)
        
#         profit = revenue - cost
#         margin = (profit / revenue * 100) if revenue > 0 else 0
        
#         # Generate recommendation based on performance
#         if margin > 60:
#             status = 'excellent'
#             action = 'Maintain current strategy'
#         elif margin > 40:
#             status = 'good'
#             action = 'Consider slight expansion'
#         elif margin > 20:
#             status = 'fair'
#             action = 'Review pricing or reduce costs'
#         else:
#             status = 'poor'
#             action = 'Urgent review needed - consider restructuring'
        
#         recommendations.append({
#             'course': course,
#             'revenue': revenue,
#             'cost': cost,
#             'profit': profit,
#             'margin': margin,
#             'status': status,
#             'action': action,
#             'enrollment_rate': int(course.enrollment_count / course.enrollment_limit * 100) if course.enrollment_limit > 0 else 0
#         })
    
#     return sorted(recommendations, key=lambda x: x['margin'], reverse=True)

def analyze_course_performance():
    recommendations = []
    
    # FIX: Use different annotation name
    courses = Course.objects.filter(is_active=True)
    
    for course in courses:
        enrollment_count = course.enrolled_count  # Use the property
        revenue = course.monthly_fee * enrollment_count
        
        if course.course_type == 'tutoring':
            cost = Decimal('100') * enrollment_count
        else:
            cost = Decimal('120') * min(8, course.duration_hours)
        
        profit = revenue - cost
        margin = (profit / revenue * 100) if revenue > 0 else 0
        
        if margin > 60:
            status = 'excellent'
            action = 'Maintain current strategy'
        elif margin > 40:
            status = 'good'
            action = 'Consider slight expansion'
        elif margin > 20:
            status = 'fair'
            action = 'Review pricing or reduce costs'
        else:
            status = 'poor'
            action = 'Urgent review needed'
        
        recommendations.append({
            'course': course,
            'revenue': revenue,
            'cost': cost,
            'profit': profit,
            'margin': margin,
            'status': status,
            'action': action,
            'enrollment_rate': int(enrollment_count / course.enrollment_limit * 100) if course.enrollment_limit > 0 else 0
        })
    
    return sorted(recommendations, key=lambda x: x['margin'], reverse=True)

# COMPLIANCE & LEGAL VIEWS

@login_required
def compliance_dashboard(request):
    """
    Dashboard showing legal compliance status and member management
    """
    # Active vs Passive members breakdown
    active_members = Member.objects.filter(is_active=True, member_type='active')
    passive_members = Member.objects.filter(is_active=True, member_type='passive')
    
    # Capital shares breakdown
    total_capital = Member.objects.filter(is_active=True).aggregate(
        total=Sum('capital_shares')
    )['total'] or Decimal('0')
    
    # Recent profit distributions
    recent_distributions = ProfitDistribution.objects.select_related(
        'member', 'financial_report'
    ).order_by('-created_at')[:10]
    
    # Compliance checklist
    compliance_items = [
        {
            'item': 'All members registered',
            'status': Member.objects.filter(is_active=True).count() > 0,
            'details': f'{Member.objects.filter(is_active=True).count()} active members'
        },
        {
            'item': 'Capital shares properly distributed',
            'status': total_capital > 0,
            'details': f'Total capital: {total_capital} DH'
        },
        {
            'item': 'Passive members (public employees) segregated',
            'status': passive_members.exists(),
            'details': f'{passive_members.count()} passive contributors'
        },
        {
            'item': 'Transparent financial records',
            'status': FinancialReport.objects.exists(),
            'details': f'{FinancialReport.objects.count()} financial reports'
        },
        {
            'item': 'Regular profit distribution',
            'status': ProfitDistribution.objects.exists(),
            'details': f'{ProfitDistribution.objects.count()} distributions made'
        }
    ]
    
    context = {
        'active_members': active_members,
        'passive_members': passive_members,
        'total_capital': total_capital,
        'recent_distributions': recent_distributions,
        'compliance_items': compliance_items,
    }
    return render(request, 'core/compliance_dashboard.html', context)


# ENHANCED REPORTING

@login_required
def comprehensive_report(request):
    """
    Generate comprehensive report with all KPIs and metrics
    """
    today = date.today()
    first_of_month = today.replace(day=1)
    
    # Student metrics
    total_students = Student.objects.filter(is_active=True).count()
    new_students_this_month = Student.objects.filter(
        registration_date__gte=first_of_month
    ).count()
    
    # Revenue metrics
    current_month_revenue = Payment.objects.filter(
        payment_type='student_fee',
        month=first_of_month,
        status='paid'
    ).aggregate(total=Sum('amount_paid'))['total'] or Decimal('0')
    
    expected_revenue = Payment.objects.filter(
        payment_type='student_fee',
        month=first_of_month
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    # Expense metrics
    instructor_payments = Payment.objects.filter(
        payment_type='instructor_payment',
        month=first_of_month,
        status='paid'
    ).aggregate(total=Sum('amount_paid'))['total'] or Decimal('0')
    
    # Enrollment metrics
    enrollment_by_subject = Course.objects.filter(is_active=True).values(
        'subject'
    ).annotate(
        students=Count('enrollments', filter=Q(enrollments__is_active=True))
    )
    
    enrollment_by_type = Course.objects.filter(is_active=True).values(
        'course_type'
    ).annotate(
        students=Count('enrollments', filter=Q(enrollments__is_active=True))
    )
    
    # Attendance metrics
    this_month_attendance = Attendance.objects.filter(
        date__gte=first_of_month
    ).values('status').annotate(count=Count('id'))
    
    attendance_rate = 0
    if this_month_attendance:
        total = sum(item['count'] for item in this_month_attendance)
        present = next((item['count'] for item in this_month_attendance if item['status'] == 'present'), 0)
        attendance_rate = (present / total * 100) if total > 0 else 0
    
    # Financial health indicators
    profit_margin = ((current_month_revenue - instructor_payments) / current_month_revenue * 100) if current_month_revenue > 0 else 0
    collection_rate = (current_month_revenue / expected_revenue * 100) if expected_revenue > 0 else 0
    
    context = {
        'report_date': today,
        'total_students': total_students,
        'new_students_this_month': new_students_this_month,
        'current_month_revenue': current_month_revenue,
        'expected_revenue': expected_revenue,
        'instructor_payments': instructor_payments,
        'net_profit': current_month_revenue - instructor_payments,
        'enrollment_by_subject': enrollment_by_subject,
        'enrollment_by_type': enrollment_by_type,
        'attendance_rate': attendance_rate,
        'profit_margin': profit_margin,
        'collection_rate': collection_rate,
        'active_courses': Course.objects.filter(is_active=True).count(),
        'active_instructors': Instructor.objects.filter(is_active=True).count(),
    }
    return render(request, 'core/comprehensive_report.html', context)


# API ENDPOINTS FOR STRUCTURED OUTPUT

@login_required
def api_financial_summary(request):
    """
    JSON API endpoint for financial summary
    """
    today = date.today()
    first_of_month = today.replace(day=1)
    
    revenue = Payment.objects.filter(
        payment_type='student_fee',
        month=first_of_month,
        status='paid'
    ).aggregate(total=Sum('amount_paid'))['total'] or Decimal('0')
    
    expenses = Payment.objects.filter(
        payment_type='instructor_payment',
        month=first_of_month,
        status='paid'
    ).aggregate(total=Sum('amount_paid'))['total'] or Decimal('0')
    
    data = {
        'month': first_of_month.strftime('%Y-%m'),
        'revenue': float(revenue),
        'expenses': float(expenses),
        'profit': float(revenue - expenses),
        'margin': float((revenue - expenses) / revenue * 100) if revenue > 0 else 0
    }
    
    return JsonResponse(data)


@login_required
def api_enrollment_stats(request):
    """
    JSON API endpoint for enrollment statistics
    """
    stats = {
        'total_students': Student.objects.filter(is_active=True).count(),
        'total_courses': Course.objects.filter(is_active=True).count(),
        'total_enrollments': Enrollment.objects.filter(is_active=True).count(),
        'by_course_type': {},
        'by_subject': {}
    }
    
    # Group by course type
    for course_type, label in Course.COURSE_TYPE_CHOICES:
        count = Enrollment.objects.filter(
            is_active=True,
            course__course_type=course_type
        ).count()
        stats['by_course_type'][label] = count
    
    # Group by subject
    for subject, label in Course.SUBJECT_CHOICES:
        count = Enrollment.objects.filter(
            is_active=True,
            course__subject=subject
        ).count()
        stats['by_subject'][label] = count
    
    return JsonResponse(stats)

# ==============================================================================
# AUTHENTICATION & EXPENSE VIEWS
# Add these to your core/views.py file
# ==============================================================================







# ==============================================================================
# AUTHENTICATION VIEWS
# ==============================================================================

def user_login(request):
    """User login view"""
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # Log the login
            AuditLog.objects.create(
                user=user,
                action='login',
                model_name='User',
                description=f'{user.get_full_name()} logged in',
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            messages.success(request, f'Welcome back, {user.get_full_name()}!')
            
            # Redirect based on role
            next_url = request.GET.get('next', 'core:dashboard')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'core/login.html')


@login_required
def user_logout(request):
    """User logout view"""
    # Log the logout
    AuditLog.objects.create(
        user=request.user,
        action='logout',
        model_name='User',
        description=f'{request.user.get_full_name()} logged out',
        ip_address=request.META.get('REMOTE_ADDR')
    )
    
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('core:login')


@login_required
def change_password(request):
    """Change password view"""
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        if not request.user.check_password(current_password):
            messages.error(request, 'Current password is incorrect.')
        elif new_password != confirm_password:
            messages.error(request, 'New passwords do not match.')
        elif len(new_password) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
        else:
            request.user.set_password(new_password)
            request.user.save()
            update_session_auth_hash(request, request.user)
            
            messages.success(request, 'Password changed successfully.')
            return redirect('core:dashboard')
    
    return render(request, 'core/change_password.html')


@admin_required
def user_management(request):
    """Manage system users"""
    users = User.objects.all().order_by('-date_joined')
    
    context = {
        'users': users,
        'total_users': users.count(),
        'active_users': users.filter(is_active=True).count(),
    }
    return render(request, 'core/user_management.html', context)


@admin_required
def create_user(request):
    """Create new user"""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        role = request.POST.get('role')
        password = request.POST.get('password')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
        elif User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists.')
        else:
            user = User.objects.create_user(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                password=password,
                role=role
            )
            
            AuditLog.objects.create(
                user=request.user,
                action='create',
                model_name='User',
                object_id=user.pk,
                description=f'Created user: {user.get_full_name()}',
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            messages.success(request, f'User {user.get_full_name()} created successfully.')
            return redirect('core:user_management')
    
    return render(request, 'core/create_user.html', {'role_choices': User.ROLE_CHOICES})


# ==============================================================================
# EXPENSE MANAGEMENT VIEWS
# ==============================================================================

@login_required
@accountant_required
def expense_list(request):
    """List all expenses with filtering"""
    expenses = Expense.objects.select_related('submitted_by', 'approved_by', 'category').all()
    
    # Filtering
    expense_type = request.GET.get('type')
    status = request.GET.get('status')
    month = request.GET.get('month')
    
    if expense_type:
        expenses = expenses.filter(expense_type=expense_type)
    if status:
        expenses = expenses.filter(status=status)
    if month:
        expenses = expenses.filter(month=month)
    
    # Statistics
    total_expenses = expenses.filter(status='paid').aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0')
    
    pending_count = expenses.filter(status='pending').count()
    
    context = {
        'expenses': expenses[:100],
        'total_expenses': total_expenses,
        'pending_count': pending_count,
        'expense_types': Expense.EXPENSE_TYPE_CHOICES,
        'status_choices': Expense.STATUS_CHOICES,
        'selected_type': expense_type,
        'selected_status': status,
    }
    return render(request, 'core/expense_list.html', context)


@login_required
@manager_required
def expense_create(request):
    """Create new expense"""
    if request.method == 'POST':
        expense_type = request.POST.get('expense_type')
        description = request.POST.get('description')
        amount = request.POST.get('amount')
        expense_date = request.POST.get('expense_date')
        month = request.POST.get('month')
        category_id = request.POST.get('category')
        receipt_file = request.FILES.get('receipt_file')
        notes = request.POST.get('notes', '')
        
        expense = Expense.objects.create(
            expense_type=expense_type,
            description=description,
            amount=amount,
            expense_date=expense_date,
            month=month,
            category_id=category_id if category_id else None,
            receipt_file=receipt_file,
            notes=notes,
            submitted_by=request.user,
            status='pending' if not request.user.is_admin else 'approved'
        )
        
        AuditLog.objects.create(
            user=request.user,
            action='create',
            model_name='Expense',
            object_id=expense.pk,
            description=f'Created expense: {expense.description} - {expense.amount} DH',
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        messages.success(request, 'Expense submitted successfully.')
        return redirect('core:expense_list')
    
    categories = ExpenseCategory.objects.filter(is_active=True)
    context = {
        'expense_types': Expense.EXPENSE_TYPE_CHOICES,
        'categories': categories,
    }
    return render(request, 'core/expense_form.html', context)


@login_required
@manager_required
def expense_approve(request, pk):
    """Approve an expense"""
    expense = get_object_or_404(Expense, pk=pk)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'approve':
            expense.status = 'approved'
            expense.approved_by = request.user
            expense.approval_date = date.today()
            expense.save()
            
            AuditLog.objects.create(
                user=request.user,
                action='approve',
                model_name='Expense',
                object_id=expense.pk,
                description=f'Approved expense: {expense.description} - {expense.amount} DH',
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            messages.success(request, 'Expense approved successfully.')
        elif action == 'reject':
            expense.status = 'rejected'
            expense.save()
            
            messages.info(request, 'Expense rejected.')
        
        return redirect('core:expense_list')
    
    return render(request, 'core/expense_approve.html', {'expense': expense})


@login_required
@accountant_required
def expense_mark_paid(request, pk):
    """Mark expense as paid"""
    expense = get_object_or_404(Expense, pk=pk)
    
    if request.method == 'POST':
        expense.status = 'paid'
        expense.paid_date = request.POST.get('paid_date', date.today())
        expense.payment_method = request.POST.get('payment_method', '')
        expense.receipt_number = request.POST.get('receipt_number', '')
        expense.save()
        
        AuditLog.objects.create(
            user=request.user,
            action='payment',
            model_name='Expense',
            object_id=expense.pk,
            description=f'Marked expense as paid: {expense.description} - {expense.amount} DH',
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        messages.success(request, 'Expense marked as paid.')
        return redirect('core:expense_list')
    
    return render(request, 'core/expense_mark_paid.html', {'expense': expense})


@login_required
@accountant_required
def expense_report(request):
    """Generate expense report"""
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    expenses = Expense.objects.filter(status='paid')
    
    if start_date:
        expenses = expenses.filter(expense_date__gte=start_date)
    if end_date:
        expenses = expenses.filter(expense_date__lte=end_date)
    
    # Summary by type
    by_type = expenses.values('expense_type').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')
    
    # Monthly summary
    by_month = expenses.values('month').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-month')[:12]
    
    total = expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    context = {
        'expenses': expenses[:100],
        'by_type': by_type,
        'by_month': by_month,
        'total': total,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'core/expense_report.html', context)


@login_required
@accountant_required
def recurring_expense_list(request):
    """List all recurring expenses"""
    recurring_expenses = RecurringExpense.objects.all()
    
    context = {
        'recurring_expenses': recurring_expenses,
    }
    return render(request, 'core/recurring_expense_list.html', context)


@login_required
@manager_required
def recurring_expense_create(request):
    """Create new recurring expense"""
    if request.method == 'POST':
        name = request.POST.get('name')
        expense_type = request.POST.get('expense_type')
        amount = request.POST.get('amount')
        frequency = request.POST.get('frequency')
        start_date = request.POST.get('start_date')
        description = request.POST.get('description', '')
        
        recurring_expense = RecurringExpense.objects.create(
            name=name,
            expense_type=expense_type,
            amount=amount,
            frequency=frequency,
            start_date=start_date,
            description=description
        )
        
        messages.success(request, 'Recurring expense created successfully.')
        return redirect('core:recurring_expense_list')
    
    context = {
        'expense_types': Expense.EXPENSE_TYPE_CHOICES,
        'frequency_choices': RecurringExpense.FREQUENCY_CHOICES,
    }
    return render(request, 'core/recurring_expense_form.html', context)


# ==============================================================================
# AUDIT LOG VIEW
# ==============================================================================

@login_required
@admin_required
def audit_log_view(request):
    """View audit logs"""
    logs = AuditLog.objects.select_related('user').all()[:200]
    
    context = {
        'logs': logs,
    }
    return render(request, 'core/audit_log.html', context)
