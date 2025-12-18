from django import forms
from .models import VehicleRecord, Driver

class VehicleRecordForm(forms.ModelForm):
    # Keep driver dropdown searchable/typeable
    driver = forms.ModelChoiceField(
        queryset=Driver.objects.all(),
        widget=forms.Select(attrs={
            'class': 'form-control selectpicker',
            'data-live-search': 'true'
        }),
        required=True
    )

    fuel_cost = forms.DecimalField(
        required=False,
        initial=0,  # default to 0
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

    maintenance_cost = forms.DecimalField(
        required=False,
        initial=0,  # default to 0
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

    reason_for_maintenance = forms.CharField(
        required=False,  # validated conditionally
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = VehicleRecord
        fields = [
            'date',
            'vehicle_number',
            'vehicle_type',
            'maintenance_cost',
            'fuel_cost',
            'driver',
            'distance_traveled',
            'paid_to_company',
            'bill_number',
            'bill_date',
            'reason_for_maintenance',
        ]
        widgets = {
            'date': forms.TextInput(attrs={
                'class': 'form-control',
                'readonly': 'readonly',
            }),
            'bill_date': forms.TextInput(attrs={
                'id': 'bill-nepali',
                'class': 'form-control'
            }),
            'vehicle_number': forms.TextInput(attrs={'class': 'form-control'}),
            'vehicle_type': forms.Select(attrs={'class': 'form-control'}),
            'maintenance_cost': forms.NumberInput(attrs={'class': 'form-control'}),
            'fuel_cost': forms.NumberInput(attrs={'class': 'form-control'}),
            'driver': forms.Select(attrs={
                'class': 'form-control selectpicker',
                'data-live-search': 'true'
            }),
            'distance_traveled': forms.NumberInput(attrs={'class': 'form-control'}),
            'paid_to_company': forms.TextInput(attrs={'class': 'form-control'}),
            'bill_number': forms.TextInput(attrs={'class': 'form-control'}),
            'reason_for_maintenance': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        maintenance_cost = cleaned_data.get('maintenance_cost') or 0
        reason = cleaned_data.get('reason_for_maintenance')

        # If maintenance cost > 0, reason is required
        if maintenance_cost > 0 and not reason:
            self.add_error('reason_for_maintenance',
                           "Reason for maintenance is required when maintenance cost is entered.")


# Admin form for adding drivers
class DriverForm(forms.ModelForm):
    class Meta:
        model = Driver
        fields = ['name', 'driver_id']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter driver name'}),
            'driver_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter driver ID'}),
        }
