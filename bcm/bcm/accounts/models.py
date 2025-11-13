from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    Custom User model with role-based access control
    Roles: Admin (BCM Manager), Department User, Viewer/Auditor
    """

    class Role(models.TextChoices):
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
        """Check if user is BCM Manager/Admin"""
        return self.role == self.Role.ADMIN

    def is_department_user(self):
        """Check if user is a Department User"""
        return self.role == self.Role.DEPARTMENT_USER

    def is_viewer(self):
        """Check if user is a Viewer/Auditor"""
        return self.role == self.Role.VIEWER

    def can_edit_risk(self, risk):
        """Check if user can edit a specific risk"""
        if self.is_admin():
            return True
        if self.is_department_user() and risk.department == self.department:
            return not risk.is_locked
        return False

    def can_view_risk(self, risk):
        """Check if user can view a specific risk"""
        if self.is_admin() or self.is_viewer():
            return True
        if self.is_department_user():
            return risk.department == self.department
        return False
