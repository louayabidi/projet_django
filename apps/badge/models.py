from django.db import models
from django.conf import settings
import os

def badge_image_path(instance, filename):
    return f'badges/{instance.id}/{filename}'

class Badge(models.Model):
    BADGE_TYPES = [
        ('plagiat', 'Vérification Plagiat'),
        ('first_book', 'Premier Livre'),
        ('completed_books', 'Livres Terminés'),
        ('custom', 'Personnalisé'),
    ]
    
    nom = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to=badge_image_path, blank=True, null=True)
    badge_type = models.CharField(max_length=50, choices=BADGE_TYPES, default='custom')
    
    # Conditions pour débloquer le badge
    condition_value = models.IntegerField(default=0, help_text="Valeur requise (ex: nombre de livres)")
    
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date_creation']
    
    def __str__(self):
        return self.nom
    
    def delete(self, *args, **kwargs):
        if self.image and os.path.isfile(self.image.path):
            os.remove(self.image.path)
        super().delete(*args, **kwargs)


class UserBadge(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user_badges')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    unlocked = models.BooleanField(default=False)
    unlocked_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ('user', 'badge')
    
    def __str__(self):
        return f"{self.user.username} - {self.badge.nom} ({'Unlocked' if self.unlocked else 'Locked'})"