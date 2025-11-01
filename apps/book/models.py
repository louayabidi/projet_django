from django.db import models
from django.conf import settings
from django.core.validators import FileExtensionValidator  # Nouveau

class Book(models.Model):
    GENRE_CHOICES = [
        ('romance', 'Romance'),
        ('fantasy', 'Fantasy'),
        ('thriller', 'Thriller'),
        ('science_fiction', 'Science-Fiction'),
        ('aventure', 'Aventure'),
        ('horreur', 'Horreur'),
        ('drame', 'Drame'),
        ('historique', 'Historique'),
        ('poesie', 'Poésie'),
        ('biographie', 'Biographie'),
        ('developpement_personnel', 'Développement personnel'),
        ('jeunesse', 'Jeunesse'),
        ('fanfiction', 'Fanfiction'),
        ('dark_romance', 'Dark Romance'),
        ('autre', 'Autre'),
    ]
    title = models.CharField(max_length=200)
    synopsis = models.TextField()
    genre = models.CharField(max_length=100, choices=GENRE_CHOICES)
    status = models.CharField(max_length=50, choices=[
        ('en_cours', 'En cours'),
        ('termine', 'Terminé'),
        ('archive', 'Archivé')
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    plagiat_web = models.BooleanField(default=False)
    plagiat_local = models.BooleanField(default=False)
    
    # Lien avec l'utilisateur (auteur)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='books')

    collaborators = models.ManyToManyField(
        settings.AUTH_USER_MODEL, 
        related_name='collaborative_books', 
        blank=True
    )

    # Fichier avec validation 
    file = models.FileField(
        upload_to='books/', 
        null=True, 
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['txt', 'pdf'])]
    )
    
    content = models.TextField(blank=True, default='')
    price = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    favorites = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='favorite_books',
        blank=True
    )

    def __str__(self):
        return self.title