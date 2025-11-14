"""
User Account Models for BCM Risk Management System

This module defines the custom User model with role-based access control (RBAC).
The system supports three roles:
- Admin (BCM Manager): Full access to all features and departments
- Department User: Limited access to their department's risks
- Viewer/Auditor: Read-only access to all risks for compliance/audit purposes
"""

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser with additional fields and role-based permissions.

    This model implements role-based access control for the BCM system:
    - Admins can manage all risks across all departments
    - Department Users can manage risks only within their department
    - Viewers have read-only access for auditing purposes

    Attributes:
        role (str): User's role (ADMIN, DEPARTMENT_USER, or VIEWER)
        department (FK): Department this user belongs to (required for Department Users)
        phone (str): Contact phone number
        language (str): Preferred language (en or ar) for UI
        created_at (datetime): Account creation timestamp
        updated_at (datetime): Last modification timestamp
    """

    class Role(models.TextChoices):
        """
        Enumeration of available user roles in the system.

        Roles define what actions a user can perform:
        - ADMIN: BCM Manager with full system access
        - DEPARTMENT_USER: Can manage risks for their assigned department
        - VIEWER: Read-only access for auditing and compliance
        """
        ADMIN = 'ADMIN', _('Admin (BCM Manager)')
        DEPARTMENT_USER = 'DEPARTMENT_USER', _('Department User')
        VIEWER = 'VIEWER', _('Viewer/Auditor')

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.DEPARTMENT_USER,
        help_text=_('User role determines access permissions')
    )

    department = models.ForeignKey(
        'departments.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
        help_text=_('Department this user belongs to (required for Department Users)')
    )

    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text=_('Contact phone number')
    )

    language = models.CharField(
        max_length=10,
        choices=[('en', 'English'), ('ar', 'العربية')],
        default='en',
        help_text=_('Preferred language')
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['username']
        verbose_name = _('User')
        verbose_name_plural = _('Users')

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    def is_admin(self):
        """
        Check if user has Admin (BCM Manager) role.

        Returns:
            bool: True if user is an admin, False otherwise
        """
        return self.role == self.Role.ADMIN

    def is_department_user(self):
        """
        Check if user has Department User role.

        Returns:
            bool: True if user is a department user, False otherwise
        """
        return self.role == self.Role.DEPARTMENT_USER

    def is_viewer(self):
        """
        Check if user has Viewer/Auditor role.

        Returns:
            bool: True if user is a viewer, False otherwise
        """
        return self.role == self.Role.VIEWER

    def can_edit_risk(self, risk):
        """
        Determine if this user has permission to edit a specific risk.

        Permission logic:
        - Admins: Can edit all risks
        - Department Users: Can edit risks in their department if not locked
        - Viewers: Cannot edit any risks (read-only)

        Args:
            risk (Risk): The risk object to check permissions for

        Returns:
            bool: True if user can edit the risk, False otherwise
        """
        if self.is_admin():
            return True
        if self.is_department_user() and risk.department == self.department:
            # Department users cannot edit locked risks
            return not risk.is_locked
        return False

    def can_view_risk(self, risk):
        """
        Determine if this user has permission to view a specific risk.

        Permission logic:
        - Admins and Viewers: Can view all risks across all departments
        - Department Users: Can only view risks in their department

        Args:
            risk (Risk): The risk object to check permissions for

        Returns:
            bool: True if user can view the risk, False otherwise
        """
        if self.is_admin() or self.is_viewer():
            return True
        if self.is_department_user():
            return risk.department == self.department
        return False
