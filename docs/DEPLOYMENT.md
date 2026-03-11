# Guide de Déploiement - Gestion Locative Backend

## 🚀 Déploiement sur Render.com

### Prérequis
- Compte Render.com
- Repository Git (GitHub, GitLab)
- Base de données PostgreSQL

### Étapes

#### 1. Créer la base de données PostgreSQL

1. Sur Render.com → New → PostgreSQL
2. Nom: `gestion-locative-db`
3. Plan: Free ou Starter
4. Créer la base
5. Noter les informations de connexion

#### 2. Créer le Web Service

1. Sur Render.com → New → Web Service
2. Connecter le repository Git
3. Configuration:
   - **Name**: gestion-locative-backend
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements/production.txt`
   - **Start Command**: `gunicorn config.wsgi:application`
   - **Plan**: Free ou Starter

#### 3. Variables d'environnement

Ajouter dans Render Dashboard → Environment:

```
SECRET_KEY=votre-cle-secrete-tres-longue-et-aleatoire
DJANGO_SETTINGS_MODULE=config.settings.production
DEBUG=False

DB_NAME=<depuis Render PostgreSQL>
DB_USER=<depuis Render PostgreSQL>
DB_PASSWORD=<depuis Render PostgreSQL>
DB_HOST=<depuis Render PostgreSQL>
DB_PORT=5432

ALLOWED_HOSTS=votre-app.onrender.com
CORS_ALLOWED_ORIGINS=https://votre-frontend.vercel.app

CLOUDINARY_CLOUD_NAME=votre_cloud_name
CLOUDINARY_API_KEY=votre_api_key
CLOUDINARY_API_SECRET=votre_api_secret

EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=votre-email@gmail.com
EMAIL_HOST_PASSWORD=votre-app-password

FRONTEND_URL=https://votre-frontend.vercel.app
```

#### 4. Migrations et Superuser

Après le premier déploiement:

```bash
# Via Render Shell
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput
```

## 🔧 Configuration PostgreSQL Local

### Installation PostgreSQL

**Windows:**
```powershell
# Télécharger depuis postgresql.org
# Installer et définir mot de passe
```

**Mac:**
```bash
brew install postgresql@14
brew services start postgresql@14
```

**Linux:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
```

### Créer la base de données

```bash
# Se connecter à PostgreSQL
psql -U postgres

# Créer la base
CREATE DATABASE gestion_locative;
CREATE USER gestion_user WITH PASSWORD 'votre_password';
ALTER ROLE gestion_user SET client_encoding TO 'utf8';
ALTER ROLE gestion_user SET timezone TO 'Africa/Abidjan';
GRANT ALL PRIVILEGES ON DATABASE gestion_locative TO gestion_user;

# Quitter
\q
```

## 📧 Configuration Email (Gmail)

### Générer un mot de passe d'application

1. Aller sur https://myaccount.google.com/security
2. Activer "Validation en deux étapes"
3. Rechercher "Mots de passe des applications"
4. Créer un nouveau mot de passe pour "Mail"
5. Copier le mot de passe généré dans `.env`

## ☁️ Configuration Cloudinary

1. Créer un compte sur https://cloudinary.com
2. Dashboard → Account Details
3. Copier:
   - Cloud Name
   - API Key
   - API Secret
4. Ajouter dans `.env`

## 🐳 Déploiement avec Docker (Optionnel)

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements/production.txt .
RUN pip install --no-cache-dir -r production.txt

COPY . .

RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  db:
    image: postgres:14
    environment:
      POSTGRES_DB: gestion_locative
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data

  web:
    build: .
    command: gunicorn config.wsgi:application --bind 0.0.0.0:8000
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    depends_on:
      - db
    env_file:
      - .env

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  celery:
    build: .
    command: celery -A config worker -l info
    volumes:
      - .:/app
    depends_on:
      - db
      - redis
    env_file:
      - .env

volumes:
  postgres_data:
```

## 📝 Checklist de déploiement

- [ ] Base de données PostgreSQL créée
- [ ] Variables d'environnement configurées
- [ ] `SECRET_KEY` généré (différent de dev)
- [ ] `DEBUG=False` en production
- [ ] `ALLOWED_HOSTS` configuré
- [ ] Migrations appliquées
- [ ] Superuser créé
- [ ] Static files collectés
- [ ] Cloudinary configuré
- [ ] Email configuré
- [ ] CORS configuré avec URL frontend
- [ ] SSL/HTTPS activé
- [ ] Backup automatique configuré

## 🔒 Sécurité Production

### Générer une SECRET_KEY sécurisée

```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

### Headers de sécurité

Dans `settings/production.py`:
```python
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
```

## 📊 Monitoring

### Sentry (Erreurs)

```bash
pip install sentry-sdk
```

```python
# settings/production.py
import sentry_sdk

sentry_sdk.init(
    dsn="votre-sentry-dsn",
    traces_sample_rate=1.0,
)
```

## 🔄 Backup Base de données

### Backup automatique (Render)

Render PostgreSQL inclut des backups automatiques journaliers.

### Backup manuel

```bash
# Export
pg_dump -U postgres gestion_locative > backup.sql

# Import
psql -U postgres gestion_locative < backup.sql
```

## 🚨 Troubleshooting

### Erreur de migration
```bash
python manage.py migrate --fake-initial
```

### Problème static files
```bash
python manage.py collectstatic --clear --noinput
```

### Réinitialiser base de données
```bash
python manage.py flush
python manage.py migrate
python manage.py createsuperuser
```
