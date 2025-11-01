from django.urls import path
from . import views

urlpatterns = [
    path('recommended/', views.recommended_books, name='recommended_books'),
    path('user/<int:user_id>/recommended/', views.get_user_recommendations, name='user_recommended_books'),
]
