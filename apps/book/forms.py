from django import forms
from .models import Book

class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['title', 'synopsis', 'genre', 'status' , 'file']
        widgets = {
            'synopsis': forms.Textarea(attrs={'rows': 5}),
        }
