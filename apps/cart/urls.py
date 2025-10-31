from django.urls import path
from . import views

urlpatterns = [
    path('', views.cart_user_view, name='cart_user_view'),
    path('add/<int:book_id>/', views.add_to_cart, name='add_to_cart'),
    path('remove/<int:cart_item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('clear/', views.clear_cart, name='clear_cart'),
]