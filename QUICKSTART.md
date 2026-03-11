# 🚀 Guide de Démarrage Rapide

## Bienvenue !

Ce guide vous aidera à lancer le backend de la plateforme de gestion locative en quelques minutes.

## 📋 Prérequis

Assurez-vous d'avoir installé :
- **Python 3.11+** : https://www.python.org/downloads/
- **PostgreSQL 14+** : https://www.postgresql.org/download/
- **Git** : https://git-scm.com/downloads

## ⚡ Installation Express (5 minutes)

### 1. Cloner et naviguer

```powershell
cd C:\Users\fofan\gestion-locative-backend
```

### 2. Créer un environnement virtuel

```powershell
python -m venv venv
.\venv\Scripts\activate
```

### 3. Installer les dépendances

```powershell
pip install -r requirements\development.txt
```

### 4. Configurer PostgreSQL

Ouvrir PostgreSQL (pgAdmin ou terminal) :

```sql
CREATE DATABASE gestion_locative;
```

### 5. Configurer les variables d'environnement

Le fichier `.env` est déjà créé, modifiez juste :

```env
DB_PASSWORD=votre_mot_de_passe_postgres
```

### 6. Appliquer les migrations

```powershell
python manage.py migrate
```

### 7. Créer un superutilisateur (admin)

```powershell
python manage.py createsuperuser
```

Renseignez :
- Email : `admin@gestion-locative.com`
- Nom : `Admin`
- Prénoms : `Super`
- Téléphone : `0123456789`
- Mot de passe : (votre choix sécurisé)

### 8. Lancer le serveur

```powershell
python manage.py runserver
```

🎉 **C'est bon !** Le backend tourne sur http://localhost:8000

## 🧪 Tester l'API

### Admin Django

👉 http://localhost:8000/admin/
- Connectez-vous avec les identifiants du superuser

### Documentation API Interactive

👉 http://localhost:8000/api/docs/ (Swagger UI)
👉 http://localhost:8000/api/redoc/ (ReDoc)

### Tester avec cURL

#### Se connecter

```powershell
curl -X POST http://localhost:8000/api/auth/login/ `
  -H "Content-Type: application/json" `
  -d '{\"email\":\"admin@gestion-locative.com\",\"password\":\"votre_password\"}'
```

#### Créer une maison

```powershell
curl -X POST http://localhost:8000/api/properties/maisons/ `
  -H "Authorization: Bearer VOTRE_TOKEN_ICI" `
  -H "Content-Type: application/json" `
  -d '{\"titre\":\"Villa F4 Cocody\",\"description\":\"Belle villa moderne\",\"type_logement\":\"F4\",\"prix\":200000,\"caution\":400000,\"adresse\":\"Cocody\",\"ville\":\"Abidjan\",\"commune\":\"Cocody\",\"quartier\":\"Riviera\",\"nombre_chambres\":4,\"nombre_salles_bain\":3,\"statut\":\"DISPONIBLE\"}'
```

## 🎯 Prochaines étapes

### Option 1 : Tester avec Postman

1. Télécharger Postman : https://www.postman.com/downloads/
2. Importer la collection API (voir `docs/API.md`)
3. Tester tous les endpoints

### Option 2 : Créer des données de test

```powershell
python manage.py shell
```

```python
from apps.users.models import User
from apps.properties.models import Maison

# Créer un locataire
locataire = User.objects.create_user(
    email="locataire@test.com",
    nom="Kouassi",
    prenoms="Jean",
    telephone="0708090605",
    password="test1234",
    role="LOCATAIRE"
)

# Créer une maison
maison = Maison.objects.create(
    titre="Appartement F2 Marcory",
    description="Joli F2 bien situé",
    type_logement="F2",
    prix=80000,
    caution=160000,
    adresse="Marcory Zone 4",
    ville="Abidjan",
    commune="Marcory",
    quartier="Zone 4",
    nombre_chambres=2,
    nombre_salles_bain=1,
    statut="DISPONIBLE"
)

print(f"Maison créée: {maison.reference}")
```

### Option 3 : Script de seed automatique

```powershell
python scripts\seed_db.py
```

## 📚 Documentation Complète

- **Architecture** : `docs/ARCHITECTURE.md`
- **API** : `docs/API.md`
- **Déploiement** : `docs/DEPLOYMENT.md`

## 🐛 Problèmes courants

### Erreur : "No module named 'psycopg2'"

```powershell
pip install psycopg2-binary
```

### Erreur : "connection to server failed"

Vérifiez que PostgreSQL est démarré :
```powershell
# Windows
services.msc → PostgreSQL → Démarrer
```

### Erreur migrations

```powershell
python manage.py makemigrations
python manage.py migrate
```

### Réinitialiser complètement

```powershell
# Supprimer la base
dropdb gestion_locative
createdb gestion_locative

# Réappliquer
python manage.py migrate
python manage.py createsuperuser
```

## 🔧 Commandes utiles

```powershell
# Lister toutes les URLs
python manage.py show_urls

# Shell interactif
python manage.py shell

# Créer des migrations
python manage.py makemigrations

# Appliquer migrations
python manage.py migrate

# Collecter les fichiers statiques
python manage.py collectstatic

# Lancer les tests
pytest

# Lancer Celery (tâches asynchrones)
celery -A config worker -l info
```

## 📞 Support

Si vous rencontrez des problèmes :
1. Consultez `docs/API.md` et `docs/ARCHITECTURE.md`
2. Vérifiez les logs dans `logs/django.log`
3. Testez sur http://localhost:8000/api/docs/

## 🎊 Félicitations !

Vous avez maintenant un backend Django REST Framework complet et fonctionnel pour votre plateforme de gestion locative !

**Prochaine étape** : Développer le frontend React pour consommer cette API.

## 📊 Vue d'ensemble des modules

✅ **Core** - Utilitaires communs  
✅ **Users** - Gestion utilisateurs  
✅ **Authentication** - JWT, Login, Register  
✅ **Properties** - Catalogue de maisons  
✅ **Billing** - Facturation SODECI/CIE automatique  
✅ **Payments** - Validation manuelle des paiements  
✅ **Rentals** - Contrats de location  
✅ **Reservations** - Réservations de maisons  
✅ **Expenses** - Gestion des dépenses  
✅ **Notifications** - Système de notifications  
✅ **Dashboard** - Analytics et statistiques  

Bon développement ! 🚀
