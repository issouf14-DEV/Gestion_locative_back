# Documentation API - Gestion Locative

## 🔗 Base URL

**Développement**: `http://localhost:8000/api/`  
**Production**: `https://votre-app.onrender.com/api/`

## 📚 Documentation Interactive

- **Swagger UI**: `/api/docs/`
- **ReDoc**: `/api/redoc/`
- **Schema JSON**: `/api/schema/`

## 🔐 Authentification

L'API utilise **JWT (JSON Web Tokens)** pour l'authentification.

### Obtenir un token

**Endpoint**: `POST /api/auth/login/`

**Body**:
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Connexion réussie",
  "data": {
    "user": {
      "id": "uuid",
      "email": "user@example.com",
      "nom": "Doe",
      "prenoms": "John",
      "role": "LOCATAIRE"
    },
    "tokens": {
      "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
      "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
    }
  }
}
```

### Utiliser le token

Ajouter dans les headers de chaque requête:
```
Authorization: Bearer {access_token}
```

### Rafraîchir le token

**Endpoint**: `POST /api/auth/token/refresh/`

**Body**:
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

## 📋 Endpoints Principaux

### Authentication

| Méthode | Endpoint | Description | Auth |
|---------|----------|-------------|------|
| POST | `/api/auth/register/` | Inscription | Non |
| POST | `/api/auth/login/` | Connexion | Non |
| POST | `/api/auth/logout/` | Déconnexion | Oui |
| POST | `/api/auth/password-reset/` | Demande reset password | Non |
| POST | `/api/auth/password-reset/confirm/` | Confirmer reset | Non |

### Users

| Méthode | Endpoint | Description | Auth |
|---------|----------|-------------|------|
| GET | `/api/users/` | Liste utilisateurs | Admin |
| GET | `/api/users/me/` | Utilisateur connecté | Oui |
| GET | `/api/users/{id}/` | Détails utilisateur | Owner/Admin |
| PATCH | `/api/users/{id}/` | Modifier utilisateur | Owner/Admin |
| POST | `/api/users/change_password/` | Changer password | Oui |
| GET | `/api/users/locataires/` | Liste locataires | Admin |

### Properties (Maisons)

| Méthode | Endpoint | Description | Auth |
|---------|----------|-------------|------|
| GET | `/api/properties/maisons/` | Liste maisons | Non |
| GET | `/api/properties/maisons/disponibles/` | Maisons disponibles | Non |
| GET | `/api/properties/maisons/{id}/` | Détails maison | Non |
| POST | `/api/properties/maisons/` | Créer maison | Admin |
| PUT/PATCH | `/api/properties/maisons/{id}/` | Modifier maison | Admin |
| DELETE | `/api/properties/maisons/{id}/` | Supprimer maison | Admin |
| POST | `/api/properties/maisons/{id}/ajouter_images/` | Ajouter images | Admin |
| PATCH | `/api/properties/maisons/{id}/changer_statut/` | Changer statut | Admin |

### Billing (Facturation)

| Méthode | Endpoint | Description | Auth |
|---------|----------|-------------|------|
| GET | `/api/billing/factures/` | Liste factures | Oui |
| GET | `/api/billing/factures/{id}/` | Détails facture | Owner/Admin |
| POST | `/api/billing/factures/repartir/` | Répartir SODECI/CIE | Admin |
| GET | `/api/billing/index-compteurs/` | Liste index | Admin |
| POST | `/api/billing/index-compteurs/` | Créer index | Admin |
| GET | `/api/billing/factures-collectives/` | Factures collectives | Admin |

### Payments

| Méthode | Endpoint | Description | Auth |
|---------|----------|-------------|------|
| GET | `/api/payments/` | Liste paiements | Oui |
| GET | `/api/payments/{id}/` | Détails paiement | Owner/Admin |
| POST | `/api/payments/` | Soumettre paiement | Locataire |
| POST | `/api/payments/{id}/valider/` | Valider paiement | Admin |
| POST | `/api/payments/{id}/rejeter/` | Rejeter paiement | Admin |

### Reservations

| Méthode | Endpoint | Description | Auth |
|---------|----------|-------------|------|
| GET | `/api/reservations/` | Liste réservations | Oui |
| GET | `/api/reservations/{id}/` | Détails réservation | Owner/Admin |
| POST | `/api/reservations/` | Créer réservation | Locataire |
| PATCH | `/api/reservations/{id}/` | Modifier réservation | Owner/Admin |

### Rentals (Locations)

| Méthode | Endpoint | Description | Auth |
|---------|----------|-------------|------|
| GET | `/api/rentals/` | Liste locations | Admin |
| GET | `/api/rentals/{id}/` | Détails location | Admin |
| POST | `/api/rentals/` | Créer location | Admin |
| PATCH | `/api/rentals/{id}/` | Modifier location | Admin |

### Expenses (Dépenses)

| Méthode | Endpoint | Description | Auth |
|---------|----------|-------------|------|
| GET | `/api/expenses/` | Liste dépenses | Admin |
| GET | `/api/expenses/{id}/` | Détails dépense | Admin |
| POST | `/api/expenses/` | Créer dépense | Admin |

### Dashboard

| Méthode | Endpoint | Description | Auth |
|---------|----------|-------------|------|
| GET | `/api/dashboard/admin/` | Stats admin | Admin |
| GET | `/api/dashboard/locataire/` | Stats locataire | Locataire |

### Notifications

| Méthode | Endpoint | Description | Auth |
|---------|----------|-------------|------|
| GET | `/api/notifications/` | Mes notifications | Oui |
| POST | `/api/notifications/{id}/marquer_lue/` | Marquer lue | Oui |
| POST | `/api/notifications/marquer_toutes_lues/` | Marquer toutes lues | Oui |

## 🔍 Filtres et Recherche

### Maisons

**Filtres disponibles**:
- `type_logement`: F1, F2, F3, etc.
- `prix_min` / `prix_max`
- `ville`, `commune`, `quartier`
- `nombre_chambres`, `nombre_chambres_min`
- `superficie_min` / `superficie_max`
- `meublee`: true/false
- `statut`: DISPONIBLE, LOUEE, etc.

**Recherche**: `search=appartement+moderne`

**Tri**: `ordering=-prix` (prix décroissant)

**Exemple**:
```
GET /api/properties/maisons/?type_logement=F2&prix_max=150000&ville=Abidjan&ordering=prix
```

### Factures

**Filtres**: `type_facture`, `statut`, `mois`, `annee`, `locataire`

## 📊 Pagination

Toutes les listes sont paginées (20 items par page par défaut).

**Paramètres**:
- `page`: Numéro de page (défaut: 1)
- `page_size`: Taille de page (max: 100)

**Response format**:
```json
{
  "pagination": {
    "count": 42,
    "next": "http://api.../page=2",
    "previous": null,
    "page_size": 20,
    "current_page": 1,
    "total_pages": 3
  },
  "results": [...]
}
```

## 📤 Upload de fichiers

### Images de maisons

**Endpoint**: `POST /api/properties/maisons/{id}/ajouter_images/`

**Content-Type**: `multipart/form-data`

**Form data**:
- `images`: Liste de fichiers (JPG, PNG, WEBP, max 5MB chacun)

### Preuve de paiement

**Endpoint**: `POST /api/payments/`

**Form data**:
- `montant`: Montant payé
- `factures_ids`: JSON array d'IDs de factures
- `preuve`: Image de la preuve (JPG, PNG)
- `notes_locataire`: Notes optionnelles

## ⚠️ Codes d'erreur

| Code | Description |
|------|-------------|
| 200 | Succès |
| 201 | Créé avec succès |
| 400 | Erreur de validation |
| 401 | Non authentifié |
| 403 | Non autorisé |
| 404 | Ressource introuvable |
| 500 | Erreur serveur |

**Format d'erreur**:
```json
{
  "success": false,
  "message": "Erreur de validation",
  "errors": {
    "email": ["Cette adresse email est déjà utilisée."]
  }
}
```

## 🧪 Exemples de requêtes

### Inscription

```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "telephone": "0123456789",
    "nom": "Doe",
    "prenoms": "John",
    "password": "SecurePass123!",
    "password_confirm": "SecurePass123!"
  }'
```

### Créer une maison

```bash
curl -X POST http://localhost:8000/api/properties/maisons/ \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "titre": "Bel appartement F3",
    "description": "Appartement moderne et spacieux",
    "type_logement": "F3",
    "prix": 125000,
    "caution": 250000,
    "adresse": "Cocody, Abidjan",
    "ville": "Abidjan",
    "commune": "Cocody",
    "quartier": "Riviera",
    "nombre_chambres": 3,
    "nombre_salles_bain": 2,
    "statut": "DISPONIBLE"
  }'
```

### Répartir facture SODECI

```bash
curl -X POST http://localhost:8000/api/billing/factures/repartir/ \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "type_facture": "SODECI",
    "montant_total": 29206,
    "mois": 3,
    "annee": 2026,
    "date_echeance": "2026-03-25"
  }'
```

## 📝 Notes importantes

- Les tokens JWT expirent après 60 minutes (configurable)
- Taille maximale des uploads: 5MB
- Rate limiting: 100 requêtes/minute (en production)
- Timezone: Africa/Abidjan (UTC+0)
- Format dates: YYYY-MM-DD
- Format datetime: YYYY-MM-DD HH:MM:SS
