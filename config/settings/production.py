"""
Configuration pour l'environnement de production
"""
from .base import *

DEBUG = False

_allowed_hosts: str = config(
    'ALLOWED_HOSTS',
    default='gestion-locative-fqax.onrender.com,.onrender.com,localhost,127.0.0.1',
)  # type: ignore[assignment]
ALLOWED_HOSTS = [host.strip() for host in _allowed_hosts.split(',') if host.strip()]

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT', default='5432'),
        'CONN_MAX_AGE': 600,
    }
}

# CORS Settings
_cors_origins: str = config('CORS_ALLOWED_ORIGINS', default='')  # type: ignore[assignment]
CORS_ALLOWED_ORIGINS = [origin.strip() for origin in _cors_origins.split(',') if origin.strip()]

# Si aucune origin configurée, autoriser toutes les origins (à ajuster en production)
if not CORS_ALLOWED_ORIGINS:
    CORS_ALLOW_ALL_ORIGINS = True
else:
    CORS_ALLOW_ALL_ORIGINS = False

CORS_ALLOW_CREDENTIALS = True

# Headers et méthodes autorisés
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

# CSRF Trusted Origins (nécessaire pour les requêtes POST depuis le frontend)
_csrf_origins: str = config('CSRF_TRUSTED_ORIGINS', default='')  # type: ignore[assignment]
CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in _csrf_origins.split(',') if origin.strip()]

# Ajouter automatiquement les origins CORS comme trusted pour CSRF
if CORS_ALLOWED_ORIGINS:
    CSRF_TRUSTED_ORIGINS.extend([
        origin for origin in CORS_ALLOWED_ORIGINS
        if origin not in CSRF_TRUSTED_ORIGINS
    ])

# Security Settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# Static files
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

# Cloudinary en production
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
