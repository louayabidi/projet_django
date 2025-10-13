# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django.urls import path, re_path
from apps.home import views

urlpatterns = [

    # The home page
    path('', views.index, name='home'),
    
    # Admin book management routes
    path('admin-books/', views.admin_books_list, name='admin_books_list'),
    path('admin-books/<int:id>/', views.admin_book_detail, name='admin_book_detail'),

    # Matches any html file
    re_path(r'^.*\.html$', views.pages, name='pages'),

]
