from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.book.models import Book  # ✅ Ajoutez apps.
from .services import BadgeService

@receiver(post_save, sender=Book)
def check_badges_on_book_update(sender, instance, **kwargs):
    """Vérifie les badges quand un livre est mis à jour"""
    if instance.status == 'termine':
        BadgeService.check_and_unlock_badges(instance.author)