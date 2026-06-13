"""Заполняет базу демонстрационными данными для защиты:
категории, демо-товары, два магазина-продавца, оплаченные заказы за последние
месяцы и пример обращения в поддержку. Команда самодостаточна и идемпотентна —
прежние демо-данные пересоздаются, поэтому её можно запускать повторно
(в том числе вешать в Start Command на Render).

    python manage.py seed_demo
"""
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone

from products.models import Product, Category
from sellers.models import Seller
from orders.models import Order, OrderItem, Download
from support.models import SupportTicket

DEMO_PASSWORD = 'demo12345'

# Демо-товары помечаем фиксированными slug с префиксом, чтобы при повторном
# запуске находить и удалять именно их, не задевая реальные товары.
DEMO_SLUG_PREFIX = 'demo-'

CATEGORIES = [
    ('Курсы', 'Онлайн-курсы и видеоуроки.'),
    ('Электронные книги', 'Книги и руководства в электронном виде.'),
    ('Графика', 'Иконки, пресеты и графические наборы.'),
    ('Шаблоны', 'Готовые шаблоны для сайтов.'),
]

# (slug, title, category, price, description)
PRODUCTS = [
    ('demo-python-course', 'Python с нуля до профи', 'Курсы', '4990.00',
     'Полный видеокурс по Python: синтаксис, ООП, работа с базами данных и практические проекты.'),
    ('demo-django-course', 'Django: создание веб-приложений', 'Курсы', '5990.00',
     'Пошаговый курс по разработке сайтов на Django с развёртыванием на сервере.'),
    ('demo-clean-code-book', 'Чистый код на практике', 'Электронные книги', '1290.00',
     'Электронная книга о принципах написания понятного и поддерживаемого кода.'),
    ('demo-algorithms-book', 'Алгоритмы и структуры данных', 'Электронные книги', '1590.00',
     'Разбор классических алгоритмов с примерами на Python и задачами для самопроверки.'),
    ('demo-flat-icons', 'Набор иконок Flat UI (500 шт.)', 'Графика', '990.00',
     'Векторный набор из 500 иконок в едином плоском стиле, форматы SVG и PNG.'),
    ('demo-lightroom-presets', 'Пресеты для Lightroom «Кино»', 'Графика', '790.00',
     'Коллекция пресетов для кинематографичной цветокоррекции фотографий.'),
    ('demo-landing-startup', 'Шаблон лендинга «Startup»', 'Шаблоны', '2490.00',
     'Адаптивный одностраничный шаблон для стартапа на HTML и CSS.'),
    ('demo-shop-template', 'HTML-шаблон интернет-магазина', 'Шаблоны', '3490.00',
     'Готовый адаптивный шаблон витрины интернет-магазина с карточками товаров и корзиной.'),
]

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
    help = 'Заполняет базу демо-данными (категории, товары, продавцы, продажи, поддержка).'

    @transaction.atomic
    def handle(self, *args, **options):
        self._cleanup()

        self._make_categories()
        self._make_products()

        buyer = self._make_user('demo_buyer', email='buyer@example.com')

        sellers = []
        for cfg in SELLERS:
            user = self._make_user(cfg['username'], email=f"{cfg['username']}@example.com")
            seller = Seller.objects.create(
                user=user, shop_name=cfg['shop_name'], description=cfg['description'],
            )
            # Привязываем демо-товары нужных категорий, ещё не занятые продавцом
            products = Product.objects.filter(
                slug__startswith=DEMO_SLUG_PREFIX,
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
        """Удаляет данные предыдущего запуска: демо-товары, продавцов и покупателя."""
        demo_users = User.objects.filter(
            username__in=['demo_coder', 'demo_pixel', 'demo_buyer']
        )
        # Заказы, OrderItem, Download и обращения демо-покупателя удалятся каскадно
        demo_users.delete()
        # Сами демо-товары (их seller обнулился при удалении продавцов)
        Product.objects.filter(slug__startswith=DEMO_SLUG_PREFIX).delete()

    def _make_categories(self):
        for name, description in CATEGORIES:
            Category.objects.get_or_create(
                name=name,
                defaults={'slug': self._slugify(name), 'description': description},
            )

    def _make_products(self):
        for slug, title, category_name, price, description in PRODUCTS:
            category = Category.objects.get(name=category_name)
            # slug задаём явно, чтобы save() не генерировал новый и cleanup их находил
            Product.objects.create(
                slug=slug, title=title, description=description,
                price=Decimal(price), category=category, is_active=True,
            )

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

    @staticmethod
    def _slugify(name):
        from products.models import transliterate_cyrillic
        from django.utils.text import slugify
        return slugify(transliterate_cyrillic(name))
