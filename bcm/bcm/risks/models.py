"""
Risk Models for BCM (Business Continuity Management) System

This module defines the core Risk model used to track and manage potential risks
identified by departments. Each risk includes:
- Problem description and impact assessment
- Severity level and current status
- Estimated resolution timeframe
- Mitigation action plans
- Locking mechanism for BCM manager review

The model supports ISO 31000 risk management principles.
"""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.mail import send_mail


class Risk(models.Model):
    """
    Core Risk model representing potential risks identified by departments.

    This model captures all essential risk information required for Business Continuity Management:
    - Risk identification (problem description, department)
    - Risk assessment (severity, impact)
    - Risk treatment (mitigation notes, resolution timeline)
    - Risk monitoring (status, locking mechanism)

    The model includes a locking mechanism where BCM Managers can lock risks after review,
    preventing further edits by department users until unlocked.

    Attributes:
        department (FK): Department responsible for this risk
        expected_problem (text): Description of the potential risk/problem
        impact (text): Expected impact if this risk occurs
        estimated_resolution_duration (int): Time needed to resolve the risk
        resolution_duration_unit (str): Unit of time (hours, days, or weeks)
        mitigation_notes (text): Action plan and mitigation strategies
        severity (str): Risk severity level (LOW, MEDIUM, HIGH, CRITICAL)
        status (str): Current status (OPEN, IN_PROGRESS, RESOLVED, CLOSED)
        is_locked (bool): Whether risk is locked by BCM Manager
        created_by (FK): User who created this risk
        updated_by (FK): User who last updated this risk
        created_at (datetime): Creation timestamp
        updated_at (datetime): Last update timestamp
    """

    class Status(models.TextChoices):
        """
        Risk status enumeration tracking the lifecycle of a risk.

        Workflow: OPEN → IN_PROGRESS → RESOLVED → CLOSED
        """
        OPEN = 'OPEN', _('Open')
        IN_PROGRESS = 'IN_PROGRESS', _('In Progress')
        RESOLVED = 'RESOLVED', _('Resolved')
        CLOSED = 'CLOSED', _('Closed')

    class Severity(models.TextChoices):
        """
        Risk severity levels based on potential impact.

        Levels are used to prioritize risk treatment:
        - LOW: Minimal impact, can be handled in routine operations
        - MEDIUM: Moderate impact, requires attention
        - HIGH: Significant impact, requires immediate attention
        - CRITICAL: Severe impact, requires urgent action and escalation
        """
        LOW = 'LOW', _('Low')
        MEDIUM = 'MEDIUM', _('Medium')
        HIGH = 'HIGH', _('High')
        CRITICAL = 'CRITICAL', _('Critical')

    class DurationUnit(models.TextChoices):
        """
        Time unit options for estimated resolution duration.

        Used to specify whether resolution time is measured in hours, days, or weeks.
        """
        HOURS = 'HOURS', _('Hours')
        DAYS = 'DAYS', _('Days')
        WEEKS = 'WEEKS', _('Weeks')

    # Core Risk Information
    department = models.ForeignKey(
        'departments.Department',
        on_delete=models.CASCADE,
        related_name='risks',
        help_text=_('Department this risk belongs to')
    )

    expected_problem = models.TextField(
        help_text=_('Description of the potential risk/expected problem')
    )

    impact = models.TextField(
        help_text=_('Expected impact if this risk occurs')
    )

    estimated_resolution_duration = models.PositiveIntegerField(
        help_text=_('Estimated time to resolve this risk')
    )

    resolution_duration_unit = models.CharField(
        max_length=10,
        choices=DurationUnit.choices,
        default=DurationUnit.HOURS,
        help_text=_('Unit for resolution duration')
    )

    mitigation_notes = models.TextField(
        blank=True,
        null=True,
        help_text=_('Action plan and mitigation notes (optional)')
    )

    # Risk Classification
    severity = models.CharField(
        max_length=20,
        choices=Severity.choices,
        default=Severity.MEDIUM,
        help_text=_('Risk severity level')
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OPEN,
        help_text=_('Current status of this risk')
    )

    # Tracking & Permissions
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_risks',
        help_text=_('User who created this risk entry')
    )

    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='updated_risks',
        help_text=_('User who last updated this risk')
    )

    is_locked = models.BooleanField(
        default=False,
        help_text=_('Locked by BCM Manager after review (prevents department editing)')
    )

    locked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='locked_risks',
        help_text=_('BCM Manager who locked this risk')
    )

    locked_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('When this risk was locked')
    )

    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_('When this risk was created')
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        help_text=_('When this risk was last updated')
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Risk')
        verbose_name_plural = _('Risks')
        indexes = [
            models.Index(fields=['department', 'status']),
            models.Index(fields=['severity']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"{self.department.code} - {self.expected_problem[:50]}... ({self.get_severity_display()})"

    def get_resolution_duration_display_full(self):
        """
        Get human-readable resolution duration with unit.

        Returns:
            str: Formatted string like "4 Hours", "2 Days", "1 Weeks"

        Example:
            >>> risk.estimated_resolution_duration = 24
            >>> risk.resolution_duration_unit = 'HOURS'
            >>> risk.get_resolution_duration_display_full()
            "24 Hours"
        """
        return f"{self.estimated_resolution_duration} {self.get_resolution_duration_unit_display()}"

    def get_resolution_hours(self):
        """
        Convert resolution duration to hours for uniform comparison and sorting.

        This method normalizes all durations to hours regardless of the original unit,
        making it easy to compare and sort risks by resolution time.

        Returns:
            int: Resolution duration converted to hours

        Conversion rates:
            - Hours: 1:1
            - Days: 1 day = 24 hours
            - Weeks: 1 week = 168 hours (24 × 7)

        Example:
            >>> risk.estimated_resolution_duration = 2
            >>> risk.resolution_duration_unit = 'DAYS'
            >>> risk.get_resolution_hours()
            48
        """
        if self.resolution_duration_unit == self.DurationUnit.HOURS:
            return self.estimated_resolution_duration
        elif self.resolution_duration_unit == self.DurationUnit.DAYS:
            return self.estimated_resolution_duration * 24
        elif self.resolution_duration_unit == self.DurationUnit.WEEKS:
            return self.estimated_resolution_duration * 24 * 7
        return 0

    def lock(self, user):
        """
        Lock this risk to prevent further editing by department users.

        When a BCM Manager reviews a risk, they can lock it to prevent department users
        from making changes. This ensures data integrity during review processes.
        Only BCM Managers can lock/unlock risks.

        Args:
            user (User): The BCM Manager locking this risk

        Side effects:
            - Sets is_locked to True
            - Records who locked it (locked_by)
            - Records when it was locked (locked_at)
            - Saves the model with only these fields updated
        """
        from django.utils import timezone
        self.is_locked = True
        self.locked_by = user
        self.locked_at = timezone.now()
        self.save(update_fields=['is_locked', 'locked_by', 'locked_at'])

    def unlock(self):
        """
        Unlock this risk to allow department users to edit it again.

        This removes the lock applied by a BCM Manager, allowing department users
        to update the risk information.

        Side effects:
            - Sets is_locked to False
            - Clears locked_by reference
            - Clears locked_at timestamp
            - Saves the model with only these fields updated
        """
        self.is_locked = False
        self.locked_by = None
        self.locked_at = None
        self.save(update_fields=['is_locked', 'locked_by', 'locked_at'])

    def send_notification_email(self, action='created'):
        """
        Send email notification to BCM Managers when risk is created or updated.

        This method sends an email alert to all active admin users (BCM Managers)
        whenever a risk is created or modified. The email includes key risk details
        for quick review.

        Args:
            action (str): Action performed ('created' or 'updated')

        Email content includes:
            - Department name
            - Expected problem description
            - Severity and status
            - Estimated resolution time
            - Creator information
            - Creation timestamp

        Note:
            - Only sends to active admin users with valid email addresses
            - Uses fail_silently=True to prevent errors from breaking the application
            - Email backend is configured in Django settings (console backend for development)
        """
        subject = f"BCM Risk {action.title()}: {self.department.name}"
        message = f"""
        A risk has been {action} for department: {self.department.name}

        Expected Problem: {self.expected_problem}
        Severity: {self.get_severity_display()}
        Status: {self.get_status_display()}
        Estimated Resolution: {self.get_resolution_duration_display_full()}

        Created by: {self.created_by.get_full_name() if self.created_by else 'N/A'}
        Created at: {self.created_at.strftime('%Y-%m-%d %H:%M')}
        """

        # Send to BCM Managers (admins)
        from accounts.models import User
        admin_emails = User.objects.filter(role=User.Role.ADMIN, is_active=True).values_list('email', flat=True)
        admin_emails = [email for email in admin_emails if email]

        if admin_emails:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@bcm.com',
                admin_emails,
                fail_silently=True,
            )
