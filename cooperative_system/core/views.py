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


def dashboard(request):
    today = date.today()
    first_of_month = today.replace(day=1)
    
    total_students = Student.objects.filter(is_active=True).count()
    total_instructors = Instructor.objects.filter(is_active=True).count()
    total_courses = Course.objects.filter(is_active=True).count()
    total_enrollments = Enrollment.objects.filter(is_active=True).count()
    
    monthly_revenue = Payment.objects.filter(
        payment_type='student_fee',
        month=first_of_month,
        status='paid'
    ).aggregate(total=Sum('amount_paid'))['total'] or Decimal('0')
    
    pending_payments = Payment.objects.filter(
        payment_type='student_fee',
        status__in=['pending', 'partial', 'overdue']
    ).count()
    
    monthly_expenses = Payment.objects.filter(
        payment_type='instructor_payment',
        month=first_of_month,
        status='paid'
    ).aggregate(total=Sum('amount_paid'))['total'] or Decimal('0')
    
    estimated_profit = monthly_revenue - monthly_expenses
    
    recent_enrollments = Enrollment.objects.select_related('student', 'course').order_by('-enrollment_date')[:5]
    recent_payments = Payment.objects.filter(payment_type='student_fee').select_related('student').order_by('-created_at')[:5]
    
    courses_by_subject = Course.objects.filter(is_active=True).values('subject').annotate(count=Count('id'))
    
    context = {
        'total_students': total_students,
        'total_instructors': total_instructors,
        'total_courses': total_courses,
        'total_enrollments': total_enrollments,
        'monthly_revenue': monthly_revenue,
        'pending_payments': pending_payments,
        'monthly_expenses': monthly_expenses,
        'estimated_profit': estimated_profit,
        'recent_enrollments': recent_enrollments,
        'recent_payments': recent_payments,
        'courses_by_subject': courses_by_subject,
    }
    return render(request, 'core/dashboard.html', context)


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


def student_detail(request, pk):
    student = get_object_or_404(Student, pk=pk)
    enrollments = student.enrollments.select_related('course').all()
    payments = student.payments.all()[:10]
    return render(request, 'core/student_detail.html', {
        'student': student,
        'enrollments': enrollments,
        'payments': payments
    })


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


def student_delete(request, pk):
    student = get_object_or_404(Student, pk=pk)
    if request.method == 'POST':
        name = student.full_name
        student.delete()
        messages.success(request, f'Student {name} deleted successfully.')
        return redirect('core:student_list')
    return render(request, 'core/confirm_delete.html', {'object': student, 'type': 'student'})


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


def instructor_delete(request, pk):
    instructor = get_object_or_404(Instructor, pk=pk)
    if request.method == 'POST':
        name = instructor.full_name
        instructor.delete()
        messages.success(request, f'Instructor {name} deleted successfully.')
        return redirect('core:instructor_list')
    return render(request, 'core/confirm_delete.html', {'object': instructor, 'type': 'instructor'})


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


def course_detail(request, pk):
    course = get_object_or_404(Course, pk=pk)
    enrollments = course.enrollments.filter(is_active=True).select_related('student')
    instructors = course.instructors.all()
    return render(request, 'core/course_detail.html', {
        'course': course,
        'enrollments': enrollments,
        'instructors': instructors
    })


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


def course_delete(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if request.method == 'POST':
        name = course.name
        course.delete()
        messages.success(request, f'Course {name} deleted successfully.')
        return redirect('core:course_list')
    return render(request, 'core/confirm_delete.html', {'object': course, 'type': 'course'})


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


def enrollment_delete(request, pk):
    enrollment = get_object_or_404(Enrollment, pk=pk)
    if request.method == 'POST':
        enrollment.delete()
        messages.success(request, 'Enrollment deleted successfully.')
        return redirect('core:enrollment_list')
    return render(request, 'core/confirm_delete.html', {'object': enrollment, 'type': 'enrollment'})


def attendance_list(request):
    attendances = Attendance.objects.select_related('enrollment__student', 'enrollment__course').order_by('-date')[:100]
    return render(request, 'core/attendance_list.html', {'attendances': attendances})


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


def payment_list(request):
    payments = Payment.objects.select_related('student', 'instructor').order_by('-month', '-created_at')[:100]
    return render(request, 'core/payment_list.html', {'payments': payments})


def student_payment_list(request):
    payments = Payment.objects.filter(payment_type='student_fee').select_related('student').order_by('-month')
    status = request.GET.get('status')
    if status:
        payments = payments.filter(status=status)
    return render(request, 'core/student_payment_list.html', {'payments': payments, 'selected_status': status})


def instructor_payment_list(request):
    payments = Payment.objects.filter(payment_type='instructor_payment').select_related('instructor').order_by('-month')
    return render(request, 'core/instructor_payment_list.html', {'payments': payments})


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


def member_list(request):
    members = Member.objects.all()
    member_type = request.GET.get('type')
    if member_type:
        members = members.filter(member_type=member_type)
    return render(request, 'core/member_list.html', {'members': members, 'selected_type': member_type})


def member_detail(request, pk):
    member = get_object_or_404(Member, pk=pk)
    distributions = member.profit_distributions.select_related('financial_report').all()[:10]
    return render(request, 'core/member_detail.html', {'member': member, 'distributions': distributions})


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


def member_delete(request, pk):
    member = get_object_or_404(Member, pk=pk)
    if request.method == 'POST':
        name = member.full_name
        member.delete()
        messages.success(request, f'Member {name} deleted successfully.')
        return redirect('core:member_list')
    return render(request, 'core/confirm_delete.html', {'object': member, 'type': 'member'})


def financial_overview(request):
    reports = FinancialReport.objects.all()[:12]
    
    today = date.today()
    first_of_month = today.replace(day=1)
    
    current_revenue = Payment.objects.filter(
        payment_type='student_fee',
        month=first_of_month
    ).aggregate(
        total=Sum('amount'),
        paid=Sum('amount_paid')
    )
    
    current_expenses = Payment.objects.filter(
        payment_type='instructor_payment',
        month=first_of_month
    ).aggregate(
        total=Sum('amount'),
        paid=Sum('amount_paid')
    )
    
    total_capital = Member.objects.filter(is_active=True).aggregate(total=Sum('capital_shares'))['total'] or Decimal('0')
    
    context = {
        'reports': reports,
        'current_revenue': current_revenue,
        'current_expenses': current_expenses,
        'total_capital': total_capital,
        'current_month': first_of_month,
    }
    return render(request, 'core/financial_overview.html', context)


def financial_report_detail(request, pk):
    report = get_object_or_404(FinancialReport, pk=pk)
    distributions = report.distributions.select_related('member').all()
    return render(request, 'core/financial_report_detail.html', {'report': report, 'distributions': distributions})


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
        
        total_revenue = Payment.objects.filter(
            payment_type='student_fee',
            month=month,
            status='paid'
        ).aggregate(total=Sum('amount_paid'))['total'] or Decimal('0')
        
        total_instructor = Payment.objects.filter(
            payment_type='instructor_payment',
            month=month,
            status='paid'
        ).aggregate(total=Sum('amount_paid'))['total'] or Decimal('0')
        
        gross_profit = total_revenue - total_instructor
        net_profit = gross_profit
        
        report, created = FinancialReport.objects.update_or_create(
            month=month,
            defaults={
                'total_revenue': total_revenue,
                'total_instructor_payments': total_instructor,
                'gross_profit': gross_profit,
                'net_profit': net_profit,
            }
        )
        
        action = 'generated' if created else 'updated'
        messages.success(request, f'Financial report for {month.strftime("%B %Y")} {action}.')
        return redirect('core:financial_report_detail', pk=report.pk)
    
    return render(request, 'core/generate_financial_report.html')


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


def generate_invoice_pdf(request, payment_pk):
    payment = get_object_or_404(Payment, pk=payment_pk)
    response = generate_invoice(payment)
    return response


def generate_contract_pdf(request, instructor_pk):
    instructor = get_object_or_404(Instructor, pk=instructor_pk)
    course_id = request.GET.get('course')
    course = None
    if course_id:
        course = get_object_or_404(Course, pk=course_id)
    response = generate_contract(instructor, course)
    return response


def generate_report_pdf(request, report_pk):
    report = get_object_or_404(FinancialReport, pk=report_pk)
    response = generate_financial_report(report)
    return response
