from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
import datetime
from cart.cart import Cart
from .models import Order, OrderItem, Download
from products.models import Product

@login_required
def checkout(request):
    cart = Cart(request)
    if not cart:
        return redirect('cart_detail')

    if request.method == 'POST':
        order = Order.objects.create(
            user=request.user,
            total_price=cart.get_total_price(),
            status='pending'
        )
        for item in cart:
            product = Product.objects.get(id=item['product_id'])
            OrderItem.objects.create(
                order=order,
                product=product,
                price=item['price'],
                quantity=item['quantity']
            )
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
    orders = Order.objects.filter(user=request.user, status='paid')
    return render(request, 'orders/order_history.html', {'orders': orders})

@login_required
def download_file(request, token):
    dl = get_object_or_404(Download, download_token=token, user=request.user)

    if dl.is_used:
        messages.error(request, 'Ссылка уже была использована')
        return redirect('profile')

    if timezone.now() > dl.expires_at:
        messages.error(request, 'Срок действия ссылки истёк')
        return redirect('profile')

    dl.is_used = True
    dl.save()

    from django.http import FileResponse
    try:
        return FileResponse(dl.product.digital_file.open(), as_attachment=True, filename=dl.product.digital_file.name.split('/')[-1])
    except FileNotFoundError:
        messages.error(request, 'Файл не найден')
        return redirect('profile')
