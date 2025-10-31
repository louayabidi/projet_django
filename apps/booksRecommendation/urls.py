from django.urls import path
from . import views

urlpatterns = [
    path('recommended/', views.recommended_books, name='recommended_books'),
]
