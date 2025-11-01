from django import forms
from .models import Book

class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['title', 'synopsis', 'genre', 'status' , 'file','price']
        widgets = {
            'synopsis': forms.Textarea(attrs={'rows': 5}),
            'price': forms.NumberInput(attrs={'min': 0, 'step': 0.01}),
        }
