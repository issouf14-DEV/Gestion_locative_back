# Plateforme de Gestion Locative - Backend

Application web complète de gestion locative pour la Côte d'Ivoire.

## 🚀 Technologies

- **Django 5+** - Framework web Python
- **Django REST Framework** - API REST
- **PostgreSQL** - Base de données
- **JWT** - Authentification
- **Celery + Redis** - Tâches asynchrones
- **Cloudinary** - Stockage d'images

## 📋 Prérequis

- Python 3.11+
- PostgreSQL 14+
- Redis (pour Celery)

## 🛠️ Installation

### 1. Cloner le repository

```bash
git clone <repository-url>
cd gestion-locative-backend
```

### 2. Créer un environnement virtuel

```bash
python -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate
```

### 3. Installer les dépendances

```bash
pip install -r requirements/development.txt
```

### 4. Configurer les variables d'environnement

```bash
cp .env.example .env
# Éditer .env avec vos valeurs
```

### 5. Créer la base de données

```bash
createdb gestion_locative
```

### 6. Appliquer les migrations

```bash
python manage.py migrate
```

### 7. Créer un superutilisateur

```bash
python manage.py createsuperuser
```

### 8. Lancer le serveur de développement

```bash
python manage.py runserver
```

L'API sera accessible sur `http://localhost:8000/api/`

## 📁 Structure du projet

```
gestion-locative-backend/
├── config/          # Configuration Django
├── apps/            # Modules de l'application
│   ├── users/       # Gestion utilisateurs
│   ├── authentication/  # Authentification JWT
│   ├── properties/  # Gestion des maisons
│   ├── reservations/  # Réservations
│   ├── rentals/     # Locations (contrats)
│   ├── billing/     # Facturation SODECI/CIE
│   ├── payments/    # Paiements et validation
│   ├── expenses/    # Dépenses
│   ├── notifications/  # Notifications
│   ├── dashboard/   # Tableau de bord
│   └── core/        # Utilitaires communs
├── media/           # Fichiers uploadés
├── static/          # Fichiers statiques
└── templates/       # Templates emails
```

## 🧪 Tests

```bash
pytest
```

## 📚 Documentation API

Une fois le serveur lancé, accédez à :
- Swagger UI: `http://localhost:8000/api/docs/`
- ReDoc: `http://localhost:8000/api/redoc/`

## 🔐 Authentification

L'API utilise JWT (JSON Web Tokens) pour l'authentification.

**Obtenir un token:**
```bash
POST /api/auth/login/
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Utiliser le token:**
```
Authorization: Bearer <access_token>
```

## 📦 Modules

### Users
Gestion des utilisateurs (locataires, administrateurs)

### Properties
Gestion du catalogue des maisons disponibles

### Billing
Calcul automatique des factures SODECI/CIE selon la consommation

### Payments
Validation manuelle des paiements uploadés par les locataires

### Dashboard
Statistiques et analytics pour l'administrateur

## 🚀 Déploiement

Voir [DEPLOYMENT.md](docs/DEPLOYMENT.md) pour les instructions de déploiement.

## 📄 Licence

Propriétaire - Tous droits réservés
