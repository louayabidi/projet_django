from django.db import models
from django.conf import settings
from django.core.validators import FileExtensionValidator  # Nouveau

class Book(models.Model):
    title = models.CharField(max_length=200)
    synopsis = models.TextField()
    genre = models.CharField(max_length=100)
    status = models.CharField(max_length=50, choices=[
        ('en_cours', 'En cours'),
        ('termine', 'Terminé'),
        ('archive', 'Archivé')
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Lien avec l'utilisateur (auteur)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='books')

    # Fichier avec validation 
    file = models.FileField(
        upload_to='books/', 
        null=True, 
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['txt', 'pdf'])]
    )
    
    content = models.TextField(blank=True, default='')

    def __str__(self):
        return self.title