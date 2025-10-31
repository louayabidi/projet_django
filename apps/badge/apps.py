from django.apps import AppConfig

class BadgeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.badge'
    
    def ready(self):
        import apps.badge.signals  