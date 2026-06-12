from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.http import FileResponse
from django.utils import timezone

from cart.cart import Cart
from .models import Order, OrderItem, Download


@login_required
def checkout(request):
    cart = Cart(request)
    if not cart:
        return redirect('cart_detail')

    if request.method == 'POST':
        with transaction.atomic():
            order = Order.objects.create(
                user=request.user,
                total_price=cart.get_total_price(),
                status='pending',
            )
            OrderItem.objects.bulk_create([
                OrderItem(
                    order=order,
                    product=item['product'],
                    price=item['price'],
                    quantity=item['quantity'],
                )
                for item in cart
            ])
        cart.clear()
        return redirect('payment_create', order_id=order.id)

    return render(request, 'orders/checkout.html', {'cart': cart})


@login_required
def order_complete(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if order.status == 'paid':
        downloads = Download.objects.filter(order=order)
        return render(request, 'orders/order_complete.html', {'order': order, 'downloads': downloads})
    return redirect('cart_detail')


@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).exclude(status='pending').prefetch_related('items__product')
    return render(request, 'orders/order_history.html', {'orders': orders})


@login_required
def download_file(request, token):
    dl = get_object_or_404(Download, download_token=token, user=request.user)

    if timezone.now() > dl.expires_at:
        messages.error(request, 'Срок действия ссылки истёк.')
        return redirect('profile')

    if not dl.product.digital_file:
        messages.error(request, 'Файл для этого товара ещё не загружен.')
        return redirect('profile')

    if not dl.is_used:
        dl.is_used = True
        dl.save(update_fields=['is_used'])

    try:
        return FileResponse(
            dl.product.digital_file.open('rb'),
            as_attachment=True,
            filename=dl.product.digital_file.name.rsplit('/', 1)[-1],
        )
    except FileNotFoundError:
        messages.error(request, 'Файл не найден на сервере.')
        return redirect('profile')
