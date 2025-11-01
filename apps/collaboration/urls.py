from django.urls import path
from . import views

urlpatterns = [
    # Pages principales utilisateur
    path('', views.collaborations_list, name='collaborations_list'),
    path('create/', views.create_collaboration_post, name='create_collaboration_post'),
    path('<int:post_id>/', views.collaboration_detail, name='collaboration_detail'),
    path('update/<int:post_id>/', views.update_collaboration_post, name='update_collaboration_post'),
    path('delete/<int:post_id>/', views.delete_collaboration_post, name='delete_collaboration_post'),
    
    # Réponses
    path('<int:post_id>/responses/', views.responses_list, name='responses_list'),
    path('<int:post_id>/respond/', views.respond_to_collaboration, name='respond_to_collaboration'),
    path('response/<int:response_id>/update/', views.update_response, name='update_response'),
    path('response/<int:response_id>/delete/', views.delete_response, name='delete_response'),
    path('response/<int:response_id>/status/<str:status>/', views.update_response_status, name='update_response_status'),
    
    # Admin
    path('admin-collaboration/', views.admin_collaborations, name='admin_collaborations'),
    path('admin-collaboration/<int:post_id>/responses/', views.admin_collaboration_responses, name='admin_collaboration_responses'),
]