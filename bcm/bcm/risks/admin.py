from django.contrib import admin
from django.utils.html import format_html
from .models import Risk


@admin.register(Risk)
class RiskAdmin(admin.ModelAdmin):
    """Risk Admin configuration"""

    list_display = [
        'id',
        'department',
        'expected_problem_short',
        'severity_badge',
        'status_badge',
        'is_locked',
        'created_by',
        'created_at'
    ]

    list_filter = [
        'severity',
        'status',
        'is_locked',
        'department',
        'created_at',
        'resolution_duration_unit'
    ]

    search_fields = [
        'expected_problem',
        'impact',
        'mitigation_notes',
        'department__name',
        'created_by__username'
    ]

    readonly_fields = [
        'created_at',
        'updated_at',
        'locked_at',
        'created_by',
        'updated_by',
        'locked_by'
    ]

    fieldsets = (
        ('Risk Information', {
            'fields': ('department', 'expected_problem', 'impact', 'mitigation_notes')
        }),
        ('Classification', {
            'fields': ('severity', 'status', 'estimated_resolution_duration', 'resolution_duration_unit')
        }),
        ('Lock Status', {
            'fields': ('is_locked', 'locked_by', 'locked_at')
        }),
        ('Tracking', {
            'fields': ('created_by', 'created_at', 'updated_by', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def expected_problem_short(self, obj):
        """Display shortened problem description"""
        return obj.expected_problem[:100] + '...' if len(obj.expected_problem) > 100 else obj.expected_problem
    expected_problem_short.short_description = 'Expected Problem'

    def severity_badge(self, obj):
        """Display severity with color badge"""
        colors = {
            'LOW': '#28a745',
            'MEDIUM': '#ffc107',
            'HIGH': '#fd7e14',
            'CRITICAL': '#dc3545'
        }
        color = colors.get(obj.severity, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color,
            obj.get_severity_display()
        )
    severity_badge.short_description = 'Severity'

    def status_badge(self, obj):
        """Display status with color badge"""
        colors = {
            'OPEN': '#17a2b8',
            'IN_PROGRESS': '#ffc107',
            'RESOLVED': '#28a745',
            'CLOSED': '#6c757d'
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    actions = ['lock_risks', 'unlock_risks']

    def lock_risks(self, request, queryset):
        """Lock selected risks"""
        for risk in queryset:
            risk.lock(request.user)
        self.message_user(request, f'{queryset.count()} risk(s) locked successfully.')
    lock_risks.short_description = 'Lock selected risks'

    def unlock_risks(self, request, queryset):
        """Unlock selected risks"""
        queryset.update(is_locked=False, locked_by=None, locked_at=None)
        self.message_user(request, f'{queryset.count()} risk(s) unlocked successfully.')
    unlock_risks.short_description = 'Unlock selected risks'
