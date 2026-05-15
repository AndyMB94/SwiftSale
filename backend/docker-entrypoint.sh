#!/bin/sh
set -e

echo "Waiting for database..."
python manage.py wait_for_db 2>/dev/null || sleep 3

echo "Running migrations..."
python manage.py migrate --no-input

echo "Collecting static files..."
python manage.py collectstatic --no-input --clear

echo "Starting server..."
exec daphne -b 0.0.0.0 -p 8000 config.asgi:application
