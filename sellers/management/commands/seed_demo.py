"""Заполняет базу демонстрационными данными для защиты:
категории, демо-товары (с реальными обложками и файлами из репозитория),
два магазина-продавца, оплаченные заказы за последние месяцы и пример обращения
в поддержку. Команда самодостаточна и идемпотентна — прежние демо-данные
пересоздаются, поэтому её можно запускать повторно (в том числе в Build/Start
Command на Render, где диск эфемерный и media пересобирается при каждом деплое).

    python manage.py seed_demo
"""
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone

from products.models import Product, Category
from sellers.models import Seller
from orders.models import Order, OrderItem, Download
from support.models import SupportTicket

DEMO_PASSWORD = 'demo12345'

# Обложки и файлы товаров хранятся в репозитории, чтобы переживать эфемерный
# сброс media на Render: при seed они копируются в MEDIA_ROOT.
DEMO_ASSETS_DIR = settings.BASE_DIR / 'assets' / 'demo'

CATEGORIES = [
    ('Курсы', 'Онлайн-курсы и видеоуроки.'),
    ('Электронные книги', 'Книги и руководства в электронном виде.'),
    ('Графика', 'Иконки, пресеты и графические наборы.'),
    ('Шаблоны', 'Готовые шаблоны для сайтов.'),
]

# (slug, title, category, price, image, file, description)
# image/file — имена в assets/demo/previews и assets/demo/files
PRODUCTS = [
    ('nabor-ikonok-dlya-interfeysa', 'Набор иконок для интерфейса', 'Графика', '490.00',
     'nabor-ikonok-dlya-interfeysa.jpg', 'icons-pack.zip',
     'Более 200 иконок в формате PNG: навигация, действия, статусы. Единый стиль линий, '
     'прозрачный фон, размер 128 пикселей. Подходит для веб-приложений и презентаций.'),
    ('django', 'Курс по Django для начинающих', 'Курсы', '2490.00',
     'django.jpg', 'django-course.zip',
     'Полный видеокурс по разработке на Django. 20 часов материала: модели, представления, '
     'шаблоны, формы, авторизация и деплой готового проекта на сервер.'),
    ('startup', 'Шаблон лендинга Startup', 'Шаблоны', '1200.00',
     'startup.jpg', 'landing-startup.zip',
     'Современный шаблон лендинга на HTML и CSS: hero-блок, преимущества, контакты. '
     'Адаптивная вёрстка, без зависимостей — просто откройте index.html и замените тексты.'),
    ('python', 'Электронная книга Python для всех', 'Электронные книги', '590.00',
     'python.jpg', 'python-dlya-vseh.pdf',
     'Подробное руководство по Python для новичков: от установки до первых проектов. '
     'Понятные примеры, упражнения после каждой главы. PDF, 300 страниц.'),
    ('videokurs-po-javascript-s-nulya', 'Видеокурс по JavaScript с нуля', 'Курсы', '1990.00',
     'videokurs-po-javascript-s-nulya.jpg', 'javascript-course.zip',
     'Современный JavaScript для новичков: синтаксис, работа с DOM, события, асинхронность '
     'и итоговый проект — интерактивное веб-приложение без фреймворков.'),
    ('python-dlya-analiza-dannyh', 'Python для анализа данных', 'Курсы', '2890.00',
     'python-dlya-analiza-dannyh.jpg', 'python-data-course.zip',
     'Практический курс: pandas, NumPy и matplotlib. Учимся загружать, чистить и '
     'визуализировать данные, строим отчёты на реальных датасетах.'),
    ('chistyy-kod-na-praktike', 'Чистый код на практике', 'Электронные книги', '790.00',
     'chistyy-kod-na-praktike.jpg', 'chistyj-kod.pdf',
     'Как писать понятный и поддерживаемый код: именование, функции, комментарии, '
     'рефакторинг. Примеры «до и после» на Python и JavaScript. PDF, 180 страниц.'),
    ('osnovy-sql-i-baz-dannyh', 'Основы SQL и баз данных', 'Электронные книги', '650.00',
     'osnovy-sql-i-baz-dannyh.jpg', 'osnovy-sql.pdf',
     'Реляционные базы данных простым языком: SELECT, JOIN, группировки, индексы и '
     'проектирование схемы. Все примеры можно выполнять в бесплатной SQLite. PDF, 220 страниц.'),
    ('kollektsiya-fonov-dlya-prezentatsiy', 'Коллекция фонов для презентаций', 'Графика', '390.00',
     'kollektsiya-fonov-dlya-prezentatsiy.jpg', 'backgrounds.zip',
     'Набор градиентных фонов в разрешении 1280×720 для слайдов, обложек и баннеров. '
     'Спокойные цвета, не отвлекают от содержания.'),
    ('shablon-rezyume-i-portfolio', 'Шаблон резюме и портфолио', 'Шаблоны', '350.00',
     'shablon-rezyume-i-portfolio.jpg', 'resume-template.zip',
     'Одностраничный HTML-шаблон резюме: блоки опыта, навыков и контактов. Печатается на A4 '
     'без потери вёрстки, легко превращается в PDF через браузер.'),
]

# Все slug демо-товаров — для идемпотентной очистки прошлого запуска
DEMO_SLUGS = [p[0] for p in PRODUCTS]

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
                slug__in=DEMO_SLUGS,
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
        """Удаляет данные предыдущего запуска: демо-товары, продавцов, покупателя и их файлы."""
        demo_users = User.objects.filter(
            username__in=['demo_coder', 'demo_pixel', 'demo_buyer']
        )
        # Заказы, OrderItem, Download и обращения демо-покупателя удалятся каскадно
        demo_users.delete()
        # Демо-товары (текущие и из прежних версий команды с префиксом demo-)
        Product.objects.filter(slug__in=DEMO_SLUGS).delete()
        Product.objects.filter(slug__startswith='demo-').delete()
        # Их файлы в media, чтобы при повторном запуске не плодились копии
        previews = settings.MEDIA_ROOT / 'products' / 'previews'
        files = settings.MEDIA_ROOT / 'products' / 'files'
        for slug in DEMO_SLUGS:
            for directory in (previews, files):
                if directory.exists():
                    for old in directory.glob(f'{slug}.*'):
                        old.unlink()
        if previews.exists():
            for old in previews.glob('demo-*.png'):
                old.unlink()

    def _make_categories(self):
        for name, description in CATEGORIES:
            Category.objects.get_or_create(
                name=name,
                defaults={'slug': self._slugify(name), 'description': description},
            )

    def _make_products(self):
        for slug, title, category_name, price, image, file_name, description in PRODUCTS:
            category = Category.objects.get(name=category_name)
            # slug задаём явно, чтобы save() не генерировал новый и cleanup их находил
            product = Product.objects.create(
                slug=slug, title=title, description=description,
                price=Decimal(price), category=category, is_active=True,
            )
            # Обложка и файл копируются из репозитория в media под именем по slug
            self._attach_file(product.preview_image, DEMO_ASSETS_DIR / 'previews' / image,
                              f'{slug}{Path(image).suffix}')
            self._attach_file(product.digital_file, DEMO_ASSETS_DIR / 'files' / file_name,
                              f'{slug}{Path(file_name).suffix}')
            product.save()

    @staticmethod
    def _attach_file(field, source_path, dest_name):
        """Копирует файл из assets в media-поле (если исходник на месте)."""
        if not source_path.exists():
            return
        with open(source_path, 'rb') as src:
            field.save(dest_name, ContentFile(src.read()), save=False)

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
