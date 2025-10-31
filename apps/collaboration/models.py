from django.db import models
from django.conf import settings
from apps.book.models import Book 

class CollaborationPost(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='collab_posts'
    )
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='collab_posts')
    title = models.CharField(max_length=200)
    content = models.TextField(help_text="Description de votre demande de collaboration")
    image = models.ImageField(upload_to='collaboration/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} par {self.author.username}"


class CollaborationResponse(models.Model):
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('accepted', 'Acceptée'),
        ('refused', 'Refusée'),
    ]
    post = models.ForeignKey(CollaborationPost, on_delete=models.CASCADE, related_name='responses')
    responder = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField(help_text="Présentez-vous et montrez votre motivation")
    pdf_file = models.FileField(upload_to='responses/pdfs/', blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Réponse de {self.responder.username} pour {self.post.title} ({self.status})"
