"""
Department Models for BCM Risk Management System

This module defines the Department model which represents organizational departments.
Departments are the primary organizational unit for risk management:
- Each department can have multiple users assigned to it
- Each department tracks its own risks
- Department Users can only manage risks within their department
- BCM Managers can view and manage risks across all departments
"""

from django.db import models
from django.utils.translation import gettext_lazy as _


class Department(models.Model):
    """
    Model representing an organizational department within the company.

    Departments are the core organizational unit in the BCM system. Each department:
    - Has assigned users (Department Users) who manage risks
    - Maintains a portfolio of identified risks
    - Has a department head responsible for oversight
    - Can be activated/deactivated without data loss

    Relationships:
        - users (reverse FK): All users assigned to this department
        - risks (reverse FK): All risks identified by this department

    Attributes:
        name (str): Full department name (unique)
        code (str): Short department code/abbreviation (unique, e.g., "IT", "HR")
        description (text): Optional department description
        head_name (str): Name of the department head/manager
        contact_email (email): Department contact email
        contact_phone (str): Department contact phone number
        is_active (bool): Whether this department is currently active
        created_at (datetime): Department creation timestamp
        updated_at (datetime): Last modification timestamp
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
        """
        Get the number of active users assigned to this department.

        Returns:
            int: Count of active users (is_active=True) in this department

        Used for:
            - Dashboard statistics
            - Department overview pages
            - Resource allocation analysis
        """
        return self.users.filter(is_active=True).count()

    def get_total_risks_count(self):
        """
        Get the total number of risks identified by this department.

        This includes risks in all statuses (OPEN, IN_PROGRESS, RESOLVED, CLOSED).

        Returns:
            int: Total count of all risks for this department

        Used for:
            - Department risk portfolio overview
            - Dashboard KPIs
            - Risk statistics and reporting
        """
        return self.risks.count()

    def get_open_risks_count(self):
        """
        Get the number of risks currently in OPEN status for this department.

        Open risks are those that have been identified but not yet addressed.
        This is a key metric for assessing department risk exposure.

        Returns:
            int: Count of risks with status='OPEN'

        Used for:
            - Dashboard alerts and warnings
            - Priority assessment
            - Workload planning
        """
        return self.risks.filter(status='OPEN').count()
