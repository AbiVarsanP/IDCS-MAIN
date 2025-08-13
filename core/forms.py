from django import forms
from .models import Bonafide

class BonafideForm(forms.ModelForm):
    class Meta:
        model = Bonafide
        fields = ['purpose', 'start', 'end', 'proof']
        widgets = {
            'purpose': forms.Textarea(attrs={'rows': 4}),
            'start': forms.DateInput(attrs={'type': 'date'}),
            'end': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['proof'].widget.attrs.update({'accept': 'application/pdf,image/*'})
