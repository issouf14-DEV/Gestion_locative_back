# Architecture Backend - Plateforme de Gestion Locative

## Vue d'ensemble

Cette architecture suit le pattern **MVT (Model-View-Template)** de Django avec une séparation claire des responsabilités, utilisant Django REST Framework pour l'API.

## Structure Modulaire

Le backend est organisé en **modules indépendants** (apps Django) qui communiquent entre eux via des services.

### Modules principaux :

1. **core** - Utilitaires communs (BaseModel, permissions, pagination, etc.)
2. **users** - Gestion des utilisateurs (User, Profile, authentification)
3. **authentication** - JWT, login, register, password reset
4. **properties** - Gestion des maisons (Maison, ImageMaison)
5. **billing** - Facturation SODECI/CIE + Loyer (Facture, IndexCompteur)
6. **payments** - Validation manuelle des paiements
7. **rentals** - Contrats de location
8. **reservations** - Réservations de maisons
9. **expenses** - Gestion des dépenses
10. **notifications** - Système de notifications
11. **dashboard** - Statistiques et analytics

## Flux de données

### 1. Authentification
```
Client → POST /api/auth/register/ → User créé → JWT tokens renvoyés
Client → POST /api/auth/login/ → Vérification credentials → JWT tokens
Client → Header: Authorization: Bearer {token} → Actions authentifiées
```

### 2. Gestion des maisons (Properties)
```
Visiteur → GET /api/properties/maisons/ → Liste maisons disponibles
Admin → POST /api/properties/maisons/ → Création maison
Admin → POST /api/properties/maisons/{id}/ajouter_images/ → Upload images
```

### 3. Système de facturation SODECI/CIE
```
Admin → POST /api/billing/index-compteurs/ → Saisie index mensuels
Admin → POST /api/billing/factures/repartir/ → Calcul automatique
       ↓
FactureCalculator.calculer_repartition()
       ↓
1. Récupère tous les index du mois
2. Calcule consommation individuelle (nouveau - ancien)
3. Calcule total des consommations
4. Calcule pourcentage par locataire
5. Répartit le montant total selon les pourcentages
6. Crée les factures individuelles
```

### 4. Workflow de paiement
```
Locataire → POST /api/payments/ (avec preuve) → Paiement créé (statut: EN_ATTENTE)
       ↓
Notification automatique à l'admin
       ↓
Admin → GET /api/payments/?statut=EN_ATTENTE → Liste paiements en attente
Admin → POST /api/payments/{id}/valider/ → Paiement validé
       ↓
       ├→ Factures marquées PAYEE
       ├→ Dette locataire mise à jour
       └→ Notification envoyée au locataire
```

### 5. Dashboard
```
Admin → GET /api/dashboard/admin/ → DashboardService.get_admin_stats()
       ↓
       ├→ Total maisons (disponibles/louées)
       ├→ Total locataires (à jour/en retard)
       ├→ Revenus du mois
       ├→ Dépenses du mois
       └→ Factures impayées

Locataire → GET /api/dashboard/locataire/ → Ses infos personnelles
       ↓
       ├→ Dette totale
       ├→ Factures impayées
       ├→ Location actuelle
       └→ Historique paiements
```

## Sécurité & Permissions

### Niveaux d'accès :
- **Public** : Liste maisons disponibles
- **Authentifié** : CRUD sur ses propres données
- **Admin** : Accès complet + validation + statistiques

### Permissions custom :
- `IsAdminUser` - Réservé aux administrateurs
- `IsOwnerOrAdmin` - Propriétaire de l'objet ou admin
- `IsAdminOrReadOnly` - Lecture publique, écriture admin

## Base de données

### Relations principales :
```
User (1) → (N) Location → (1) Maison
User (1) → (N) Facture
User (1) → (N) Paiement
Maison (1) → (N) ImageMaison
Facture (N) ← (1) FactureCollective (SODECI/CIE)
```

## Technologies & Stack

- **Framework**: Django 5+ REST Framework
- **Base de données**: PostgreSQL
- **Authentification**: JWT (SimpleJWT)
- **Tâches async**: Celery + Redis
- **Stockage**: Cloudinary (images)
- **Documentation**: drf-spectacular (OpenAPI/Swagger)
- **Tests**: pytest + pytest-django

## Déploiement

- **Frontend**: Vercel (React)
- **Backend**: Render.com / Railway (Django + PostgreSQL)
- **Media**: Cloudinary CDN
- **DNS**: Cloudflare

## Points clés

✅ Validation manuelle des paiements (pas d'API de paiement en ligne)
✅ Calcul automatique des factures SODECI/CIE selon consommation réelle
✅ Système de notifications in-app + email
✅ Dashboard analytics avec statistiques financières
✅ API REST complète et documentée (Swagger)
✅ Architecture modulaire et scalable
