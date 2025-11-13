from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.mail import send_mail


class Risk(models.Model):
    """
    Risk model representing potential risks identified by departments
    Based on BRD requirements:
    - Expected Problem (Potential Risk)
    - Impact if Occurred
    - Estimated Resolution Duration
    - Mitigation Notes / Action Plan
    """

    class Status(models.TextChoices):
        OPEN = 'OPEN', _('Open')
        IN_PROGRESS = 'IN_PROGRESS', _('In Progress')
        RESOLVED = 'RESOLVED', _('Resolved')
        CLOSED = 'CLOSED', _('Closed')

    class Severity(models.TextChoices):
        LOW = 'LOW', _('Low')
        MEDIUM = 'MEDIUM', _('Medium')
        HIGH = 'HIGH', _('High')
        CRITICAL = 'CRITICAL', _('Critical')

    class DurationUnit(models.TextChoices):
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
        """Return full resolution duration with unit"""
        return f"{self.estimated_resolution_duration} {self.get_resolution_duration_unit_display()}"

    def get_resolution_hours(self):
        """Convert resolution duration to hours for comparison"""
        if self.resolution_duration_unit == self.DurationUnit.HOURS:
            return self.estimated_resolution_duration
        elif self.resolution_duration_unit == self.DurationUnit.DAYS:
            return self.estimated_resolution_duration * 24
        elif self.resolution_duration_unit == self.DurationUnit.WEEKS:
            return self.estimated_resolution_duration * 24 * 7
        return 0

    def lock(self, user):
        """Lock this risk (BCM Manager only)"""
        from django.utils import timezone
        self.is_locked = True
        self.locked_by = user
        self.locked_at = timezone.now()
        self.save(update_fields=['is_locked', 'locked_by', 'locked_at'])

    def unlock(self):
        """Unlock this risk"""
        self.is_locked = False
        self.locked_by = None
        self.locked_at = None
        self.save(update_fields=['is_locked', 'locked_by', 'locked_at'])

    def send_notification_email(self, action='created'):
        """Send notification email when risk is created or updated"""
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
