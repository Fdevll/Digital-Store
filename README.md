# DigitalStore

Интернет-магазин цифровых товаров на Django.

## Запуск проекта

1. Создайте виртуальное окружение:
   ```
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   .venv\Scripts\activate  # Windows
   ```

2. Установите зависимости:
   ```
   pip install -r requirements.txt
   ```

3. Создайте файл `.env` на основе `.env.example` и заполните его.

4. Выполните миграции:
   ```
   python manage.py migrate
   ```

5. Создайте суперпользователя:
   ```
   python manage.py createsuperuser
   ```

6. Запустите сервер:
   ```
   python manage.py runserver
   ```

7. Откройте http://127.0.0.1:8000 в браузере.

## Структура проекта

- `config/` — настройки Django
- `products/` — товары и категории
- `orders/` — заказы и скачивание
- `cart/` — корзина (сессии)
- `users/` — пользователи и профили
- `payments/` — оплата
- `templates/` — HTML шаблоны
- `static/` — CSS, JS, изображения
