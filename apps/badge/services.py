from django.utils import timezone
from .models import Badge, UserBadge
from apps.book.models import Book  # ✅ Ajoutez apps.

class BadgeService:
    
    @staticmethod
    def check_and_unlock_badges(user):
        """Vérifie et débloque les badges pour un utilisateur"""
        badges = Badge.objects.all()
        unlocked_badges = []
        
        for badge in badges:
            user_badge, created = UserBadge.objects.get_or_create(
                user=user, 
                badge=badge
            )
            
            if not user_badge.unlocked:
                if BadgeService._check_badge_condition(user, badge):
                    user_badge.unlocked = True
                    user_badge.unlocked_at = timezone.now()
                    user_badge.save()
                    unlocked_badges.append(badge)
        
        return unlocked_badges
    
    @staticmethod
    def _check_badge_condition(user, badge):
        """Vérifie si l'utilisateur remplit les conditions du badge"""
        
        if badge.badge_type == 'plagiat':
            # Vérifie si l'utilisateur a au moins 1 livre terminé sans plagiat
            return Book.objects.filter(
                author=user,
                status='termine',
                plagiat_web=False,
                plagiat_local=False
            ).exists()
        
        elif badge.badge_type == 'first_book':
            # Premier livre terminé
            return Book.objects.filter(
                author=user,
                status='termine'
            ).exists()
        
        elif badge.badge_type == 'completed_books':
            # Nombre de livres terminés >= condition_value
            count = Book.objects.filter(
                author=user,
                status='termine'
            ).count()
            return count >= badge.condition_value
        
        return False
    
    @staticmethod
    def initialize_user_badges(user):
        """Initialise tous les badges pour un nouvel utilisateur"""
        badges = Badge.objects.all()
        for badge in badges:
            UserBadge.objects.get_or_create(user=user, badge=badge)