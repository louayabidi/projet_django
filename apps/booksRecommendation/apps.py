from django.apps import AppConfig

class BooksRecommendationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.booksRecommendation'  # <-- correspond à INSTALLED_APPS
