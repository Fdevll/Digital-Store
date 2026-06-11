from django.conf import settings

def create_yookassa_payment(order, request):
    try:
        import yookassa
        yookassa.Configuration.account_id = getattr(settings, 'YOOKASSA_SHOP_ID', '')
        yookassa.Configuration.secret_key = getattr(settings, 'YOOKASSA_SECRET_KEY', '')

        payment = yookassa.Payment.create({
            "amount": {
                "value": str(order.total_price),
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": request.build_absolute_uri(f'/payments/success/{order.id}/?force=1')
            },
            "capture": True,
            "description": f'Заказ #{order.id}'
        })
        order.payment_id = payment.id
        order.save()
        return payment.confirmation.confirmation_url
    except ImportError:
        return None

def create_stripe_payment(order, request):
    try:
        import stripe
        stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', '')

        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'rub',
                    'product_data': {'name': f'Заказ #{order.id}'},
                    'unit_amount': int(order.total_price * 100),
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=request.build_absolute_uri(f'/payments/success/{order.id}/?force=1'),
            cancel_url=request.build_absolute_uri(f'/payments/fail/{order.id}/'),
        )
        order.payment_id = session.id
        order.save()
        return session.url
    except ImportError:
        return None
