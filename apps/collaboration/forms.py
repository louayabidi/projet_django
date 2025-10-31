from django import forms
from .models import CollaborationPost, CollaborationResponse 

from apps.book.models import Book

class CollaborationPostForm(forms.ModelForm):
    class Meta:
        model = CollaborationPost
        fields = ['book', 'title', 'content', 'image']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Titre de la collaboration'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 5, 
                'placeholder': 'Décrivez votre projet et vos attentes'
            }),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # récupérer l'utilisateur courant
        super().__init__(*args, **kwargs)
        if user:
            # filtrer les livres en cours uniquement
            self.fields['book'].queryset = Book.objects.filter(author=user, status='en_cours')
        else:
            self.fields['book'].queryset = Book.objects.none()


class CollaborationResponseForm(forms.ModelForm):
    class Meta:
        model = CollaborationResponse
        fields = ['message', 'pdf_file']
