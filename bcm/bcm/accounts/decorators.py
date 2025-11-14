"""
Role-Based Access Control Decorators for BCM Risk Management System

This module provides view decorators that enforce role-based access control (RBAC).
These decorators protect views from unauthorized access based on user roles.

Available decorators:
- @role_required(*roles): Generic decorator accepting one or more roles
- @admin_required: Restricts access to Admins (BCM Managers) only
- @department_user_required: Restricts access to Department Users only
- @department_user_or_admin_required: Allows both Department Users and Admins

Usage example:
    @admin_required
    @login_required
    def export_pdf(request):
        # Only admins can access this view
        ...

Security:
- Unauthenticated users are redirected to login page
- Authenticated users without proper role see error message and get PermissionDenied (403)
- Always use @login_required in combination with these decorators for complete protection
"""

from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied


def role_required(*roles):
    """
    Generic decorator factory to restrict view access based on user role(s).

    This is a higher-order function that creates a decorator which checks if the
    current user has one of the specified roles. It provides a flexible way to
    implement role-based access control for any combination of roles.

    Args:
        *roles (str): One or more role names (e.g., 'ADMIN', 'DEPARTMENT_USER', 'VIEWER')
                     The user must have at least one of these roles to access the view

    Returns:
        function: A decorator function that can be applied to views

    Behavior:
        - If user is not authenticated: Redirects to login page
        - If user doesn't have any of the required roles:
          * Shows error message
          * Raises PermissionDenied (HTTP 403)
        - If user has appropriate role: Allows access to the view

    Example:
        >>> @role_required('ADMIN', 'VIEWER')
        >>> def view_all_risks(request):
        >>>     # Only admins and viewers can access
        >>>     ...

    Note:
        Should be used with @login_required for complete protection:
        @role_required('ADMIN')
        @login_required
        def admin_dashboard(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            # Check if user is authenticated first
            if not request.user.is_authenticated:
                return redirect('accounts:login')

            # Check if user has one of the required roles
            if request.user.role not in roles:
                messages.error(request, 'You do not have permission to access this page.')
                raise PermissionDenied

            # User is authenticated and has proper role - allow access
            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator


def admin_required(view_func):
    """
    Decorator to restrict access to BCM Managers (Admins) only.

    This decorator ensures only users with the ADMIN role can access the view.
    Admins have full system access including:
    - Managing all risks across all departments
    - Locking/unlocking risks
    - Accessing all reports and analytics
    - Managing users and departments

    Args:
        view_func (function): The view function to protect

    Returns:
        function: Wrapped view with admin access control

    Example:
        >>> @admin_required
        >>> @login_required
        >>> def delete_risk(request, pk):
        >>>     # Only admins can delete risks
        >>>     ...

    Usage in views:
        - Export functions (PDF, Excel)
        - Delete operations
        - Lock/unlock operations
        - System-wide reports
    """
    return role_required('ADMIN')(view_func)


def department_user_required(view_func):
    """
    Decorator to restrict access to Department Users only.

    This decorator ensures only users with the DEPARTMENT_USER role can access the view.
    Department Users can:
    - Manage risks within their assigned department
    - View and edit unlocked risks
    - Create new risks for their department

    Args:
        view_func (function): The view function to protect

    Returns:
        function: Wrapped view with department user access control

    Note:
        This decorator alone is rarely used. Usually, you want to allow both
        department users AND admins using @department_user_or_admin_required
    """
    return role_required('DEPARTMENT_USER')(view_func)


def department_user_or_admin_required(view_func):
    """
    Decorator to allow access to both Department Users and Admins.

    This is the most commonly used decorator for risk management operations.
    It allows both regular department users and admins to perform actions like
    creating, editing, and viewing risks.

    Args:
        view_func (function): The view function to protect

    Returns:
        function: Wrapped view accessible to department users and admins

    Example:
        >>> @department_user_or_admin_required
        >>> @login_required
        >>> def create_risk(request):
        >>>     # Both department users and admins can create risks
        >>>     ...

    Usage in views:
        - risk_create: Both can create risks
        - risk_update: Both can edit risks (with additional permission checks)
        - Most risk management CRUD operations

    Note:
        Viewers (read-only role) are explicitly excluded from these operations.
    """
    return role_required('ADMIN', 'DEPARTMENT_USER')(view_func)
