from django.urls import path
from . import views, ai_views

urlpatterns = [
    path('', views.book_list, name='book_list'),          # Lire tous les livres
    path('add/', views.book_create, name='book_create'),  # Ajouter un livre
    path('<int:id>/edit/', views.book_update, name='book_update'),  # Modifier
    path('<int:id>/delete/', views.book_delete, name='book_delete'),# Supprimer
    path('<int:id>/download/', views.book_download_pdf, name='book_download_pdf'),  # Télécharger PDF
    path('<int:id>/editor/', views.book_editor, name='book_editor'),  # Éditeur de texte
    path('test/', views.test_view, name='book_test'),
    path('plagiarism-test/', views.plagiarism_test, name='plagiarism_test'),  
    path('download-examples/', views.download_example_books, name='download_example_books'),  
    
    path('api/ai/correct-grammar/', ai_views.correct_grammar, name='ai_correct_grammar'),
    path('api/ai/generate-synopsis/', ai_views.generate_synopsis, name='ai_generate_synopsis'),
    path('api/ai/analyze-sentiment/', ai_views.analyze_sentiment, name='ai_analyze_sentiment'),
    path('api/ai/extract-keywords/', ai_views.extract_keywords, name='ai_extract_keywords'),
    path('api/ai/detect-genre/', ai_views.detect_genre, name='ai_detect_genre'),
    path('api/ai/analyze-readability/', ai_views.analyze_readability, name='ai_analyze_readability'),
    path('api/ai/full-analysis/', ai_views.full_analysis, name='ai_full_analysis'),
    path('library/', views.getAllFinishedBooks, name='all_books'),
    path('favorites/add/<int:book_id>/', views.add_to_favorites, name='add_to_favorites'),
    path('favorites/remove/<int:book_id>/', views.remove_from_favorites, name='remove_favorites'),
    path('favorites/', views.view_favorites, name='view_favorites'),
    path('favorites/check/<int:book_id>/', views.check_is_favorite, name='check_favorite_status'),
    path('recommend/<int:book_id>/', views.book_detail, name='book_detail'),
    path('my-library/', views.my_library, name='my_library'),
]
