from django import forms
from .transport_models import BusApplication

class BusApplicationForm(forms.ModelForm):
    class Meta:
        model = BusApplication
        fields = ['name', 'register_no', 'mobile_number', 'route', 'boarding_point']
