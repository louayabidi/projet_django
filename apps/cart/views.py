from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from apps.cart.models import Cart, CartItem

@login_required(login_url="/login/")
def cart_user_view(request):
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
    cart_items = CartItem.objects.filter(cart__user=request.user)
    if not cart_items.exists():
        return redirect('cart_user_view')

    # Simuler le paiement
    cart_items.delete()

    return render(request, 'cart/checkout_success.html')
