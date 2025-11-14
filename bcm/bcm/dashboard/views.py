"""
Dashboard and Reporting Views for BCM Risk Management System

This module contains all dashboard views and export functionality including:
- Role-based dashboard views (Admin, Department User, Viewer)
- Excel export of risk data with filtering
- Professional PDF report generation with charts and analytics

The dashboard adapts its content based on user roles:
- Admins see organization-wide statistics across all departments
- Department Users see statistics limited to their department
- Viewers see the same view as Admins (read-only)

Export Features:
- Excel export: Tabular data with filtering options
- PDF export: Executive-style report with logo, charts, and department breakdown
  * Uses ReportLab for PDF generation
  * Uses Matplotlib for data visualization charts
  * Includes 4 analytical charts (pie charts and bar charts)
  * Professional layout with NCEC branding
"""

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
    """
    Main dashboard view displaying risk statistics based on user role.

    This view provides a role-aware dashboard showing relevant risk metrics:
    - Admins: Organization-wide statistics across all departments
    - Department Users: Statistics limited to their assigned department
    - Viewers: Same as admins (full visibility but read-only)

    The dashboard includes:
    - Total risks count
    - Open risks (requiring attention)
    - Critical risks (highest priority)
    - Department-wise breakdown (for admins)
    - Risk severity distribution
    - Recent risks list
    - Average resolution time

    Args:
        request (HttpRequest): The HTTP request object with authenticated user

    Returns:
        HttpResponse: Rendered dashboard template with context data

    Template:
        dashboard/home.html
    """
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
    """Export elegant PDF report with logo and charts"""
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from datetime import datetime
    import os
    from django.conf import settings

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    story = []
    styles = getSampleStyleSheet()
    width, height = letter

    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#16a34a'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )

    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#16a34a'),
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )

    # Add logo
    logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'ncec-logo-en.png')
    if os.path.exists(logo_path):
        logo = Image(logo_path, width=2*inch, height=0.8*inch)
        logo.hAlign = 'CENTER'
        story.append(logo)
        story.append(Spacer(1, 20))

    # Title
    title = Paragraph("Business Continuity Management<br/>Risk Assessment Report", title_style)
    story.append(title)

    # Date
    date_style = ParagraphStyle('DateStyle', parent=styles['Normal'], alignment=TA_CENTER, fontSize=10, textColor=colors.grey)
    story.append(Paragraph(f"Generated on: {datetime.now().strftime('%B %d, %Y at %H:%M')}", date_style))
    story.append(Spacer(1, 30))

    # Executive Summary
    story.append(Paragraph("Executive Summary", heading_style))

    total_risks = Risk.objects.count()
    open_risks = Risk.objects.filter(status='OPEN').count()
    in_progress = Risk.objects.filter(status='IN_PROGRESS').count()
    resolved_risks = Risk.objects.filter(status='RESOLVED').count()
    critical_risks = Risk.objects.filter(severity='CRITICAL').count()
    high_risks = Risk.objects.filter(severity='HIGH').count()
    medium_risks = Risk.objects.filter(severity='MEDIUM').count()
    low_risks = Risk.objects.filter(severity='LOW').count()

    # Summary statistics table
    summary_data = [
        ['Metric', 'Count', 'Percentage'],
        ['Total Risks', str(total_risks), '100%'],
        ['Open Risks', str(open_risks), f'{(open_risks/total_risks*100) if total_risks > 0 else 0:.1f}%'],
        ['In Progress', str(in_progress), f'{(in_progress/total_risks*100) if total_risks > 0 else 0:.1f}%'],
        ['Resolved Risks', str(resolved_risks), f'{(resolved_risks/total_risks*100) if total_risks > 0 else 0:.1f}%'],
        ['Critical Severity', str(critical_risks), f'{(critical_risks/total_risks*100) if total_risks > 0 else 0:.1f}%'],
        ['High Severity', str(high_risks), f'{(high_risks/total_risks*100) if total_risks > 0 else 0:.1f}%'],
    ]

    summary_table = Table(summary_data, colWidths=[3*inch, 1.5*inch, 1.5*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#16a34a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 30))

    # Create charts
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(10, 8))
    fig.patch.set_facecolor('white')

    # Chart 1: Risk Status Distribution
    status_data = [open_risks, in_progress, resolved_risks, Risk.objects.filter(status='CLOSED').count()]
    status_labels = ['Open', 'In Progress', 'Resolved', 'Closed']
    colors_status = ['#ef4444', '#3b82f6', '#22c55e', '#6b7280']
    ax1.pie(status_data, labels=status_labels, autopct='%1.1f%%', colors=colors_status, startangle=90)
    ax1.set_title('Risk Status Distribution', fontsize=12, fontweight='bold', color='#16a34a')

    # Chart 2: Severity Distribution
    severity_data = [critical_risks, high_risks, medium_risks, low_risks]
    severity_labels = ['Critical', 'High', 'Medium', 'Low']
    colors_severity = ['#dc2626', '#f59e0b', '#eab308', '#3b82f6']
    ax2.pie(severity_data, labels=severity_labels, autopct='%1.1f%%', colors=colors_severity, startangle=90)
    ax2.set_title('Severity Distribution', fontsize=12, fontweight='bold', color='#16a34a')

    # Chart 3: Top 5 Departments by Risk Count
    departments = Department.objects.filter(is_active=True)
    dept_data = []
    for dept in departments:
        count = Risk.objects.filter(department=dept).count()
        if count > 0:
            dept_data.append((dept.code, count))
    dept_data.sort(key=lambda x: x[1], reverse=True)
    dept_data = dept_data[:5]

    if dept_data:
        dept_names = [d[0] for d in dept_data]
        dept_counts = [d[1] for d in dept_data]
        ax3.barh(dept_names, dept_counts, color='#22c55e')
        ax3.set_xlabel('Number of Risks')
        ax3.set_title('Top 5 Departments by Risk Count', fontsize=12, fontweight='bold', color='#16a34a')
        ax3.invert_yaxis()

    # Chart 4: Risk Trend (Status breakdown by severity)
    severities = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
    open_by_sev = [Risk.objects.filter(severity=s, status='OPEN').count() for s in severities]
    prog_by_sev = [Risk.objects.filter(severity=s, status='IN_PROGRESS').count() for s in severities]

    x = range(len(severities))
    width = 0.35
    ax4.bar([i - width/2 for i in x], open_by_sev, width, label='Open', color='#ef4444')
    ax4.bar([i + width/2 for i in x], prog_by_sev, width, label='In Progress', color='#3b82f6')
    ax4.set_xlabel('Severity Level')
    ax4.set_ylabel('Number of Risks')
    ax4.set_title('Risk Status by Severity', fontsize=12, fontweight='bold', color='#16a34a')
    ax4.set_xticks(x)
    ax4.set_xticklabels(severities)
    ax4.legend()

    plt.tight_layout()

    # Save chart to buffer
    chart_buffer = BytesIO()
    plt.savefig(chart_buffer, format='png', dpi=150, bbox_inches='tight')
    chart_buffer.seek(0)
    plt.close()

    # Add charts to PDF
    story.append(Paragraph("Risk Analytics & Visualizations", heading_style))
    chart_image = Image(chart_buffer, width=6.5*inch, height=5.2*inch)
    story.append(chart_image)
    story.append(PageBreak())

    # Department Details
    story.append(Paragraph("Department Risk Breakdown", heading_style))
    story.append(Spacer(1, 12))

    dept_detail_data = [['Department', 'Code', 'Total', 'Open', 'Critical', 'High']]
    for dept in departments:
        dept_risks = Risk.objects.filter(department=dept)
        dept_detail_data.append([
            dept.name[:25],
            dept.code,
            str(dept_risks.count()),
            str(dept_risks.filter(status='OPEN').count()),
            str(dept_risks.filter(severity='CRITICAL').count()),
            str(dept_risks.filter(severity='HIGH').count()),
        ])

    dept_table = Table(dept_detail_data, colWidths=[2.5*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch])
    dept_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#16a34a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
    ]))
    story.append(dept_table)
    story.append(Spacer(1, 20))

    # Footer note
    footer_style = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.grey, alignment=TA_CENTER)
    story.append(Spacer(1, 30))
    story.append(Paragraph(
        "This report is confidential and for internal use only.<br/>"
        "Generated by BCM Risk Management System - NCEC",
        footer_style
    ))

    # Build PDF
    doc.build(story)

    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename=bcm_risk_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'

    return response
