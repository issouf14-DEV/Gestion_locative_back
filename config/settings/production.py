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
# Replace 'votre-frontend.onrender.com' with the actual production frontend URL,
# or set CORS_ALLOWED_ORIGINS env variable to a comma-separated list of origins.
_cors_origins_default = 'https://votre-frontend.onrender.com'
_cors_origins: str = config('CORS_ALLOWED_ORIGINS', default=_cors_origins_default)  # type: ignore[assignment]
CORS_ALLOWED_ORIGINS = [origin.strip() for origin in _cors_origins.split(',') if origin.strip()]
CORS_ALLOW_CREDENTIALS = True

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
