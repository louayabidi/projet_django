from django import forms
from .models import Badge

class BadgeForm(forms.ModelForm):
    class Meta:
        model = Badge
        fields = ['nom', 'description', 'image', 'badge_type', 'condition_value']
        widgets = {
            'nom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom du badge'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Description du badge',
                'rows': 4
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control'
            }),
            'badge_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'condition_value': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Valeur de condition (ex: 5 livres)'
            })
        }