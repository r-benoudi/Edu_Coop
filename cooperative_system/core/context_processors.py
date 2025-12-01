"""
Context processors for making user data available in all templates
Place this file in: cooperative_system/core/context_processors.py
"""

def user_permissions(request):
    """
    Add user permission checks to template context
    """
    if request.user.is_authenticated:
        return {
            'user_is_admin': request.user.is_admin,
            'user_is_manager': request.user.is_manager,
            'user_is_accountant': request.user.can_view_financials,
            'user_is_instructor': request.user.role == 'instructor',
            'user_is_staff': request.user.role == 'staff',
            'user_can_manage_students': request.user.role in ['staff', 'manager', 'admin'],
            'user_can_manage_courses': request.user.is_manager,
            'user_can_view_payments': request.user.role != 'instructor',
            'user_can_manage_payments': request.user.can_view_financials,
        }
    return {}