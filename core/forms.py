from django import forms
from .transport_models import BusApplication, Bus, BoardingPoint


class BusApplicationForm(forms.ModelForm):
    class Meta:
        model = BusApplication
        fields = ['name', 'register_no', 'mobile_number', 'route', 'bus', 'boarding_point']

    def clean(self):
        cleaned = super().clean()
        bus = cleaned.get('bus')
        bp = cleaned.get('boarding_point')
        if bus and bp and bp.bus_id != bus.id:
            raise forms.ValidationError('Selected boarding point does not belong to the selected bus.')
        return cleaned
