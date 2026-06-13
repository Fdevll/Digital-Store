from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, F, DecimalField
from django.shortcuts import render, redirect, get_object_or_404

from products.models import Product
from orders.models import OrderItem
from .forms import SellerForm, SellerProductForm
from .models import Seller


def _get_seller(user):
    return Seller.objects.filter(user=user).first()


@login_required
def become_seller(request):
    """Регистрация пользователя как продавца (создание магазина)."""
    seller = _get_seller(request.user)
    if seller:
        return redirect('seller_dashboard')

    if request.method == 'POST':
        form = SellerForm(request.POST)
        if form.is_valid():
            seller = form.save(commit=False)
            seller.user = request.user
            seller.save()
            messages.success(request, 'Магазин создан. Теперь вы можете добавлять товары.')
            return redirect('seller_dashboard')
    else:
        form = SellerForm()
    return render(request, 'sellers/become_seller.html', {'form': form})


@login_required
def seller_dashboard(request):
    seller = _get_seller(request.user)
    if not seller:
        return redirect('become_seller')

    products = seller.products.select_related('category').order_by('-created_at')

    # Выручка продавца — по оплаченным заказам
    paid_items = OrderItem.objects.filter(
        product__seller=seller, order__status='paid'
    )
    stats = paid_items.aggregate(
        revenue=Sum(F('price') * F('quantity'), output_field=DecimalField()),
        sales_count=Sum('quantity'),
    )
    return render(request, 'sellers/dashboard.html', {
        'seller': seller,
        'products': products,
        'products_count': products.count(),
        'revenue': stats['revenue'] or 0,
        'sales_count': stats['sales_count'] or 0,
    })


@login_required
def edit_shop(request):
    seller = _get_seller(request.user)
    if not seller:
        return redirect('become_seller')
    if request.method == 'POST':
        form = SellerForm(request.POST, instance=seller)
        if form.is_valid():
            form.save()
            messages.success(request, 'Данные магазина обновлены.')
            return redirect('seller_dashboard')
    else:
        form = SellerForm(instance=seller)
    return render(request, 'sellers/edit_shop.html', {'form': form, 'seller': seller})


@login_required
def product_create(request):
    seller = _get_seller(request.user)
    if not seller:
        return redirect('become_seller')
    if request.method == 'POST':
        form = SellerProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.seller = seller
            product.save()
            messages.success(request, 'Товар добавлен.')
            return redirect('seller_dashboard')
    else:
        form = SellerProductForm()
    return render(request, 'sellers/product_form.html', {'form': form, 'title': 'Новый товар'})


@login_required
def product_edit(request, pk):
    seller = _get_seller(request.user)
    if not seller:
        return redirect('become_seller')
    product = get_object_or_404(Product, pk=pk, seller=seller)
    if request.method == 'POST':
        form = SellerProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Товар обновлён.')
            return redirect('seller_dashboard')
    else:
        form = SellerProductForm(instance=product)
    return render(request, 'sellers/product_form.html', {
        'form': form, 'title': 'Редактирование товара', 'product': product,
    })


@login_required
def product_delete(request, pk):
    seller = _get_seller(request.user)
    if not seller:
        return redirect('become_seller')
    product = get_object_or_404(Product, pk=pk, seller=seller)
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Товар удалён.')
        return redirect('seller_dashboard')
    return render(request, 'sellers/product_confirm_delete.html', {'product': product})


@login_required
def seller_sales(request):
    seller = _get_seller(request.user)
    if not seller:
        return redirect('become_seller')
    items = OrderItem.objects.filter(
        product__seller=seller, order__status='paid'
    ).select_related('product', 'order', 'order__user').order_by('-order__created_at')
    total = items.aggregate(
        revenue=Sum(F('price') * F('quantity'), output_field=DecimalField())
    )['revenue'] or 0
    return render(request, 'sellers/sales.html', {
        'seller': seller, 'items': items, 'total': total,
    })


def seller_shop(request, slug):
    """Публичная витрина магазина продавца."""
    seller = get_object_or_404(Seller, slug=slug, is_active=True)
    products = seller.products.filter(is_active=True).select_related('category')
    return render(request, 'sellers/shop.html', {'seller': seller, 'products': products})
