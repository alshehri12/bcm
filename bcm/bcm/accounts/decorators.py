from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied


def role_required(*roles):
    """
    Decorator to restrict access based on user role
    Usage: @role_required('ADMIN', 'DEPARTMENT_USER')
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('accounts:login')

            if request.user.role not in roles:
                messages.error(request, 'You do not have permission to access this page.')
                raise PermissionDenied

            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator


def admin_required(view_func):
    """Decorator to restrict access to BCM Managers (Admins) only"""
    return role_required('ADMIN')(view_func)


def department_user_required(view_func):
    """Decorator to restrict access to Department Users only"""
    return role_required('DEPARTMENT_USER')(view_func)


def department_user_or_admin_required(view_func):
    """Decorator to allow access to Department Users or Admins"""
    return role_required('ADMIN', 'DEPARTMENT_USER')(view_func)
