web: python manage.py migrate --settings=config.settings.production && gunicorn config.wsgi:application --env DJANGO_SETTINGS_MODULE=config.settings.production
worker: celery -A config worker -l info --settings=config.settings.production
