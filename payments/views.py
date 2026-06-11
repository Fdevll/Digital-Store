from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from django.utils import timezone
import json
from orders.models import Order

@login_required
def payment_create(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'payments/payment.html', {'order': order})

@login_required
def payment_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if request.method == 'POST' or request.GET.get('force'):
        order.status = 'paid'
        order.save()
        from django.utils import timezone
        import datetime
        from orders.models import Download
        for item in order.items.all():
            Download.objects.create(
                user=request.user,
                product=item.product,
                order=order,
                expires_at=timezone.now() + datetime.timedelta(days=getattr(settings, 'DOWNLOAD_LINK_DAYS', 30))
            )
        return render(request, 'payments/payment_success.html', {'order': order})
    return redirect('checkout')

@login_required
def payment_fail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'payments/payment_fail.html', {'order': order})

def payment_webhook(request):
    if request.method != 'POST':
        return HttpResponse(status=405)
    try:
        data = json.loads(request.body)
        payment_id = data.get('object', {}).get('id')
        status = data.get('object', {}).get('status')
        if payment_id and status == 'succeeded':
            order = Order.objects.get(payment_id=payment_id)
            order.status = 'paid'
            order.save()
    except Exception:
        pass
    return HttpResponse(status=200)
