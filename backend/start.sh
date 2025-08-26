#!/usr/bin/env bash
set -e

echo "Applying database migrations..."
python manage.py migrate --noinput

if [ "${DJANGO_DEBUG}" = "True" ] || [ "${DJANGO_DEBUG}" = "true" ]; then
  echo "Starting Django dev server on 0.0.0.0:8000"
  exec python manage.py runserver 0.0.0.0:8000
else
  echo "Starting Gunicorn on 0.0.0.0:8000"
  # ajuste 'core.wsgi' para o nome do seu módulo wsgi se for diferente
  exec gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 120
fi
