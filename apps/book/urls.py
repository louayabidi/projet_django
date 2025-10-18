from django.urls import path
from . import views

urlpatterns = [
    path('', views.book_list, name='book_list'),          # Lire tous les livres
    path('add/', views.book_create, name='book_create'),  # Ajouter un livre
    path('<int:id>/edit/', views.book_update, name='book_update'),  # Modifier
    path('<int:id>/delete/', views.book_delete, name='book_delete'),# Supprimer
    path('<int:id>/download/', views.book_download_pdf, name='book_download_pdf'),  # Télécharger PDF
    path('test/', views.test_view, name='book_test'),
    path('plagiarism-test/', views.plagiarism_test, name='plagiarism_test'),  
    path('download-examples/', views.download_example_books, name='download_example_books'),  

    path('test/', views.test_view, name='book_test'),


]
