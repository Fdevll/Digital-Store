#!/usr/bin/env bash
# Скрипт сборки для Render (Build Command: ./build.sh)
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
