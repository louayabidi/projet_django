from django.db import models
from django.conf import settings
from apps.book.models import Book

class UserInteraction(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    viewed = models.BooleanField(default=False)
    favorited = models.BooleanField(default=False)
    added_to_cart = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'book')  # un enregistrement par utilisateur/livre

    def __str__(self):
        return f"{self.user.username} - {self.book.title}"
