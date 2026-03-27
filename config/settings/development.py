"""
Configuration pour l'environnement de développement
"""
from .base import *

DEBUG = True

_allowed_hosts: str = config('ALLOWED_HOSTS', default='gestion-locative-fqax.onrender.com,localhost,127.0.0.1') # type: ignore
ALLOWED_HOSTS = _allowed_hosts.split(',')

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME', default='gestion_locative'),
        'USER': config('DB_USER', default='postgres'),
        'PASSWORD': config('DB_PASSWORD', default=''),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
        'OPTIONS': {
            'client_encoding': 'UTF8',
        },
    }
}

# CORS Settings
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
]
CORS_ALLOW_ALL_ORIGINS = True  
CORS_ALLOW_CREDENTIALS = True



# Email Backend pour développement (console)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Désactiver Cloudinary en dev si nécessaire
# DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
