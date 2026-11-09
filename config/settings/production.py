"""
Configuration pour l'environnement de production (Render)
"""
import os

import dj_database_url

from .base import *  # noqa: F401,F403

DEBUG = False

# ------------------------------------------------------------------------------
# Clé secrète : obligatoire, jamais la valeur par défaut
# ------------------------------------------------------------------------------
if not SECRET_KEY or SECRET_KEY.startswith('django-insecure') or len(SECRET_KEY) < 50:
    raise RuntimeError("SECRET_KEY absente ou trop faible (50 caractères minimum).")
SIMPLE_JWT['SIGNING_KEY'] = SECRET_KEY


def _liste(nom, defaut=''):
    """Lit une variable d'environnement séparée par des virgules."""
    valeur = config(nom, default=defaut)
    return [v.strip().rstrip('/') for v in str(valeur).split(',') if v.strip()]


# ------------------------------------------------------------------------------
# Hôtes autorisés : Render fournit RENDER_EXTERNAL_HOSTNAME automatiquement
# ------------------------------------------------------------------------------
ALLOWED_HOSTS = _liste('ALLOWED_HOSTS')
_render_host = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if _render_host:
    ALLOWED_HOSTS.append(_render_host)
if not ALLOWED_HOSTS:
    raise RuntimeError("Aucun hôte autorisé : définissez ALLOWED_HOSTS.")

# ------------------------------------------------------------------------------
# Base de données (DATABASE_URL fournie par la base PostgreSQL Render)
# ------------------------------------------------------------------------------
_database_url = os.environ.get('DATABASE_URL')
if not _database_url:
    raise RuntimeError("La variable d'environnement DATABASE_URL est manquante.")

DATABASES = {
    'default': dj_database_url.parse(
        _database_url,
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# ------------------------------------------------------------------------------
# CORS / CSRF : uniquement les origines déclarées (aucun localhost en production)
# ------------------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = _liste('CORS_ALLOWED_ORIGINS')
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOW_CREDENTIALS = True
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
CORS_ALLOW_METHODS = ['DELETE', 'GET', 'OPTIONS', 'PATCH', 'POST', 'PUT']

CSRF_TRUSTED_ORIGINS = _liste('CSRF_TRUSTED_ORIGINS')
if _render_host:
    CSRF_TRUSTED_ORIGINS.append(f'https://{_render_host}')
CSRF_TRUSTED_ORIGINS += [o for o in CORS_ALLOWED_ORIGINS if o not in CSRF_TRUSTED_ORIGINS]

# ------------------------------------------------------------------------------
# Sécurité HTTP
# ------------------------------------------------------------------------------
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
# Jeton CSRF en cookie (sinon une requête avec un hôte invalide provoque une erreur 500)
CSRF_USE_SESSIONS = False
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'
X_FRAME_OPTIONS = 'DENY'

# ------------------------------------------------------------------------------
# Fichiers statiques (WhiteNoise) et médias (Cloudinary si configuré)
# ------------------------------------------------------------------------------
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
MIDDLEWARE.insert(0, 'config.health.HealthCheckMiddleware')

_cloudinary_ok = all(CLOUDINARY_STORAGE.values())
STORAGES = {
    'default': {
        'BACKEND': 'cloudinary_storage.storage.MediaCloudinaryStorage'
        if _cloudinary_ok else 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'},
}

# ------------------------------------------------------------------------------
# Celery : pas de worker sur le plan gratuit -> exécution directe sans Redis
# ------------------------------------------------------------------------------
if not os.environ.get('REDIS_URL'):
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = True
    CELERY_BROKER_URL = 'memory://'
    CELERY_RESULT_BACKEND = 'cache+memory://'

# ------------------------------------------------------------------------------
# Journalisation : console uniquement (le disque Render est éphémère)
# ------------------------------------------------------------------------------
LOGGING['handlers'].pop('file', None)
for _logger in LOGGING['loggers'].values():
    _logger['handlers'] = ['console']
LOGGING['loggers']['apps']['level'] = 'INFO'

# ------------------------------------------------------------------------------
# Sentry (optionnel)
# ------------------------------------------------------------------------------
_sentry_dsn = os.environ.get('SENTRY_DSN')
if _sentry_dsn:
    import sentry_sdk

    sentry_sdk.init(dsn=_sentry_dsn, traces_sample_rate=0.1, send_default_pii=False)
