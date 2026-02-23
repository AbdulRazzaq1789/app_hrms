from django import forms
from .models import LeaveEntry

class YourModelForm(forms.ModelForm):
    class Meta:
        model = LeaveEntry
        fields = '__all__'
        widgets = {
            'date_from': forms.DateField(attrs={'autocomplete': 'off'}),
   
        }