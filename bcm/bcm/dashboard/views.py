from django.shortcuts import render, HttpResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg, Q
from risks.models import Risk
from departments.models import Department
from accounts.models import User
from accounts.decorators import admin_required
import openpyxl
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO


@login_required
def dashboard_home(request):
    """Main dashboard view - shows different content based on user role"""
    user = request.user

    if user.is_admin():
        # BCM Manager Dashboard - All departments
        context = _get_admin_dashboard_context()
    elif user.is_department_user():
        # Department User Dashboard - Their department only
        context = _get_department_user_dashboard_context(user)
    elif user.is_viewer():
        # Viewer Dashboard - Read-only view of all
        context = _get_viewer_dashboard_context()
    else:
        context = {}

    return render(request, 'dashboard/home.html', context)


def _get_admin_dashboard_context():
    """Get dashboard context for BCM Manager"""
    departments = Department.objects.filter(is_active=True)

    # Overall statistics
    total_risks = Risk.objects.count()
    open_risks = Risk.objects.filter(status='OPEN').count()
    critical_risks = Risk.objects.filter(severity='CRITICAL').count()

    # Department-wise statistics
    dept_stats = []
    for dept in departments:
        dept_risks = Risk.objects.filter(department=dept)
        dept_stats.append({
            'department': dept,
            'total_risks': dept_risks.count(),
            'open_risks': dept_risks.filter(status='OPEN').count(),
            'critical_risks': dept_risks.filter(severity='CRITICAL').count(),
        })

    # Risk severity distribution
    severity_stats = Risk.objects.values('severity').annotate(
        count=Count('id')
    ).order_by('severity')

    # Recent risks
    recent_risks = Risk.objects.select_related('department', 'created_by').order_by('-created_at')[:10]

    # Average resolution time
    avg_resolution_hours = Risk.objects.aggregate(
        avg_hours=Avg('estimated_resolution_duration')
    )['avg_hours'] or 0

    return {
        'total_risks': total_risks,
        'open_risks': open_risks,
        'critical_risks': critical_risks,
        'dept_stats': dept_stats,
        'severity_stats': severity_stats,
        'recent_risks': recent_risks,
        'avg_resolution_hours': round(avg_resolution_hours, 1),
    }


def _get_department_user_dashboard_context(user):
    """Get dashboard context for Department User"""
    if not user.department:
        return {}

    dept_risks = Risk.objects.filter(department=user.department)

    # Department statistics
    total_risks = dept_risks.count()
    open_risks = dept_risks.filter(status='OPEN').count()
    critical_risks = dept_risks.filter(severity='CRITICAL').count()
    locked_risks = dept_risks.filter(is_locked=True).count()

    # Severity distribution
    severity_stats = dept_risks.values('severity').annotate(
        count=Count('id')
    ).order_by('severity')

    # Recent risks for this department
    recent_risks = dept_risks.select_related('created_by').order_by('-created_at')[:10]

    return {
        'department': user.department,
        'total_risks': total_risks,
        'open_risks': open_risks,
        'critical_risks': critical_risks,
        'locked_risks': locked_risks,
        'severity_stats': severity_stats,
        'recent_risks': recent_risks,
    }


def _get_viewer_dashboard_context():
    """Get dashboard context for Viewer/Auditor"""
    # Similar to admin but read-only
    return _get_admin_dashboard_context()


@admin_required
@login_required
def export_excel(request):
    """Export risks to Excel (Admin only)"""
    # Create workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "BCM Risks Report"

    # Headers
    headers = [
        'Department', 'Expected Problem', 'Impact', 'Severity', 'Status',
        'Resolution Duration', 'Created By', 'Created At', 'Locked'
    ]
    ws.append(headers)

    # Get risks based on filters
    risks = Risk.objects.select_related('department', 'created_by').all()

    # Apply filters if provided
    department_id = request.GET.get('department')
    severity = request.GET.get('severity')
    status = request.GET.get('status')

    if department_id:
        risks = risks.filter(department_id=department_id)
    if severity:
        risks = risks.filter(severity=severity)
    if status:
        risks = risks.filter(status=status)

    # Add data
    for risk in risks:
        ws.append([
            risk.department.name,
            risk.expected_problem[:100],
            risk.impact[:100],
            risk.get_severity_display(),
            risk.get_status_display(),
            risk.get_resolution_duration_display_full(),
            risk.created_by.get_full_name() if risk.created_by else 'N/A',
            risk.created_at.strftime('%Y-%m-%d %H:%M'),
            'Yes' if risk.is_locked else 'No'
        ])

    # Create response
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=bcm_risks_report.xlsx'
    wb.save(response)

    return response


@admin_required
@login_required
def export_pdf(request):
    """Export risks summary to PDF (Admin only)"""
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Title
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, height - 50, "BCM Risk Management Report")

    # Summary statistics
    p.setFont("Helvetica", 12)
    y = height - 100

    total_risks = Risk.objects.count()
    open_risks = Risk.objects.filter(status='OPEN').count()
    critical_risks = Risk.objects.filter(severity='CRITICAL').count()

    p.drawString(50, y, f"Total Risks: {total_risks}")
    y -= 20
    p.drawString(50, y, f"Open Risks: {open_risks}")
    y -= 20
    p.drawString(50, y, f"Critical Risks: {critical_risks}")
    y -= 40

    # Department summary
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, "Department Summary")
    y -= 20
    p.setFont("Helvetica", 10)

    departments = Department.objects.filter(is_active=True)
    for dept in departments:
        dept_risk_count = Risk.objects.filter(department=dept).count()
        p.drawString(50, y, f"{dept.name}: {dept_risk_count} risks")
        y -= 15
        if y < 100:
            p.showPage()
            y = height - 50

    p.showPage()
    p.save()

    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=bcm_risks_summary.pdf'

    return response
