# Guide de Déploiement - Gestion Locative Backend

## 🚀 Déploiement sur Render.com (Blueprint)

Le fichier `render.yaml` décrit toute l'infrastructure : le service web (Gunicorn), la base PostgreSQL et les variables d'environnement. `build.sh` installe les dépendances, lance `collectstatic` et `migrate`, et crée l'admin si les variables sont présentes.

### Étapes

1. Sur Render : **New > Blueprint**, puis choisir le dépôt GitHub et la branche `main`.
2. Render crée `gestion-locative-api` et `gestion-locative-db`. `SECRET_KEY` est générée automatiquement et `DATABASE_URL` est liée à la base.
3. Renseigner les variables marquées `sync: false` :

| Variable | Obligatoire | Exemple |
|---|---|---|
| `CORS_ALLOWED_ORIGINS` | oui (frontend) | `https://mon-front.vercel.app` |
| `DJANGO_SUPERUSER_EMAIL` / `DJANGO_SUPERUSER_PASSWORD` | au premier déploiement | mot de passe de 12 caractères minimum |
| `CLOUDINARY_CLOUD_NAME` / `_API_KEY` / `_API_SECRET` | pour les images | sinon, stockage disque éphémère |
| `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` | pour les emails | mot de passe d'application Gmail |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | connexion Google | |
| `ALLOWED_HOSTS` | non | domaine personnalisé (le domaine `*.onrender.com` est ajouté automatiquement) |
| `SENTRY_DSN` | non | |

4. Déployer, puis vérifier : `https://<service>.onrender.com/health/` doit renvoyer `{"status": "ok"}`, et la documentation est sur `/api/docs/`.

### Garder le service éveillé

Sur le plan gratuit, Render endort le service après 15 minutes sans requête, et le réveil prend environ 1 minute. Le workflow `.github/workflows/keep-alive.yml` appelle `/health/` toutes les 10 minutes.

1. Sur GitHub : **Settings > Secrets and variables > Actions > Variables > New repository variable**, avec `RENDER_URL` = `https://<service>.onrender.com` (sans `/` à la fin).
2. Onglet **Actions** > « Garder Render éveillé » > **Run workflow**, pour tester.

Remarque : GitHub désactive les workflows planifiés après 60 jours sans commit sur le dépôt. Il suffit alors de les réactiver dans l'onglet Actions.

### Notes

- **Celery** : le plan gratuit n'a pas de worker. Sans `REDIS_URL`, les tâches s'exécutent directement. Pour un vrai worker, créer un Key Value Render et un Background Worker (`celery -A config worker -l info`), puis lier `REDIS_URL` (voir la partie en commentaire dans `render.yaml`).
- **Sécurité** : la production refuse de démarrer sans `SECRET_KEY` forte ou sans `DATABASE_URL`. Aucune origine localhost n'est acceptée et CORS n'est jamais ouvert à tous.
- La base gratuite Render expire au bout de 30 jours : pensez à faire une sauvegarde (voir plus bas).

## 🔧 Configuration PostgreSQL Local

### Alternatives PostgreSQL Gratuites (si limite Render atteinte)

**Neon.tech** (Recommandé)
- 10 projets gratuits par compte
- 3 GB de stockage par base
- Inscription: https://neon.tech
- Après création, copiez l'URL de connexion et utilisez-la dans `DATABASE_URL`

**Supabase**
- 2 projets gratuits
- 500 MB par base
- Inscription: https://supabase.com

**ElephantSQL**
- Plan gratuit: 20 MB
- Inscription: https://www.elephantsql.com

### Installation PostgreSQL Local

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

### Erreur: "cannot have more than one active free tier database"
Render ne permet qu'une seule base PostgreSQL gratuite par compte. Solutions:
1. **Réutiliser la base existante**: Créez une nouvelle base dans votre PostgreSQL existant (voir Option B ci-dessus)
2. **Service externe gratuit**: Utilisez Neon.tech, Supabase, ou ElephantSQL
3. **Payer Render**: Passez au plan Starter ($7/mois) pour plusieurs bases

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
