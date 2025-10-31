from django.urls import path
from . import views

app_name = 'badge'

urlpatterns = [
    path('', views.badge_list, name='badge_list'),
     path('your-badges/', views.your_badges, name='your_badges'),
    path('create/', views.badge_create, name='badge_create'),
    path('<int:pk>/', views.badge_detail, name='badge_detail'),
    path('<int:pk>/update/', views.badge_update, name='badge_update'),
    path('<int:pk>/delete/', views.badge_delete, name='badge_delete'),
]