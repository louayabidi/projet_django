from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.urls import reverse
import stripe
from apps.book.models import Book
from apps.cart.models import Cart, CartItem, Order, OrderItem, UserLibrary
from apps.booksRecommendation.models import UserInteraction
from core import settings
stripe.api_key = settings.STRIPE_SECRET_KEY
@login_required(login_url="/login/")
def cart_user_view(request):
    print("stripe key:", settings.STRIPE_SECRET_KEY)
    user = request.user
    try:
        cart = user.cart  # récupère le Cart lié à l'utilisateur
        cart_items = cart.items.all()
    except Cart.DoesNotExist:
        cart_items = []

    total = sum(item.book.price for item in cart_items)

    context = {
        'cart_items': cart_items,
        'total': total,
    }
    return render(request, 'cart/user_cart.html', context)


@login_required(login_url="/login/")
def add_to_cart(request, book_id):
    user_cart, _ = Cart.objects.get_or_create(user=request.user)
    cart_item, _ = CartItem.objects.get_or_create(cart=user_cart, book_id=book_id)
    book = Book.objects.get(id=book_id)
    interaction, _ = UserInteraction.objects.get_or_create(user=request.user, book=book)
    interaction.added_to_cart = True
    interaction.save()
    return redirect('cart_user_view')


@login_required(login_url="/login/")
def remove_from_cart(request, cart_item_id):
    try:
        cart_item = CartItem.objects.get(id=cart_item_id, cart__user=request.user)
        cart_item.delete()
    except CartItem.DoesNotExist:
        pass
    return redirect('cart_user_view')


@login_required(login_url="/login/")
def clear_cart(request):
    CartItem.objects.filter(cart__user=request.user).delete()
    return redirect('cart_user_view')


@login_required(login_url="/login/")
def checkout(request):
    stripe.api_key = settings.STRIPE_SECRET_KEY
    print("stripe key in checkout:", settings.STRIPE_SECRET_KEY)
    cart_items = CartItem.objects.filter(cart__user=request.user)
    if not cart_items.exists():
        return redirect('cart_user_view')

    # Créer des line items pour Stripe
    line_items = []
    for item in cart_items:
        line_items.append({
            'price_data': {
                'currency': 'eur',
                'product_data': {
                    'name': item.book.title,
                },
                'unit_amount': int(item.book.price * 100),  # prix en centimes
            },
            'quantity': 1,
        })

    # Créer la session Stripe Checkout
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=line_items,
        mode='payment',
        success_url=request.build_absolute_uri(reverse('checkout_success')),
        cancel_url=request.build_absolute_uri(reverse('cart_user_view')),
    )

    return redirect(session.url, code=303)
@login_required(login_url="/login/")
@login_required(login_url="/login/")
def checkout_success(request):
    cart_items = CartItem.objects.filter(cart__user=request.user)
    if not cart_items.exists():
        return redirect('cart_user_view')

    total = sum(item.book.price for item in cart_items)

    # Créer l'Order
    order = Order.objects.create(user=request.user, total_amount=total)

    # Ajouter les livres achetés à OrderItem
    for item in cart_items:
        OrderItem.objects.create(
            order=order,
            book=item.book,
            price=item.book.price
        )
        UserLibrary.objects.get_or_create(user=request.user, book=item.book)

    # Supprimer les items du panier
    cart_items.delete()

    return render(request, 'cart/checkout_success.html', {'order': order})

