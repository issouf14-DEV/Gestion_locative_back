#!/usr/bin/env bash
# Script de build exécuté par Render à chaque déploiement
set -o errexit

pip install --upgrade pip
pip install -r requirements/production.txt

python manage.py collectstatic --noinput
python manage.py migrate --noinput

# Crée l'admin seulement si DJANGO_SUPERUSER_EMAIL et DJANGO_SUPERUSER_PASSWORD sont définis
if [ -n "$DJANGO_SUPERUSER_EMAIL" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
  python manage.py create_superuser
fi

# Données de démonstration : SEED_DEMO=creer pour les ajouter, SEED_DEMO=supprimer pour les retirer
if [ "$SEED_DEMO" = "creer" ]; then
  python manage.py seed_demo
elif [ "$SEED_DEMO" = "supprimer" ]; then
  python manage.py seed_demo --supprimer
fi
