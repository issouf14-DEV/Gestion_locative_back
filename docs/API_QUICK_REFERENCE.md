# API Quick Reference - Gestion Locative

## 🚀 Configuration Rapide

```javascript
// api.js
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api',
  headers: { 'Content-Type': 'application/json' }
});

api.interceptors.request.use(config => {
  const token = localStorage.getItem('access_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export default api;
```

---

## 🔐 Authentification

| Action | Endpoint | Méthode | Body |
|--------|----------|---------|------|
| **Connexion** | `/auth/login/` | POST | `{email, password}` |
| **Inscription** | `/auth/register/` | POST | `{email, password, password2, nom, prenoms, telephone, role}` |
| **Refresh Token** | `/auth/token/refresh/` | POST | `{refresh}` |
| **Déconnexion** | `/auth/logout/` | POST | - |
| **Mot de passe oublié** | `/auth/password-reset/` | POST | `{email}` |
| **Changer mot de passe** | `/auth/password-change/` | POST | `{old_password, new_password, confirm_password}` |
| **Google Login** | `/auth/google/` | POST | `{token}` |

---

## 👥 Utilisateurs

| Action | Endpoint | Admin | Body/Params |
|--------|----------|-------|-------------|
| **Mon profil** | `GET /users/me/` | ❌ | - |
| **Liste** | `GET /users/` | ✅ | `?role=&statut=&search=` |
| **Créer** | `POST /users/` | ✅ | `{email, password, nom, prenoms, telephone, role}` |
| **Modifier** | `PATCH /users/{id}/` | ✅ | `{...updates}` |
| **Locataires** | `GET /users/locataires/` | ✅ | - |
| **Changer statut** | `PATCH /users/{id}/update_status/` | ✅ | `{statut}` |

---

## 🏠 Propriétés

| Action | Endpoint | Public | Body/Params |
|--------|----------|--------|-------------|
| **Liste** | `GET /properties/maisons/` | ✅ | `?statut=&type_propriete=&commune=&min_prix=&max_prix=` |
| **Disponibles** | `GET /properties/maisons/disponibles/` | ✅ | - |
| **Détails** | `GET /properties/maisons/{id}/` | ✅ | - |
| **Créer** | `POST /properties/maisons/` | ❌ (Admin) | `{titre, type_propriete, prix, commune, quartier, ...}` |
| **Modifier** | `PATCH /properties/maisons/{id}/` | ❌ (Admin) | `{...updates}` |
| **Changer statut** | `PATCH /properties/maisons/{id}/changer_statut/` | ❌ (Admin) | `{statut}` |
| **Ajouter images** | `POST /properties/maisons/{id}/ajouter_images/` | ❌ (Admin) | FormData: `images[]` |

---

## 📝 Locations

| Action | Endpoint | Admin | Body/Params |
|--------|----------|-------|-------------|
| **Ma location** | `GET /rentals/ma_location/` | ❌ | - |
| **Liste** | `GET /rentals/` | ✅/❌ | `?statut=&locataire=&maison=` |
| **Créer** | `POST /rentals/` | ✅ | `{locataire, maison, date_debut, duree_mois, loyer_mensuel, caution}` |
| **Renouveler** | `POST /rentals/{id}/renouveler/` | ✅ | `{duree_supplementaire_mois}` |
| **Résilier** | `POST /rentals/{id}/resilier/` | ✅ | `{raison}` |
| **Actives** | `GET /rentals/actives/` | ✅ | - |
| **Expirant** | `GET /rentals/expirant/` | ✅ | `?jours=30` |
| **Statistiques** | `GET /rentals/statistiques/` | ✅ | - |

---

## 💰 Facturation

### Compteurs

| Action | Endpoint | Body |
|--------|----------|------|
| **Liste** | `GET /billing/compteurs/` | `?maison=&locataire=&type=&actif=` |
| **Créer** | `POST /billing/compteurs/` | `{numero, type_compteur, maison, date_installation}` |
| **Assigner** | `POST /billing/compteurs/assigner/` | `{compteur_id, locataire_id, index_initial}` |
| **Libérer** | `POST /billing/compteurs/{id}/liberer/` | - |
| **Par locataire** | `GET /billing/compteurs/par_locataire/` | `?locataire_id=` |

### Factures

| Action | Endpoint | Body/Params |
|--------|----------|-------------|
| **Liste** | `GET /billing/factures/` | `?locataire=&type_facture=&statut=&mois=&annee=` |
| **Créer** | `POST /billing/factures/` | `{locataire, type_facture, mois, annee, montant, date_echeance}` |
| **Répartir SODECI/CIE** | `POST /billing/factures/repartir/` | `{mois, annee, montant_sodeci, montant_cie}` |
| **Envoyer notification** | `POST /billing/factures/{id}/envoyer_notification/` | `{canaux: ['email', 'app', 'whatsapp']}` |
| **Lien WhatsApp** | `GET /billing/factures/{id}/lien_whatsapp/` | - |
| **Liens WhatsApp mois** | `GET /billing/factures/liens_whatsapp_mois/` | `?mois=&annee=&type=` |
| **📄 PDF Facture** | `GET /billing/factures/{id}/telecharger_pdf/` | responseType: 'blob' |
| **📄 Rapport mensuel** | `GET /billing/factures/rapport_mensuel/` | `?mois=&annee=` + responseType: 'blob' |

### Rappels de Loyer

| Action | Endpoint | Body |
|--------|----------|------|
| **WhatsApp** | `POST /billing/rappels-loyer/envoyer_whatsapp/` | `{locataire_id, montant, mois, annee}` |
| **Email** | `POST /billing/rappels-loyer/envoyer_email/` | `{locataire_id, montant, mois, annee}` |
| **Tous canaux** | `POST /billing/rappels-loyer/envoyer_tous_canaux/` | `{locataire_id, montant, mois, annee, canaux}` |
| **Liens mois** | `GET /billing/rappels-loyer/liens_whatsapp_mois/` | `?mois=&annee=` |
| **À tous** | `POST /billing/rappels-loyer/envoyer_rappels_tous/` | `{mois, annee, canaux}` |

---

## 💳 Paiements

### Workflow de Validation

| Action | Endpoint | Rôle | Body |
|--------|----------|------|------|
| **Mes paiements** | `GET /payments/paiements/mes_paiements/` | Locataire | - |
| **Soumettre** | `POST /payments/paiements/` | Locataire | FormData: `{montant, mode_paiement, reference_paiement, preuve_paiement, description}` |
| **En attente** | `GET /payments/paiements/en_attente/` | Admin | - |
| **Valider** | `POST /payments/paiements/{id}/valider/` | Admin | `{commentaire}` |
| **Rejeter** | `POST /payments/paiements/{id}/rejeter/` | Admin | `{commentaire}` (requis) |
| **Statistiques** | `GET /payments/paiements/statistiques/` | Admin | `?mois=&annee=` |

### Encaissement Direct (Admin)

| Action | Endpoint | Body |
|--------|----------|------|
| **Encaisser loyer** | `POST /payments/encaissements/encaisser_loyer/` | `{locataire_id, mois, annee, montant, mode_paiement, reference_paiement, notes}` |
| **Encaisser facture** | `POST /payments/encaissements/encaisser_facture/` | `{facture_id, montant, mode_paiement, reference_paiement, notes}` |
| **Encaisser multiple** | `POST /payments/encaissements/encaisser_multiple/` | `{factures_ids: [], montant_total, mode_paiement, reference_paiement, notes}` |
| **Factures impayées** | `GET /payments/encaissements/factures_impayees/` | `?locataire_id=` |
| **Résumé mois** | `GET /payments/encaissements/resume_mois/` | `?mois=&annee=` |

---

## 💸 Dépenses

| Action | Endpoint | Body |
|--------|----------|------|
| **Liste** | `GET /expenses/` | `?categorie=&maison=&date_debut=&date_fin=` |
| **Créer** | `POST /expenses/` | FormData: `{titre, categorie, montant, date_depense, maison, recu, description}` |
| **Modifier** | `PATCH /expenses/{id}/` | `{...updates}` |
| **Supprimer** | `DELETE /expenses/{id}/` | - |

---

## 🔔 Notifications

| Action | Endpoint | Body |
|--------|----------|------|
| **Liste** | `GET /notifications/` | `?type_notification=&lu=` |
| **Récentes** | `GET /notifications/recentes/` | - |
| **Non lues (count)** | `GET /notifications/non_lues/` | - |
| **Marquer lue** | `POST /notifications/{id}/marquer_lue/` | - |
| **Marquer toutes lues** | `POST /notifications/marquer_toutes_lues/` | - |
| **Envoyer** | `POST /notifications/envoyer/` | `{destinataires: [], titre, message, type_notification}` (Admin) |
| **À tous locataires** | `POST /notifications/envoyer_a_tous_locataires/` | `{titre, message, type_notification}` (Admin) |
| **Supprimer lues** | `DELETE /notifications/supprimer_lues/` | - |

---

## 📅 Réservations

| Action | Endpoint | Body |
|--------|----------|------|
| **Liste** | `GET /reservations/` | `?statut=&maison=&utilisateur=` |
| **Créer** | `POST /reservations/` | `{maison, date_visite, message}` |
| **Modifier** | `PATCH /reservations/{id}/` | `{statut}` |
| **Supprimer** | `DELETE /reservations/{id}/` | - |

---

## 📊 Dashboard

| Action | Endpoint | Rôle |
|--------|----------|------|
| **Admin** | `GET /dashboard/admin/` | Admin |
| **Locataire** | `GET /dashboard/locataire/` | Locataire |

---

## 📱 WhatsApp - Guide Rapide

```javascript
// 1. Obtenir le lien WhatsApp
const response = await api.get(`/billing/factures/${id}/lien_whatsapp/`);
const { lien_whatsapp } = response.data.data;

// 2. Ouvrir WhatsApp Web/App
window.open(lien_whatsapp, '_blank');

// C'est tout ! 100% gratuit, aucune config requise
```

### Composant React
```jsx
const WhatsAppButton = ({ factureId }) => (
  <button onClick={async () => {
    const res = await api.get(`/billing/factures/${factureId}/lien_whatsapp/`);
    window.open(res.data.data.lien_whatsapp, '_blank');
  }}>
    📱 Envoyer via WhatsApp
  </button>
);
```

---

## 📄 PDF - Guide Rapide

```javascript
// Fonction générique
const downloadPDF = async (url, filename) => {
  const response = await api.get(url, { responseType: 'blob' });
  const blob = new Blob([response.data], { type: 'application/pdf' });
  const link = document.createElement('a');
  link.href = window.URL.createObjectURL(blob);
  link.download = filename;
  link.click();
  window.URL.revokeObjectURL(link.href);
};

// Utilisation
await downloadPDF(
  `/billing/factures/${id}/telecharger_pdf/`,
  `facture_${reference}.pdf`
);
```

---

## 🛠️ Codes Erreur

| Code | Signification | Action |
|------|--------------|--------|
| **400** | Données invalides | Vérifier les champs (response.data.errors) |
| **401** | Non authentifié | Refresh token ou rediriger vers login |
| **403** | Non autorisé | Vérifier les permissions (admin/user) |
| **404** | Non trouvé | Ressource inexistante |
| **500** | Erreur serveur | Réessayer plus tard |

---

## 📋 Types de Données

### Rôles Utilisateur
- `LOCATAIRE` - Locataire
- `BAILLEUR` - Propriétaire
- `ADMIN` - Administrateur

### Statuts Utilisateur
- `ACTIF` - Actif
- `INACTIF` - Inactif
- `SUSPENDU` - Suspendu

### Types de Propriété
- `APPARTEMENT`
- `STUDIO`
- `VILLA`
- `CHAMBRE`
- `DUPLEX`

### Statuts Maison
- `DISPONIBLE`
- `LOUEE`
- `EN_MAINTENANCE`
- `INDISPONIBLE`

### Statuts Location
- `ACTIVE` - Active
- `EXPIREE` - Expirée
- `RESILLIEE` - Résiliée

### Types de Facture
- `LOYER` - Loyer mensuel
- `SODECI` - Eau (quote-part)
- `CIE` - Électricité (quote-part)

### Statuts Facture
- `IMPAYEE` - Impayée
- `PAYEE_PARTIELLE` - Payée partiellement
- `PAYEE` - Payée

### Types de Compteur
- `SODECI` - Eau
- `CIE` - Électricité

### Modes de Paiement
- `ESPECES` - Espèces
- `VIREMENT` - Virement bancaire
- `MOBILE_MONEY` - Mobile Money
- `CHEQUE` - Chèque

### Statuts Paiement
- `EN_ATTENTE` - En attente de validation
- `VALIDE` - Validé
- `REJETE` - Rejeté

### Types de Notification
- `INFO` - Information
- `ALERTE` - Alerte
- `SUCCES` - Succès
- `ERREUR` - Erreur

### Statuts Réservation
- `EN_ATTENTE` - En attente
- `CONFIRMEE` - Confirmée
- `ANNULEE` - Annulée

---

## 🔑 Permissions Rapides

| Endpoint | Public | Locataire | Admin |
|----------|--------|-----------|-------|
| Liste maisons | ✅ | ✅ | ✅ |
| Détails maison | ✅ | ✅ | ✅ |
| Créer/Modifier maison | ❌ | ❌ | ✅ |
| Ma location | ❌ | ✅ | ❌ |
| Mes factures | ❌ | ✅ | ✅ |
| Créer factures | ❌ | ❌ | ✅ |
| Soumettre paiement | ❌ | ✅ | ❌ |
| Valider paiement | ❌ | ❌ | ✅ |
| Encaisser directement | ❌ | ❌ | ✅ |
| Compteurs | ❌ | ❌ | ✅ |
| Rappels loyer | ❌ | ❌ | ✅ |
| Dépenses | ❌ | ❌ | ✅ |
| Dashboard admin | ❌ | ❌ | ✅ |
| Dashboard locataire | ❌ | ✅ | ❌ |

---

## 📝 Exemples Rapides

### Login + Fetch Data
```javascript
// 1. Login
const login = await api.post('/auth/login/', { email, password });
localStorage.setItem('access_token', login.data.data.access);
localStorage.setItem('refresh_token', login.data.data.refresh);

// 2. Fetch protected data
const maisons = await api.get('/properties/maisons/');
console.log(maisons.data.data);
```

### Créer et Envoyer Facture
```javascript
// 1. Créer facture
const facture = await api.post('/billing/factures/', {
  locataire: 1,
  type_facture: 'LOYER',
  mois: 3,
  annee: 2026,
  montant: 250000,
  date_echeance: '2026-04-05'
});

// 2. Envoyer par WhatsApp
const whatsapp = await api.get(`/billing/factures/${facture.data.data.id}/lien_whatsapp/`);
window.open(whatsapp.data.data.lien_whatsapp, '_blank');

// 3. Télécharger PDF
const pdf = await api.get(
  `/billing/factures/${facture.data.data.id}/telecharger_pdf/`,
  { responseType: 'blob' }
);
// ... download logic
```

### Soumettre et Valider Paiement
```javascript
// Locataire soumet
const formData = new FormData();
formData.append('montant', 250000);
formData.append('mode_paiement', 'MOBILE_MONEY');
formData.append('preuve_paiement', file);
const paiement = await api.post('/payments/paiements/', formData);

// Admin valide
await api.post(`/payments/paiements/${paiement.data.data.id}/valider/`, {
  commentaire: 'Paiement confirmé'
});
```

### Encaisser Directement (Admin)
```javascript
// Encaisser loyer directement sans soumission locataire
await api.post('/payments/encaissements/encaisser_loyer/', {
  locataire_id: 1,
  mois: 3,
  annee: 2026,
  montant: 250000,
  mode_paiement: 'ESPECES'
});
```

---

## 🎯 Checklist d'Intégration

- [ ] Configuration Axios avec intercepteurs
- [ ] Gestion du refresh token automatique
- [ ] Page de login/register
- [ ] Dashboard admin avec statistiques
- [ ] Dashboard locataire avec factures/paiements
- [ ] Liste des propriétés (public)
- [ ] Gestion des locations (admin)
- [ ] Gestion des compteurs et factures (admin)
- [ ] Système de paiement (soumission + validation)
- [ ] Encaissement direct (admin)
- [ ] Notifications en temps réel
- [ ] Boutons WhatsApp pour factures/loyers
- [ ] Téléchargement PDF factures/rapports
- [ ] Upload d'images propriétés
- [ ] Gestion des dépenses
- [ ] Réservations de visite
- [ ] Profil utilisateur
- [ ] Gestion des erreurs avec messages clairs

---

**Total: 114 endpoints disponibles**

📚 Documentation complète: [FRONTEND_INTEGRATION.md](./FRONTEND_INTEGRATION.md)
