from django.db import models
from django.utils.translation import gettext_lazy as _


class Department(models.Model):
    """
    Department model representing organizational departments
    Each department can have multiple users and risks
    """

    name = models.CharField(
        max_length=200,
        unique=True,
        help_text=_('Department name')
    )

    code = models.CharField(
        max_length=20,
        unique=True,
        help_text=_('Department code/abbreviation')
    )

    description = models.TextField(
        blank=True,
        null=True,
        help_text=_('Department description')
    )

    head_name = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text=_('Name of department head')
    )

    contact_email = models.EmailField(
        blank=True,
        null=True,
        help_text=_('Department contact email')
    )

    contact_phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text=_('Department contact phone')
    )

    is_active = models.BooleanField(
        default=True,
        help_text=_('Is this department active?')
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = _('Department')
        verbose_name_plural = _('Departments')

    def __str__(self):
        return f"{self.name} ({self.code})"

    def get_active_users_count(self):
        """Return count of active users in this department"""
        return self.users.filter(is_active=True).count()

    def get_total_risks_count(self):
        """Return total count of risks for this department"""
        return self.risks.count()

    def get_open_risks_count(self):
        """Return count of open/active risks"""
        return self.risks.filter(status='OPEN').count()
