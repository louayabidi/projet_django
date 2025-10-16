from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", include("apps.authentication.urls")),
    path('books/', include('apps.book.urls')),          # Front-end classique
    path("", include("apps.home.urls")),
]
