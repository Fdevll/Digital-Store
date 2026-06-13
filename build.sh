#!/usr/bin/env bash
# Скрипт сборки для Render (Build Command: ./build.sh)
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
# Демо-наполнение (категории, товары с обложками, продавцы, продажи).
# Команда идемпотентна и пересоздаёт обложки, поэтому превью не пропадают
# после эфемерного сброса диска при каждом редеплое на Render.
python manage.py seed_demo
