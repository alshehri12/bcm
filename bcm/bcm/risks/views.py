from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from .models import Risk
from .forms import RiskForm, RiskFilterForm
from accounts.decorators import department_user_or_admin_required, admin_required


@login_required
def risk_list(request):
    """List all risks based on user role and permissions"""
    user = request.user

    # Base queryset based on user role
    if user.is_admin() or user.is_viewer():
        risks = Risk.objects.all()
    elif user.is_department_user():
        risks = Risk.objects.filter(department=user.department)
    else:
        risks = Risk.objects.none()

    # Apply filters
    form = RiskFilterForm(request.GET)
    if form.is_valid():
        if form.cleaned_data.get('severity'):
            risks = risks.filter(severity=form.cleaned_data['severity'])
        if form.cleaned_data.get('status'):
            risks = risks.filter(status=form.cleaned_data['status'])
        if form.cleaned_data.get('search'):
            search_term = form.cleaned_data['search']
            risks = risks.filter(
                Q(expected_problem__icontains=search_term) |
                Q(impact__icontains=search_term) |
                Q(mitigation_notes__icontains=search_term)
            )

    # Ordering and pagination
    risks = risks.select_related('department', 'created_by').order_by('-created_at')
    paginator = Paginator(risks, 20)  # Show 20 risks per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'filter_form': form,
    }
    return render(request, 'risks/risk_list.html', context)


@login_required
def risk_detail(request, pk):
    """View details of a specific risk"""
    risk = get_object_or_404(Risk, pk=pk)

    # Check if user can view this risk
    if not request.user.can_view_risk(risk):
        messages.error(request, 'You do not have permission to view this risk.')
        return redirect('risks:list')

    context = {
        'risk': risk,
        'can_edit': request.user.can_edit_risk(risk),
    }
    return render(request, 'risks/risk_detail.html', context)


@department_user_or_admin_required
@login_required
def risk_create(request):
    """Create a new risk"""
    if request.method == 'POST':
        form = RiskForm(request.POST, user=request.user)
        if form.is_valid():
            risk = form.save(commit=False)

            # Set department based on user role
            if request.user.is_department_user():
                risk.department = request.user.department
            elif request.user.is_admin():
                # Department is set from form field for admins
                pass

            risk.created_by = request.user
            risk.updated_by = request.user
            risk.save()

            # Send notification email
            risk.send_notification_email(action='created')

            messages.success(request, 'Risk created successfully.')
            return redirect('risks:detail', pk=risk.pk)
    else:
        form = RiskForm(user=request.user)

    context = {
        'form': form,
        'action': 'Create',
    }
    return render(request, 'risks/risk_form.html', context)


@department_user_or_admin_required
@login_required
def risk_update(request, pk):
    """Update an existing risk"""
    risk = get_object_or_404(Risk, pk=pk)

    # Check if user can edit this risk
    if not request.user.can_edit_risk(risk):
        messages.error(request, 'You do not have permission to edit this risk.')
        return redirect('risks:detail', pk=risk.pk)

    if request.method == 'POST':
        form = RiskForm(request.POST, instance=risk, user=request.user)
        if form.is_valid():
            risk = form.save(commit=False)
            risk.updated_by = request.user
            risk.save()

            # Send notification email
            risk.send_notification_email(action='updated')

            messages.success(request, 'Risk updated successfully.')
            return redirect('risks:detail', pk=risk.pk)
    else:
        form = RiskForm(instance=risk, user=request.user)

    context = {
        'form': form,
        'risk': risk,
        'action': 'Update',
    }
    return render(request, 'risks/risk_form.html', context)


@admin_required
@login_required
def risk_delete(request, pk):
    """Delete a risk (Admin only)"""
    risk = get_object_or_404(Risk, pk=pk)

    if request.method == 'POST':
        risk.delete()
        messages.success(request, 'Risk deleted successfully.')
        return redirect('risks:list')

    context = {
        'risk': risk,
    }
    return render(request, 'risks/risk_confirm_delete.html', context)


@admin_required
@login_required
def risk_lock(request, pk):
    """Lock a risk (Admin only)"""
    risk = get_object_or_404(Risk, pk=pk)
    risk.lock(request.user)
    messages.success(request, f'Risk locked successfully.')
    return redirect('risks:detail', pk=risk.pk)


@admin_required
@login_required
def risk_unlock(request, pk):
    """Unlock a risk (Admin only)"""
    risk = get_object_or_404(Risk, pk=pk)
    risk.unlock()
    messages.success(request, f'Risk unlocked successfully.')
    return redirect('risks:detail', pk=risk.pk)
