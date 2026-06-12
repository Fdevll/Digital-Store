import datetime
import json

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.conf import settings
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from orders.models import Order, Download
from .services import create_yookassa_payment


def _create_downloads(order):
    """Создать ссылки на скачивание для оплаченного заказа (идемпотентно)."""
    expires_at = timezone.now() + datetime.timedelta(days=settings.DOWNLOAD_LINK_DAYS)
    for item in order.items.all():
        Download.objects.get_or_create(
            user=order.user,
            product=item.product,
            order=order,
            defaults={'expires_at': expires_at},
        )


def _mark_paid(order):
    if order.status != 'paid':
        order.status = 'paid'
        order.save(update_fields=['status', 'updated_at'])
    _create_downloads(order)


@login_required
def payment_create(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user, status='pending')

    # Если настроена ЮKassa — отправляем на реальную платёжную страницу,
    # иначе работает демо-режим с подтверждением вручную
    if settings.YOOKASSA_SHOP_ID and settings.YOOKASSA_SECRET_KEY:
        confirmation_url = create_yookassa_payment(order, request)
        if confirmation_url:
            return redirect(confirmation_url)

    return render(request, 'payments/payment.html', {'order': order})


@login_required
@require_POST
def payment_confirm(request, order_id):
    """Подтверждение оплаты в демо-режиме (без платёжной системы)."""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    _mark_paid(order)
    return redirect('payment_success', order_id=order.id)


@login_required
def payment_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if order.status != 'paid':
        # Возврат с платёжной страницы ЮKassa: статус подтверждает webhook,
        # но на случай его задержки проверяем платёж напрямую
        from .services import check_yookassa_payment
        if order.payment_id and check_yookassa_payment(order.payment_id):
            _mark_paid(order)
        else:
            return render(request, 'payments/payment_pending.html', {'order': order})
    return render(request, 'payments/payment_success.html', {'order': order})


@login_required
def payment_fail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'payments/payment_fail.html', {'order': order})


@csrf_exempt
def payment_webhook(request):
    """Уведомления ЮKassa об изменении статуса платежа."""
    if request.method != 'POST':
        return HttpResponse(status=405)
    try:
        data = json.loads(request.body)
        obj = data.get('object', {})
        payment_id = obj.get('id')
        status = obj.get('status')
        if payment_id and status == 'succeeded':
            order = Order.objects.filter(payment_id=payment_id).first()
            if order:
                _mark_paid(order)
        elif payment_id and status == 'canceled':
            Order.objects.filter(payment_id=payment_id, status='pending').update(status='cancelled')
    except (json.JSONDecodeError, KeyError):
        return HttpResponse(status=400)
    return HttpResponse(status=200)
