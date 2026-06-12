import uuid

from django.conf import settings
from django.urls import reverse


def _configure_yookassa():
    try:
        from yookassa import Configuration
    except ImportError:
        return False
    if not (settings.YOOKASSA_SHOP_ID and settings.YOOKASSA_SECRET_KEY):
        return False
    Configuration.account_id = settings.YOOKASSA_SHOP_ID
    Configuration.secret_key = settings.YOOKASSA_SECRET_KEY
    return True


def create_yookassa_payment(order, request):
    """Создать платёж в ЮKassa и вернуть URL страницы оплаты."""
    if not _configure_yookassa():
        return None
    from yookassa import Payment

    return_url = request.build_absolute_uri(
        reverse('payment_success', args=[order.id])
    )
    payment = Payment.create(
        {
            'amount': {'value': f'{order.total_price:.2f}', 'currency': 'RUB'},
            'confirmation': {'type': 'redirect', 'return_url': return_url},
            'capture': True,
            'description': f'Заказ №{order.id}',
            'metadata': {'order_id': order.id},
        },
        str(uuid.uuid4()),  # ключ идемпотентности
    )
    order.payment_id = payment.id
    order.save(update_fields=['payment_id', 'updated_at'])
    return payment.confirmation.confirmation_url


def check_yookassa_payment(payment_id):
    """Проверить статус платежа напрямую через API ЮKassa."""
    if not _configure_yookassa():
        return False
    from yookassa import Payment

    try:
        payment = Payment.find_one(payment_id)
    except Exception:
        return False
    return payment.status == 'succeeded'
