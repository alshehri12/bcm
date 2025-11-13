from django import forms
from .models import Risk
from departments.models import Department


class RiskForm(forms.ModelForm):
    """Form for creating and editing risks"""

    class Meta:
        model = Risk
        fields = [
            'department',
            'expected_problem',
            'impact',
            'estimated_resolution_duration',
            'resolution_duration_unit',
            'mitigation_notes',
            'severity',
            'status'
        ]
        widgets = {
            'department': forms.Select(attrs={
                'class': 'form-control'
            }),
            'expected_problem': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe the potential risk or expected problem'
            }),
            'impact': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe the expected impact if this risk occurs'
            }),
            'estimated_resolution_duration': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'placeholder': 'Enter estimated resolution time'
            }),
            'resolution_duration_unit': forms.Select(attrs={
                'class': 'form-control'
            }),
            'mitigation_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Optional: Describe mitigation plan or action items'
            }),
            'severity': forms.Select(attrs={
                'class': 'form-control'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            }),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # If user is a department user, hide and auto-set department
        if user and hasattr(user, 'is_department_user') and user.is_department_user():
            # Remove department field for department users
            self.fields.pop('department', None)
        else:
            # For admins, show department dropdown with all active departments
            self.fields['department'].queryset = Department.objects.filter(is_active=True)
            self.fields['department'].required = True


class RiskFilterForm(forms.Form):
    """Form for filtering risks"""

    severity = forms.ChoiceField(
        choices=[('', 'All Severities')] + list(Risk.Severity.choices),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + list(Risk.Status.choices),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search risks...'
        })
    )
