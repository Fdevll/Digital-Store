import json

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from products.models import Product
from .cart import Cart


def _get_quantity(request, default=1):
    """Количество из формы или из JSON-тела запроса."""
    value = request.POST.get('quantity')
    if value is None and request.content_type == 'application/json':
        try:
            value = json.loads(request.body).get('quantity')
        except (json.JSONDecodeError, AttributeError):
            value = None
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return default


def cart_detail(request):
    cart = Cart(request)
    return render(request, 'cart/cart_detail.html', {'cart': cart})


@require_POST
def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id, is_active=True)
    cart.add(product, _get_quantity(request))
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'cart_count': len(cart)})
    return redirect('cart_detail')


@require_POST
def cart_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    return redirect('cart_detail')


@require_POST
def cart_update(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.update(product, _get_quantity(request))
    return redirect('cart_detail')
