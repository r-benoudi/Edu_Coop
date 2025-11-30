from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),

    # Authentication
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('change-password/', views.change_password, name='change_password'),
    
    # User Management (Admin only)
    path('users/', views.user_management, name='user_management'),
    path('users/create/', views.create_user, name='create_user'),
    
    # Expense Management
    path('expenses/', views.expense_list, name='expense_list'),
    path('expenses/add/', views.expense_create, name='expense_create'),
    path('expenses/<int:pk>/approve/', views.expense_approve, name='expense_approve'),
    path('expenses/<int:pk>/pay/', views.expense_mark_paid, name='expense_mark_paid'),
    path('expenses/report/', views.expense_report, name='expense_report'),
    
    # Recurring Expenses
    path('recurring-expenses/', views.recurring_expense_list, name='recurring_expense_list'),
    path('recurring-expenses/create/', views.recurring_expense_create, name='recurring_expense_create'),
    
    # Audit Log
    path('audit/', views.audit_log_view, name='audit_log'),

    # Intelligence & Automation (NEW)
    path('intelligence/', views.system_intelligence_dashboard, name='intelligence_dashboard'),
    path('compliance/', views.compliance_dashboard, name='compliance_dashboard'),
    path('reports/comprehensive/', views.comprehensive_report, name='comprehensive_report'),
    
    # API Endpoints (NEW)
    path('api/financial-summary/', views.api_financial_summary, name='api_financial_summary'),
    path('api/enrollment-stats/', views.api_enrollment_stats, name='api_enrollment_stats'),
    
    path('students/', views.student_list, name='student_list'),
    path('students/add/', views.student_create, name='student_create'),
    path('students/<int:pk>/', views.student_detail, name='student_detail'),
    path('students/<int:pk>/edit/', views.student_edit, name='student_edit'),
    path('students/<int:pk>/delete/', views.student_delete, name='student_delete'),
    
    path('instructors/', views.instructor_list, name='instructor_list'),
    path('instructors/add/', views.instructor_create, name='instructor_create'),
    path('instructors/<int:pk>/', views.instructor_detail, name='instructor_detail'),
    path('instructors/<int:pk>/edit/', views.instructor_edit, name='instructor_edit'),
    path('instructors/<int:pk>/delete/', views.instructor_delete, name='instructor_delete'),
    
    path('courses/', views.course_list, name='course_list'),
    path('courses/add/', views.course_create, name='course_create'),
    path('courses/<int:pk>/', views.course_detail, name='course_detail'),
    path('courses/<int:pk>/edit/', views.course_edit, name='course_edit'),
    path('courses/<int:pk>/delete/', views.course_delete, name='course_delete'),
    
    path('enrollments/', views.enrollment_list, name='enrollment_list'),
    path('enrollments/add/', views.enrollment_create, name='enrollment_create'),
    path('enrollments/<int:pk>/delete/', views.enrollment_delete, name='enrollment_delete'),
    
    path('attendance/', views.attendance_list, name='attendance_list'),
    path('attendance/record/', views.attendance_record, name='attendance_record'),
    path('attendance/report/', views.attendance_report, name='attendance_report'),
    
    path('payments/', views.payment_list, name='payment_list'),
    path('payments/student/', views.student_payment_list, name='student_payment_list'),
    path('payments/instructor/', views.instructor_payment_list, name='instructor_payment_list'),
    path('payments/generate/', views.generate_monthly_payments, name='generate_monthly_payments'),
    path('payments/<int:pk>/record/', views.record_payment, name='record_payment'),
    
    path('members/', views.member_list, name='member_list'),
    path('members/add/', views.member_create, name='member_create'),
    path('members/<int:pk>/', views.member_detail, name='member_detail'),
    path('members/<int:pk>/edit/', views.member_edit, name='member_edit'),
    path('members/<int:pk>/delete/', views.member_delete, name='member_delete'),
    
    path('financial/', views.financial_overview, name='financial_overview'),
    path('financial/report/<int:pk>/', views.financial_report_detail, name='financial_report_detail'),
    path('financial/generate/', views.generate_financial_report, name='generate_financial_report'),
    path('financial/distribute/<int:pk>/', views.distribute_profits, name='distribute_profits'),
    
    path('pdf/invoice/<int:payment_pk>/', views.generate_invoice_pdf, name='generate_invoice_pdf'),
    path('pdf/contract/<int:instructor_pk>/', views.generate_contract_pdf, name='generate_contract_pdf'),
    path('pdf/report/<int:report_pk>/', views.generate_report_pdf, name='generate_report_pdf'),
]
