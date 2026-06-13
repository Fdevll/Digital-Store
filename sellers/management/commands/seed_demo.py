"""Заполняет базу демонстрационными данными для защиты:
два магазина-продавца, привязка товаров, оплаченные заказы за последние месяцы
и пример обращения в поддержку. Команду можно запускать повторно —
прежние демо-данные пересоздаются.

    python manage.py seed_demo
"""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone

from products.models import Product
from sellers.models import Seller
from orders.models import Order, OrderItem, Download
from support.models import SupportTicket

DEMO_PASSWORD = 'demo12345'

SELLERS = [
    {
        'username': 'demo_coder',
        'shop_name': 'Кодер Маркет',
        'description': 'Курсы и книги по программированию.',
        'categories': ['Курсы', 'Электронные книги'],
    },
    {
        'username': 'demo_pixel',
        'shop_name': 'Пиксель Стор',
        'description': 'Графика и готовые шаблоны для сайтов.',
        'categories': ['Графика', 'Шаблоны'],
    },
]


class Command(BaseCommand):
    help = 'Заполняет базу демо-данными (продавцы, продажи, поддержка).'

    @transaction.atomic
    def handle(self, *args, **options):
        self._cleanup()

        buyer = self._make_user('demo_buyer', email='buyer@example.com')

        sellers = []
        for cfg in SELLERS:
            user = self._make_user(cfg['username'], email=f"{cfg['username']}@example.com")
            seller = Seller.objects.create(
                user=user, shop_name=cfg['shop_name'], description=cfg['description'],
            )
            # Привязываем товары нужных категорий, ещё не занятые другим продавцом
            products = Product.objects.filter(
                category__name__in=cfg['categories'], seller__isnull=True,
            )
            products.update(seller=seller)
            sellers.append(seller)
            self.stdout.write(f'Магазин «{seller.shop_name}»: товаров {seller.products.count()}')

        self._make_sales(buyer, sellers)
        self._make_ticket(buyer)

        self.stdout.write(self.style.SUCCESS(
            f'Готово. Демо-продавцы: demo_coder / demo_pixel, покупатель: demo_buyer. '
            f'Пароль у всех: {DEMO_PASSWORD}'
        ))

    def _cleanup(self):
        """Удаляет данные предыдущего запуска, освобождая товары."""
        demo_users = User.objects.filter(
            username__in=['demo_coder', 'demo_pixel', 'demo_buyer']
        )
        Product.objects.filter(seller__user__in=demo_users).update(seller=None)
        # Заказы и обращения демо-покупателя удалятся каскадно вместе с пользователем
        demo_users.delete()

    def _make_user(self, username, email):
        user = User.objects.create_user(username, email, DEMO_PASSWORD)
        return user

    def _make_sales(self, buyer, sellers):
        """Создаёт оплаченные заказы за последние 6 месяцев для наглядного графика."""
        products = list(Product.objects.filter(seller__in=sellers))
        if not products:
            return
        now = timezone.now()
        # Кол-во заказов в каждом месяце (от старого к текущему)
        orders_per_month = [2, 1, 3, 2, 4, 3]
        for months_ago, count in zip(range(5, -1, -1), orders_per_month):
            order_date = now - timedelta(days=months_ago * 30 + 5)
            for n in range(count):
                # В каждый заказ кладём два товара по кругу
                chosen = [
                    products[(months_ago + n) % len(products)],
                    products[(months_ago + n + 1) % len(products)],
                ]
                order = Order.objects.create(
                    user=buyer, total_price=0, status='paid',
                )
                total = 0
                for prod in chosen:
                    OrderItem.objects.create(
                        order=order, product=prod, price=prod.price, quantity=1,
                    )
                    Download.objects.create(
                        user=buyer, product=prod, order=order,
                        expires_at=order_date + timedelta(days=30),
                    )
                    total += prod.price
                order.total_price = total
                order.save(update_fields=['total_price'])
                # created_at — auto_now_add, поэтому проставляем дату напрямую
                Order.objects.filter(id=order.id).update(created_at=order_date)

    def _make_ticket(self, buyer):
        SupportTicket.objects.create(
            user=buyer,
            subject='Не приходит ссылка на скачивание',
            message='Оплатил заказ, но не вижу файла в личном кабинете. Подскажите, пожалуйста.',
            status='closed',
            answer='Ссылка появляется в разделе «Мои файлы» сразу после подтверждения оплаты. '
                   'Проверьте, пожалуйста, статус заказа — он должен быть «Оплачен».',
        )
