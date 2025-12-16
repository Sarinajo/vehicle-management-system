from django import forms
from .models import VehicleRecord

class VehicleRecordForm(forms.ModelForm):
    class Meta:
        model = VehicleRecord
        fields = [
            'date',
            'vehicle_number',
            'vehicle_type',
            'maintenance_cost',
            'fuel_cost',
            'driver_name',
            'paid_to_company',
            'bill_number',
            'bill_date',
            'remarks',
        ]
        widgets = {
            'date': forms.TextInput(attrs={'id': 'date-nepali', 'class': 'form-control'}),
            'bill_date': forms.TextInput(attrs={'id': 'bill-nepali', 'class': 'form-control'}),
            'vehicle_number': forms.TextInput(attrs={'class': 'form-control'}),
            'vehicle_type': forms.Select(attrs={'class': 'form-control'}),
            'maintenance_cost': forms.NumberInput(attrs={'class': 'form-control'}),
            'fuel_cost': forms.NumberInput(attrs={'class': 'form-control'}),
            'driver_name': forms.TextInput(attrs={'class': 'form-control'}),
            'paid_to_company': forms.TextInput(attrs={'class': 'form-control'}),
            'bill_number': forms.TextInput(attrs={'class': 'form-control'}),
            'remarks': forms.TextInput(attrs={'class': 'form-control'}),
        }
