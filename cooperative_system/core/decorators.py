"""
Role-based access control decorators for the Educational Cooperative System
Place this file in: cooperative_system/core/decorators.py
"""

from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from functools import wraps


def admin_required(view_func):
    """Decorator to require admin role"""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_admin:
            messages.error(request, 'You do not have permission to access this page. Admin access required.')
            return redirect('core:dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def manager_required(view_func):
    """Decorator to require manager or admin role"""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_manager:
            messages.error(request, 'You do not have permission to access this page. Manager access required.')
            return redirect('core:dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def accountant_required(view_func):
    """Decorator to require accountant, manager, or admin role"""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.can_view_financials:
            messages.error(request, 'You do not have permission to access this page. Accountant access required.')
            return redirect('core:dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def instructor_required(view_func):
    """Decorator to require instructor role (or higher)"""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role not in ['instructor', 'admin', 'manager']:
            messages.error(request, 'You do not have permission to access this page. Instructor access required.')
            return redirect('core:dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def staff_or_higher(view_func):
    """Decorator to require staff role or higher (all authenticated users)"""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        # All authenticated users with staff role or higher can access
        return view_func(request, *args, **kwargs)
    return wrapper


def can_manage_students(view_func):
    """Decorator for views that can add/edit students (staff and higher)"""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role not in ['staff', 'manager', 'admin']:
            messages.error(request, 'You do not have permission to manage students.')
            return redirect('core:student_list')
        return view_func(request, *args, **kwargs)
    return wrapper


def can_manage_courses(view_func):
    """Decorator for views that can add/edit courses (manager and higher)"""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_manager:
            messages.error(request, 'You do not have permission to manage courses.')
            return redirect('core:course_list')
        return view_func(request, *args, **kwargs)
    return wrapper


def can_manage_enrollments(view_func):
    """Decorator for views that can manage enrollments (staff and higher)"""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role not in ['staff', 'manager', 'admin']:
            messages.error(request, 'You do not have permission to manage enrollments.')
            return redirect('core:enrollment_list')
        return view_func(request, *args, **kwargs)
    return wrapper


def can_record_attendance(view_func):
    """Decorator for views that can record attendance (instructors and higher)"""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role not in ['instructor', 'staff', 'manager', 'admin']:
            messages.error(request, 'You do not have permission to record attendance.')
            return redirect('core:attendance_list')
        return view_func(request, *args, **kwargs)
    return wrapper


def can_view_payments(view_func):
    """Decorator for views that can view payment information"""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role == 'instructor':
            messages.error(request, 'You do not have permission to view all payments.')
            return redirect('core:dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def can_manage_payments(view_func):
    """Decorator for views that can manage payments (accountant and higher)"""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.can_view_financials:
            messages.error(request, 'You do not have permission to manage payments.')
            return redirect('core:dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def can_view_financials(view_func):
    """Decorator for financial reports and data"""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.can_view_financials:
            messages.error(request, 'You do not have permission to view financial information.')
            return redirect('core:dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper