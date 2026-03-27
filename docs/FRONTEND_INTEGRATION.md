# Guide d'Intégration Frontend - API Gestion Locative

## Table des Matières

1. [Configuration de Base](#configuration-de-base)
2. [Authentification & Autorisation](#authentification--autorisation)
3. [Module Utilisateurs](#module-utilisateurs)
4. [Module Propriétés](#module-propriétés)
5. [Module Locations](#module-locations)
6. [Module Facturation](#module-facturation)
7. [Module Paiements](#module-paiements)
8. [Module Dépenses](#module-dépenses)
9. [Module Notifications](#module-notifications)
10. [Module Réservations](#module-réservations)
11. [Dashboard](#dashboard)
12. [Gestion des Erreurs](#gestion-des-erreurs)
13. [Intégration WhatsApp](#intégration-whatsapp)
14. [Téléchargement PDF](#téléchargement-pdf)

---

## Configuration de Base

### URL de Base
```javascript
const API_BASE_URL = 'http://localhost:8000/api';
```

### Structure de Réponse Standard
Toutes les APIs retournent une réponse standardisée avec ce format :

```json
{
  "success": true,
  "message": "Message descriptif",
  "data": { /* données */ },
  "errors": null
}
```

En cas d'erreur :
```json
{
  "success": false,
  "message": "Message d'erreur",
  "data": null,
  "errors": { "field": ["error messages"] }
}
```

### Configuration Axios
```javascript
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Intercepteur pour ajouter le token JWT
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Intercepteur pour gérer le refresh token
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        const refreshToken = localStorage.getItem('refresh_token');
        const response = await axios.post(
          'http://localhost:8000/api/auth/token/refresh/',
          { refresh: refreshToken }
        );
        
        const { access } = response.data;
        localStorage.setItem('access_token', access);
        
        originalRequest.headers.Authorization = `Bearer ${access}`;
        return api(originalRequest);
      } catch (err) {
        // Rediriger vers la page de connexion
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return Promise.reject(err);
      }
    }
    
    return Promise.reject(error);
  }
);

export default api;
```

---

## Authentification & Autorisation

### 1. Inscription
```javascript
// POST /api/auth/register/
const register = async (userData) => {
  const response = await api.post('/auth/register/', {
    email: 'user@example.com',
    password: 'SecurePass123!',
    password2: 'SecurePass123!',
    nom: 'Doe',
    prenoms: 'John',
    telephone: '+225 07 00 00 00 00',
    role: 'LOCATAIRE'  // ou 'BAILLEUR', 'ADMIN'
  });
  return response.data;
};
```

### 2. Connexion
```javascript
// POST /api/auth/login/
const login = async (email, password) => {
  const response = await api.post('/auth/login/', {
    email,
    password
  });
  
  const { access, refresh, user } = response.data.data;
  
  // Stocker les tokens
  localStorage.setItem('access_token', access);
  localStorage.setItem('refresh_token', refresh);
  localStorage.setItem('user', JSON.stringify(user));
  
  return response.data;
};
```

### 3. Connexion Google
```javascript
// POST /api/auth/google/
const googleLogin = async (googleToken) => {
  const response = await api.post('/auth/google/', {
    token: googleToken
  });
  
  const { access, refresh, user } = response.data.data;
  localStorage.setItem('access_token', access);
  localStorage.setItem('refresh_token', refresh);
  localStorage.setItem('user', JSON.stringify(user));
  
  return response.data;
};
```

### 4. Déconnexion
```javascript
// POST /api/auth/logout/
const logout = async () => {
  await api.post('/auth/logout/');
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user');
};
```

### 5. Rafraîchir Token
```javascript
// POST /api/auth/token/refresh/
const refreshToken = async () => {
  const refresh = localStorage.getItem('refresh_token');
  const response = await api.post('/auth/token/refresh/', { refresh });
  
  const { access } = response.data;
  localStorage.setItem('access_token', access);
  
  return access;
};
```

### 6. Réinitialisation Mot de Passe (Oublié)
```javascript
// POST /api/auth/password-reset/
const requestPasswordReset = async (email) => {
  const response = await api.post('/auth/password-reset/', { email });
  return response.data;
};

// POST /api/auth/password-reset/confirm/
const confirmPasswordReset = async (uid, token, newPassword) => {
  const response = await api.post('/auth/password-reset/confirm/', {
    uid,
    token,
    new_password: newPassword,
    confirm_password: newPassword
  });
  return response.data;
};
```

### 7. Changement Mot de Passe (Connecté)
```javascript
// POST /api/auth/password-change/
const changePassword = async (oldPassword, newPassword) => {
  const response = await api.post('/auth/password-change/', {
    old_password: oldPassword,
    new_password: newPassword,
    confirm_password: newPassword
  });
  return response.data;
};
```

### 8. Vérification Email
```javascript
// GET /api/auth/verify-email/{uid}/{token}/
// Appelé depuis le lien dans l'email
```

---

## Module Utilisateurs

### 1. Profil de l'utilisateur connecté
```javascript
// GET /api/users/me/
const getMyProfile = async () => {
  const response = await api.get('/users/me/');
  return response.data.data;
};
```

### 2. Liste des utilisateurs (Admin)
```javascript
// GET /api/users/
const getUsers = async (filters = {}) => {
  const response = await api.get('/users/', {
    params: {
      role: filters.role,        // LOCATAIRE, BAILLEUR, ADMIN
      statut: filters.statut,    // ACTIF, INACTIF, SUSPENDU
      is_active: filters.isActive,
      search: filters.search,    // nom, prenoms, email, telephone
      ordering: '-date_joined',  // ou 'nom', 'prenoms'
      page: filters.page || 1,
      page_size: filters.pageSize || 10
    }
  });
  return response.data;
};
```

### 3. Détails d'un utilisateur
```javascript
// GET /api/users/{id}/
const getUserById = async (userId) => {
  const response = await api.get(`/users/${userId}/`);
  return response.data.data;
};
```

### 4. Créer un utilisateur (Admin)
```javascript
// POST /api/users/
const createUser = async (userData) => {
  const response = await api.post('/users/', {
    email: 'user@example.com',
    password: 'SecurePass123!',
    nom: 'Doe',
    prenoms: 'John',
    telephone: '+225 07 00 00 00 00',
    role: 'LOCATAIRE',
    date_naissance: '1990-01-01',
    lieu_naissance: 'Abidjan',
    nationalite: 'Ivoirienne',
    numero_piece: 'CI123456',
    type_piece: 'CNI'  // CNI, PASSPORT, CARTE_SEJOUR
  });
  return response.data;
};
```

### 5. Modifier un utilisateur
```javascript
// PATCH /api/users/{id}/
const updateUser = async (userId, updates) => {
  const response = await api.patch(`/users/${userId}/`, updates);
  return response.data;
};
```

### 6. Changer le mot de passe
```javascript
// POST /api/users/change_password/
const changeUserPassword = async (oldPassword, newPassword) => {
  const response = await api.post('/users/change_password/', {
    old_password: oldPassword,
    new_password: newPassword,
    confirm_password: newPassword
  });
  return response.data;
};
```

### 7. Mettre à jour le statut (Admin)
```javascript
// PATCH /api/users/{id}/update_status/
const updateUserStatus = async (userId, statut) => {
  const response = await api.patch(`/users/${userId}/update_status/`, {
    statut: statut  // ACTIF, INACTIF, SUSPENDU
  });
  return response.data;
};
```

### 8. Liste des locataires (Admin)
```javascript
// GET /api/users/locataires/
const getLocataires = async () => {
  const response = await api.get('/users/locataires/');
  return response.data.data;
};
```

### 9. Profil utilisateur
```javascript
// GET /api/users/{id}/profile/
const getUserProfile = async (userId) => {
  const response = await api.get(`/users/${userId}/profile/`);
  return response.data.data;
};

// PATCH /api/users/{id}/profile/
const updateUserProfile = async (userId, profileData) => {
  const response = await api.patch(`/users/${userId}/profile/`, profileData);
  return response.data;
};
```

---

## Module Propriétés

### 1. Liste des maisons (Public)
```javascript
// GET /api/properties/maisons/
const getMaisons = async (filters = {}) => {
  const response = await api.get('/properties/maisons/', {
    params: {
      statut: filters.statut,          // DISPONIBLE, LOUEE, EN_MAINTENANCE, INDISPONIBLE
      type_propriete: filters.type,    // APPARTEMENT, STUDIO, VILLA, CHAMBRE, DUPLEX
      commune: filters.commune,
      quartier: filters.quartier,
      min_prix: filters.minPrix,
      max_prix: filters.maxPrix,
      nombre_chambres: filters.chambres,
      meublee: filters.meublee,
      search: filters.search,
      ordering: filters.ordering || '-created_at',
      page: filters.page || 1,
      page_size: filters.pageSize || 10
    }
  });
  return response.data;
};
```

### 2. Maisons disponibles uniquement
```javascript
// GET /api/properties/maisons/disponibles/
const getMaisonsDisponibles = async () => {
  const response = await api.get('/properties/maisons/disponibles/');
  return response.data.data;
};
```

### 3. Détails d'une maison
```javascript
// GET /api/properties/maisons/{id}/
const getMaisonById = async (maisonId) => {
  const response = await api.get(`/properties/maisons/${maisonId}/`);
  return response.data.data;
};
```

### 4. Créer une maison (Admin)
```javascript
// POST /api/properties/maisons/
const createMaison = async (maisonData) => {
  const response = await api.post('/properties/maisons/', {
    titre: 'Belle villa meublée',
    description: 'Description complète...',
    type_propriete: 'VILLA',
    prix: 250000,
    commune: 'Cocody',
    quartier: 'Angré',
    adresse: '7ème tranche, lot 123',
    superficie: 150.5,
    nombre_chambres: 3,
    nombre_salles_bain: 2,
    nombre_salons: 1,
    meublee: true,
    equipements: ['Climatisation', 'Cuisine équipée', 'Parking'],
    disponible_le: '2026-04-01',
    statut: 'DISPONIBLE'
  });
  return response.data;
};
```

### 5. Modifier une maison (Admin)
```javascript
// PATCH /api/properties/maisons/{id}/
const updateMaison = async (maisonId, updates) => {
  const response = await api.patch(`/properties/maisons/${maisonId}/`, updates);
  return response.data;
};
```

### 6. Supprimer une maison (Admin)
```javascript
// DELETE /api/properties/maisons/{id}/
const deleteMaison = async (maisonId) => {
  await api.delete(`/properties/maisons/${maisonId}/`);
};
```

### 7. Changer le statut d'une maison (Admin)
```javascript
// PATCH /api/properties/maisons/{id}/changer_statut/
const changerStatutMaison = async (maisonId, statut) => {
  const response = await api.patch(
    `/properties/maisons/${maisonId}/changer_statut/`,
    { statut }  // DISPONIBLE, LOUEE, EN_MAINTENANCE, INDISPONIBLE
  );
  return response.data;
};
```

### 8. Ajouter des images à une maison (Admin)
```javascript
// POST /api/properties/maisons/{id}/ajouter_images/
const ajouterImagesMaison = async (maisonId, files) => {
  const formData = new FormData();
  files.forEach(file => {
    formData.append('images', file);
  });
  
  const response = await api.post(
    `/properties/maisons/${maisonId}/ajouter_images/`,
    formData,
    {
      headers: { 'Content-Type': 'multipart/form-data' }
    }
  );
  return response.data;
};
```

### 9. Récupérer les images d'une maison
```javascript
// GET /api/properties/maisons/{id}/images/
const getImagesMaison = async (maisonId) => {
  const response = await api.get(`/properties/maisons/${maisonId}/images/`);
  return response.data.data;
};
```

### 10. Gérer les images
```javascript
// GET /api/properties/images/
const getAllImages = async () => {
  const response = await api.get('/properties/images/');
  return response.data;
};

// DELETE /api/properties/images/{id}/
const deleteImage = async (imageId) => {
  await api.delete(`/properties/images/${imageId}/`);
};

// PATCH /api/properties/images/{id}/definir_principale/
const setImagePrincipale = async (imageId) => {
  const response = await api.patch(`/properties/images/${imageId}/definir_principale/`);
  return response.data;
};
```

---

## Module Locations

### 1. Liste des locations
```javascript
// GET /api/rentals/
const getLocations = async (filters = {}) => {
  const response = await api.get('/rentals/', {
    params: {
      statut: filters.statut,      // ACTIVE, EXPIREE, RESILLIEE
      locataire: filters.locataireId,
      maison: filters.maisonId,
      search: filters.search,
      ordering: filters.ordering || '-date_debut',
      page: filters.page || 1,
      page_size: filters.pageSize || 10
    }
  });
  return response.data;
};
```

### 2. Ma location (Locataire)
```javascript
// GET /api/rentals/ma_location/
const getMaLocation = async () => {
  const response = await api.get('/rentals/ma_location/');
  return response.data.data;
};
```

### 3. Détails d'une location
```javascript
// GET /api/rentals/{id}/
const getLocationById = async (locationId) => {
  const response = await api.get(`/rentals/${locationId}/`);
  return response.data.data;
};
```

### 4. Créer une location (Admin)
```javascript
// POST /api/rentals/
const createLocation = async (locationData) => {
  const response = await api.post('/rentals/', {
    locataire: locataireId,
    maison: maisonId,
    date_debut: '2026-04-01',
    duree_mois: 12,
    loyer_mensuel: 250000,
    caution: 500000,
    avance_loyer_mois: 2,
    frais_agence: 50000,
    charges_mensuelles: 15000,
    conditions_particulieres: 'Règlement intérieur...'
  });
  return response.data;
};
```

### 5. Modifier une location (Admin)
```javascript
// PATCH /api/rentals/{id}/
const updateLocation = async (locationId, updates) => {
  const response = await api.patch(`/rentals/${locationId}/`, updates);
  return response.data;
};
```

### 6. Renouveler une location (Admin)
```javascript
// POST /api/rentals/{id}/renouveler/
const renouvelerLocation = async (locationId, mois) => {
  const response = await api.post(`/rentals/${locationId}/renouveler/`, {
    duree_supplementaire_mois: mois
  });
  return response.data;
};
```

### 7. Résilier une location (Admin)
```javascript
// POST /api/rentals/{id}/resilier/
const resilierLocation = async (locationId, raison) => {
  const response = await api.post(`/rentals/${locationId}/resilier/`, {
    raison: raison  // optionnel
  });
  return response.data;
};
```

### 8. Locations actives (Admin)
```javascript
// GET /api/rentals/actives/
const getLocationsActives = async () => {
  const response = await api.get('/rentals/actives/');
  return response.data.data;
};
```

### 9. Locations expirant bientôt (Admin)
```javascript
// GET /api/rentals/expirant/
const getLocationsExpirant = async (jours = 30) => {
  const response = await api.get('/rentals/expirant/', {
    params: { jours }
  });
  return response.data.data;
};
```

### 10. Statistiques des locations (Admin)
```javascript
// GET /api/rentals/statistiques/
const getStatistiquesLocations = async () => {
  const response = await api.get('/rentals/statistiques/');
  return response.data.data;
};
```

---

## Module Facturation

### 1. Gestion des Compteurs

#### Liste des compteurs
```javascript
// GET /api/billing/compteurs/
const getCompteurs = async (filters = {}) => {
  const response = await api.get('/billing/compteurs/', {
    params: {
      maison: filters.maisonId,
      locataire: filters.locataireId,
      type: filters.type,        // SODECI, CIE
      actif: filters.actif       // true/false
    }
  });
  return response.data;
};
```

#### Créer un compteur (Admin)
```javascript
// POST /api/billing/compteurs/
const createCompteur = async (compteurData) => {
  const response = await api.post('/billing/compteurs/', {
    numero: 'SODECI-123456',
    type_compteur: 'SODECI',  // ou 'CIE'
    maison: maisonId,
    dernier_index: 0,
    date_installation: '2026-03-01',
    actif: true
  });
  return response.data;
};
```

#### Assigner un compteur à un locataire (Admin)
```javascript
// POST /api/billing/compteurs/assigner/
const assignerCompteur = async (compteurId, locataireId, indexInitial) => {
  const response = await api.post('/billing/compteurs/assigner/', {
    compteur_id: compteurId,
    locataire_id: locataireId,
    index_initial: indexInitial  // optionnel
  });
  return response.data;
};
```

#### Libérer un compteur (Admin)
```javascript
// POST /api/billing/compteurs/{id}/liberer/
const libererCompteur = async (compteurId) => {
  const response = await api.post(`/billing/compteurs/${compteurId}/liberer/`);
  return response.data;
};
```

#### Compteurs d'un locataire
```javascript
// GET /api/billing/compteurs/par_locataire/
const getCompteursLocataire = async (locataireId) => {
  const response = await api.get('/billing/compteurs/par_locataire/', {
    params: { locataire_id: locataireId }
  });
  return response.data.data;
};
```

### 2. Gestion des Index de Compteurs

#### Liste des index
```javascript
// GET /api/billing/index-compteurs/
const getIndexCompteurs = async () => {
  const response = await api.get('/billing/index-compteurs/');
  return response.data;
};
```

#### Créer un relevé d'index (Admin)
```javascript
// POST /api/billing/index-compteurs/
const createIndexCompteur = async (indexData) => {
  const response = await api.post('/billing/index-compteurs/', {
    compteur: compteurId,
    index_precedent: 1000,
    index_actuel: 1150,
    date_releve: '2026-03-31',
    consommation: 150,  // calculé automatiquement si non fourni
    photo_compteur: null  // optionnel
  });
  return response.data;
};
```

### 3. Gestion des Factures

#### Liste des factures
```javascript
// GET /api/billing/factures/
const getFactures = async (filters = {}) => {
  const response = await api.get('/billing/factures/', {
    params: {
      locataire: filters.locataireId,
      type_facture: filters.type,  // LOYER, SODECI, CIE
      statut: filters.statut,      // IMPAYEE, PAYEE_PARTIELLE, PAYEE
      mois: filters.mois,
      annee: filters.annee
    }
  });
  return response.data;
};
```

#### Créer une facture (Admin)
```javascript
// POST /api/billing/factures/
const createFacture = async (factureData) => {
  const response = await api.post('/billing/factures/', {
    locataire: locataireId,
    type_facture: 'LOYER',  // LOYER, SODECI, CIE
    mois: 3,
    annee: 2026,
    montant: 250000,
    date_echeance: '2026-04-05',
    description: 'Loyer du mois de Mars 2026'
  });
  return response.data;
};
```

#### Répartir une facture SODECI/CIE (Admin)
```javascript
// POST /api/billing/factures/repartir/
const repartirFacture = async (repartitionData) => {
  const response = await api.post('/billing/factures/repartir/', {
    mois: 3,
    annee: 2026,
    montant_sodeci: 50000,      // optionnel
    montant_cie: 75000,         // optionnel
    facture_collective_id: 123  // optionnel
  });
  return response.data.data;
};
```

#### Envoyer une notification pour une facture
```javascript
// POST /api/billing/factures/{id}/envoyer_notification/
const envoyerNotificationFacture = async (factureId, canaux) => {
  const response = await api.post(
    `/billing/factures/${factureId}/envoyer_notification/`,
    {
      canaux: canaux  // ['email', 'app', 'whatsapp']
    }
  );
  return response.data.data;
};
```

#### Obtenir le lien WhatsApp pour une facture
```javascript
// GET /api/billing/factures/{id}/lien_whatsapp/
const getLienWhatsAppFacture = async (factureId) => {
  const response = await api.get(`/billing/factures/${factureId}/lien_whatsapp/`);
  return response.data.data;
  // Retour: { lien_whatsapp: "https://wa.me/...", telephone: "...", message: "..." }
};
```

#### Obtenir les liens WhatsApp pour toutes les factures du mois
```javascript
// GET /api/billing/factures/liens_whatsapp_mois/
const getLiensWhatsAppMois = async (mois, annee, typeFacture = null) => {
  const response = await api.get('/billing/factures/liens_whatsapp_mois/', {
    params: { 
      mois, 
      annee,
      type: typeFacture  // optionnel: LOYER, SODECI, CIE
    }
  });
  return response.data.data;
  // Retour: { nombre_factures: 5, factures: [{locataire: "...", lien: "...", montant: ...}] }
};
```

#### Télécharger le PDF d'une facture
```javascript
// GET /api/billing/factures/{id}/telecharger_pdf/
const telechargerPDFFacture = async (factureId) => {
  const response = await api.get(
    `/billing/factures/${factureId}/telecharger_pdf/`,
    { responseType: 'blob' }
  );
  
  // Créer un lien de téléchargement
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', `facture_${factureId}.pdf`);
  document.body.appendChild(link);
  link.click();
  link.remove();
};
```

#### Télécharger le rapport mensuel PDF
```javascript
// GET /api/billing/factures/rapport_mensuel/
const telechargerRapportMensuel = async (mois, annee) => {
  const response = await api.get('/billing/factures/rapport_mensuel/', {
    params: { mois, annee },
    responseType: 'blob'
  });
  
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', `rapport_${mois}_${annee}.pdf`);
  document.body.appendChild(link);
  link.click();
  link.remove();
};
```

### 4. Gestion des Factures Collectives

#### Liste des factures collectives (Admin)
```javascript
// GET /api/billing/factures-collectives/
const getFacturesCollectives = async () => {
  const response = await api.get('/billing/factures-collectives/');
  return response.data;
};
```

#### Créer une facture collective (Admin)
```javascript
// POST /api/billing/factures-collectives/
const createFactureCollective = async (factureData) => {
  const response = await api.post('/billing/factures-collectives/', {
    type_facture: 'SODECI',  // SODECI ou CIE
    mois: 3,
    annee: 2026,
    montant_total: 125000,
    date_facture: '2026-04-01',
    numero_facture: 'SODECI-2026-03-001',
    consommation_totale: 500,  // en m³ pour SODECI, kWh pour CIE
    description: 'Facture collective SODECI mars 2026'
  });
  return response.data;
};
```

### 5. Rappels de Loyer

#### Envoyer un rappel de loyer par WhatsApp
```javascript
// POST /api/billing/rappels-loyer/envoyer_whatsapp/
const envoyerRappelWhatsApp = async (rappelData) => {
  const response = await api.post('/billing/rappels-loyer/envoyer_whatsapp/', {
    locataire_id: locataireId,
    montant: 250000,
    mois: 3,
    annee: 2026
  });
  return response.data.data;
  // Retour: { lien_whatsapp: "https://wa.me/...", telephone: "...", message: "..." }
};
```

#### Envoyer un rappel de loyer par email
```javascript
// POST /api/billing/rappels-loyer/envoyer_email/
const envoyerRappelEmail = async (rappelData) => {
  const response = await api.post('/billing/rappels-loyer/envoyer_email/', {
    locataire_id: locataireId,
    montant: 250000,
    mois: 3,
    annee: 2026
  });
  return response.data;
};
```

#### Envoyer un rappel par tous les canaux
```javascript
// POST /api/billing/rappels-loyer/envoyer_tous_canaux/
const envoyerRappelTousCanaux = async (rappelData) => {
  const response = await api.post('/billing/rappels-loyer/envoyer_tous_canaux/', {
    locataire_id: locataireId,
    montant: 250000,
    mois: 3,
    annee: 2026,
    canaux: ['email', 'whatsapp']  // optionnel, défaut: les deux
  });
  return response.data.data;
  // Retour: { email: {...}, whatsapp: {...} }
};
```

#### Obtenir les liens WhatsApp pour tous les loyers du mois
```javascript
// GET /api/billing/rappels-loyer/liens_whatsapp_mois/
const getLiensWhatsAppLoyers = async (mois, annee) => {
  const response = await api.get('/billing/rappels-loyer/liens_whatsapp_mois/', {
    params: { mois, annee }
  });
  return response.data.data;
  // Retour: { nombre_locataires: 10, locataires: [{nom: "...", lien: "...", montant: ...}] }
};
```

#### Envoyer des rappels à tous les locataires
```javascript
// POST /api/billing/rappels-loyer/envoyer_rappels_tous/
const envoyerRappelsTous = async (mois, annee, canaux = null) => {
  const response = await api.post('/billing/rappels-loyer/envoyer_rappels_tous/', {
    mois,
    annee,
    canaux: canaux  // optionnel: ['email', 'whatsapp']
  });
  return response.data.data;
  // Retour: { nombre_rappels: 10, details: [...] }
};
```

---

## Module Paiements

### 1. Workflow de Validation des Paiements

#### Liste des paiements
```javascript
// GET /api/payments/paiements/
const getPaiements = async (filters = {}) => {
  const response = await api.get('/payments/paiements/', {
    params: {
      statut: filters.statut,      // EN_ATTENTE, VALIDE, REJETE
      locataire: filters.locataireId,
      search: filters.search,
      ordering: filters.ordering || '-created_at'
    }
  });
  return response.data;
};
```

#### Soumettre un paiement (Locataire)
```javascript
// POST /api/payments/paiements/
const soumettrePayement = async (paiementData, preuve) => {
  const formData = new FormData();
  formData.append('montant', paiementData.montant);
  formData.append('mode_paiement', paiementData.modePaiement);  // ESPECES, VIREMENT, MOBILE_MONEY, CHEQUE
  formData.append('reference_paiement', paiementData.reference);
  formData.append('description', paiementData.description);
  
  if (preuve) {
    formData.append('preuve_paiement', preuve);
  }
  
  const response = await api.post('/payments/paiements/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  return response.data;
};
```

#### Mes paiements (Locataire)
```javascript
// GET /api/payments/paiements/mes_paiements/
const getMesPaiements = async () => {
  const response = await api.get('/payments/paiements/mes_paiements/');
  return response.data.data;
};
```

#### Paiements en attente (Admin)
```javascript
// GET /api/payments/paiements/en_attente/
const getPaiementsEnAttente = async () => {
  const response = await api.get('/payments/paiements/en_attente/');
  return response.data.data;
};
```

#### Valider un paiement (Admin)
```javascript
// POST /api/payments/paiements/{id}/valider/
const validerPaiement = async (paiementId, commentaire = '') => {
  const response = await api.post(`/payments/paiements/${paiementId}/valider/`, {
    commentaire
  });
  return response.data;
};
```

#### Rejeter un paiement (Admin)
```javascript
// POST /api/payments/paiements/{id}/rejeter/
const rejeterPaiement = async (paiementId, raison) => {
  const response = await api.post(`/payments/paiements/${paiementId}/rejeter/`, {
    commentaire: raison
  });
  return response.data;
};
```

#### Statistiques des paiements (Admin)
```javascript
// GET /api/payments/paiements/statistiques/
const getStatistiquesPaiements = async (mois = null, annee = null) => {
  const response = await api.get('/payments/paiements/statistiques/', {
    params: { mois, annee }
  });
  return response.data.data;
};
```

### 2. Encaissement Direct (Admin uniquement)

#### Encaisser le loyer d'un locataire
```javascript
// POST /api/payments/encaissements/encaisser_loyer/
const encaisserLoyer = async (encaissementData) => {
  const response = await api.post('/payments/encaissements/encaisser_loyer/', {
    locataire_id: encaissementData.locataireId,
    mois: encaissementData.mois,
    annee: encaissementData.annee,
    montant: encaissementData.montant,
    mode_paiement: encaissementData.modePaiement || 'ESPECES',
    reference_paiement: encaissementData.reference || '',
    notes: encaissementData.notes || ''
  });
  return response.data;
};
```

#### Encaisser une facture spécifique
```javascript
// POST /api/payments/encaissements/encaisser_facture/
const encaisserFacture = async (factureId, montant, modePaiement = 'ESPECES') => {
  const response = await api.post('/payments/encaissements/encaisser_facture/', {
    facture_id: factureId,
    montant: montant,
    mode_paiement: modePaiement,
    reference_paiement: '',
    notes: ''
  });
  return response.data;
};
```

#### Encaisser plusieurs factures
```javascript
// POST /api/payments/encaissements/encaisser_multiple/
const encaisserMultiple = async (facturesIds, montantTotal, modePaiement = 'ESPECES') => {
  const response = await api.post('/payments/encaissements/encaisser_multiple/', {
    factures_ids: facturesIds,  // [1, 2, 3]
    montant_total: montantTotal,
    mode_paiement: modePaiement,
    reference_paiement: '',
    notes: ''
  });
  return response.data;
};
```

#### Factures impayées d'un locataire
```javascript
// GET /api/payments/encaissements/factures_impayees/
const getFacturesImpayees = async (locataireId) => {
  const response = await api.get('/payments/encaissements/factures_impayees/', {
    params: { locataire_id: locataireId }
  });
  return response.data.data;
};
```

#### Résumé des encaissements du mois
```javascript
// GET /api/payments/encaissements/resume_mois/
const getResumeEncaissements = async (mois, annee) => {
  const response = await api.get('/payments/encaissements/resume_mois/', {
    params: { mois, annee }
  });
  return response.data.data;
};
```

---

## Module Dépenses

### 1. Liste des dépenses
```javascript
// GET /api/expenses/
const getDepenses = async (filters = {}) => {
  const response = await api.get('/expenses/', {
    params: {
      categorie: filters.categorie,
      maison: filters.maisonId,
      date_debut: filters.dateDebut,
      date_fin: filters.dateFin,
      search: filters.search
    }
  });
  return response.data;
};
```

### 2. Créer une dépense (Admin)
```javascript
// POST /api/expenses/
const createDepense = async (depenseData) => {
  const formData = new FormData();
  formData.append('titre', depenseData.titre);
  formData.append('categorie', depenseData.categorie);
  formData.append('montant', depenseData.montant);
  formData.append('date_depense', depenseData.date);
  formData.append('description', depenseData.description);
  
  if (depenseData.maison) {
    formData.append('maison', depenseData.maison);
  }
  
  if (depenseData.recu) {
    formData.append('recu', depenseData.recu);
  }
  
  const response = await api.post('/expenses/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  return response.data;
};
```

### 3. Modifier/Supprimer une dépense
```javascript
// PATCH /api/expenses/{id}/
const updateDepense = async (depenseId, updates) => {
  const response = await api.patch(`/expenses/${depenseId}/`, updates);
  return response.data;
};

// DELETE /api/expenses/{id}/
const deleteDepense = async (depenseId) => {
  await api.delete(`/expenses/${depenseId}/`);
};
```

---

## Module Notifications

### 1. Liste des notifications
```javascript
// GET /api/notifications/
const getNotifications = async (filters = {}) => {
  const response = await api.get('/notifications/', {
    params: {
      type_notification: filters.type,  // INFO, ALERTE, SUCCES, ERREUR
      lu: filters.lu,                   // true/false
      page: filters.page || 1
    }
  });
  return response.data;
};
```

### 2. Notifications récentes
```javascript
// GET /api/notifications/recentes/
const getNotificationsRecentes = async () => {
  const response = await api.get('/notifications/recentes/');
  return response.data.data;
};
```

### 3. Nombre de notifications non lues
```javascript
// GET /api/notifications/non_lues/
const getCountNonLues = async () => {
  const response = await api.get('/notifications/non_lues/');
  return response.data.data.count;
};
```

### 4. Marquer une notification comme lue
```javascript
// POST /api/notifications/{id}/marquer_lue/
const marquerNotificationLue = async (notificationId) => {
  const response = await api.post(`/notifications/${notificationId}/marquer_lue/`);
  return response.data;
};
```

### 5. Marquer toutes les notifications comme lues
```javascript
// POST /api/notifications/marquer_toutes_lues/
const marquerToutesLues = async () => {
  const response = await api.post('/notifications/marquer_toutes_lues/');
  return response.data;
};
```

### 6. Supprimer les notifications lues
```javascript
// DELETE /api/notifications/supprimer_lues/
const supprimerNotificationsLues = async () => {
  const response = await api.delete('/notifications/supprimer_lues/');
  return response.data;
};
```

### 7. Envoyer une notification (Admin)
```javascript
// POST /api/notifications/envoyer/
const envoyerNotification = async (notificationData) => {
  const response = await api.post('/notifications/envoyer/', {
    destinataires: [userId1, userId2],  // Liste d'IDs
    titre: 'Titre de la notification',
    message: 'Message de la notification',
    type_notification: 'INFO'  // INFO, ALERTE, SUCCES, ERREUR
  });
  return response.data;
};
```

### 8. Envoyer à tous les locataires (Admin)
```javascript
// POST /api/notifications/envoyer_a_tous_locataires/
const envoyerATousLocataires = async (titre, message, type = 'INFO') => {
  const response = await api.post('/notifications/envoyer_a_tous_locataires/', {
    titre,
    message,
    type_notification: type
  });
  return response.data;
};
```

---

## Module Réservations

### 1. Liste des réservations
```javascript
// GET /api/reservations/
const getReservations = async (filters = {}) => {
  const response = await api.get('/reservations/', {
    params: {
      statut: filters.statut,  // EN_ATTENTE, CONFIRMEE, ANNULEE
      maison: filters.maisonId,
      utilisateur: filters.userId
    }
  });
  return response.data;
};
```

### 2. Créer une réservation
```javascript
// POST /api/reservations/
const createReservation = async (reservationData) => {
  const response = await api.post('/reservations/', {
    maison: maisonId,
    date_visite: '2026-04-15T10:00:00',
    message: 'Je souhaite visiter cette propriété'
  });
  return response.data;
};
```

### 3. Annuler/Confirmer une réservation
```javascript
// PATCH /api/reservations/{id}/
const updateReservation = async (reservationId, statut) => {
  const response = await api.patch(`/reservations/${reservationId}/`, {
    statut: statut  // CONFIRMEE, ANNULEE
  });
  return response.data;
};
```

---

## Dashboard

### 1. Dashboard Admin
```javascript
// GET /api/dashboard/admin/
const getDashboardAdmin = async () => {
  const response = await api.get('/dashboard/admin/');
  return response.data.data;
  /* Retour:
  {
    statistiques_generales: {
      total_maisons: 50,
      maisons_disponibles: 12,
      maisons_louees: 35,
      total_locataires: 40,
      taux_occupation: 85.5
    },
    revenus: {
      revenus_mois: 5250000,
      revenus_annee: 58750000,
      factures_impayees: 1250000,
      taux_recouvrement: 87.5
    },
    locations: {
      actives: 35,
      expirant_30j: 5,
      nouvelles_mois: 3
    },
    paiements: {
      en_attente: 8,
      valides_mois: 32,
      montant_valide_mois: 4500000
    }
  }
  */
};
```

### 2. Dashboard Locataire
```javascript
// GET /api/dashboard/locataire/
const getDashboardLocataire = async () => {
  const response = await api.get('/dashboard/locataire/');
  return response.data.data;
  /* Retour:
  {
    location: {
      maison_titre: "Belle Villa Angré",
      loyer_mensuel: 250000,
      date_debut: "2025-01-01",
      date_fin: "2026-01-01",
      jours_restants: 295
    },
    factures: {
      total_impayees: 250000,
      nombre_impayees: 1,
      prochaine_echeance: "2026-04-05"
    },
    paiements: {
      dernier_paiement: 250000,
      date_dernier_paiement: "2026-03-05",
      total_paye_annee: 750000
    },
    notifications_non_lues: 3
  }
  */
};
```

---

## Gestion des Erreurs

### Codes HTTP et Messages

```javascript
const handleApiError = (error) => {
  if (error.response) {
    // Le serveur a répondu avec un code d'erreur
    const status = error.response.status;
    const data = error.response.data;
    
    switch (status) {
      case 400:
        // Erreur de validation
        console.error('Erreurs de validation:', data.errors);
        return {
          type: 'validation',
          message: data.message || 'Données invalides',
          errors: data.errors
        };
        
      case 401:
        // Non authentifié
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return {
          type: 'auth',
          message: 'Session expirée, veuillez vous reconnecter'
        };
        
      case 403:
        // Non autorisé
        return {
          type: 'permission',
          message: 'Vous n\'avez pas la permission d\'effectuer cette action'
        };
        
      case 404:
        // Ressource non trouvée
        return {
          type: 'notfound',
          message: data.message || 'Ressource non trouvée'
        };
        
      case 500:
        // Erreur serveur
        return {
          type: 'server',
          message: 'Erreur serveur, veuillez réessayer plus tard'
        };
        
      default:
        return {
          type: 'unknown',
          message: data.message || 'Une erreur est survenue'
        };
    }
  } else if (error.request) {
    // La requête a été envoyée mais pas de réponse
    return {
      type: 'network',
      message: 'Erreur de connexion, vérifiez votre réseau'
    };
  } else {
    // Erreur lors de la préparation de la requête
    return {
      type: 'client',
      message: error.message
    };
  }
};

// Utilisation
try {
  const data = await getMaisons();
} catch (error) {
  const errorInfo = handleApiError(error);
  // Afficher l'erreur à l'utilisateur
  showNotification(errorInfo.message, 'error');
}
```

---

## Intégration WhatsApp

### Comment utiliser les liens WhatsApp

Les APIs retournent des liens WhatsApp au format `https://wa.me/2250700000000?text=Message`. L'admin doit cliquer sur ces liens pour ouvrir WhatsApp Web/App avec le message pré-rempli.

```javascript
// Exemple avec une facture
const envoyerFactureWhatsApp = async (factureId) => {
  try {
    // 1. Récupérer le lien WhatsApp
    const response = await getLienWhatsAppFacture(factureId);
    const { lien_whatsapp, telephone, message } = response;
    
    // 2. Ouvrir WhatsApp dans un nouvel onglet
    window.open(lien_whatsapp, '_blank');
    
    // 3. Afficher confirmation
    showNotification(
      `WhatsApp ouvert pour ${telephone}`,
      'success'
    );
  } catch (error) {
    handleApiError(error);
  }
};

// Exemple avec un bouton React
const WhatsAppButton = ({ factureId }) => {
  const handleClick = async () => {
    const response = await api.get(`/billing/factures/${factureId}/lien_whatsapp/`);
    window.open(response.data.data.lien_whatsapp, '_blank');
  };
  
  return (
    <button onClick={handleClick} className="btn-whatsapp">
      <WhatsAppIcon />
      Envoyer via WhatsApp
    </button>
  );
};

// Exemple avec plusieurs liens (boucle)
const envoyerTousLoyersWhatsApp = async (mois, annee) => {
  const response = await getLiensWhatsAppLoyers(mois, annee);
  const { locataires } = response;
  
  // Afficher une liste de boutons
  locataires.forEach(locataire => {
    console.log(`${locataire.nom}: ${locataire.lien}`);
    // L'admin clique sur chaque lien pour envoyer individuellement
  });
};
```

### Composant React pour WhatsApp
```jsx
import React from 'react';
import { FaWhatsapp } from 'react-icons/fa';

const WhatsAppLink = ({ telephone, message, label = "Envoyer" }) => {
  const encodedMessage = encodeURIComponent(message);
  const cleanPhone = telephone.replace(/\s+/g, '');
  const whatsappUrl = `https://wa.me/${cleanPhone}?text=${encodedMessage}`;
  
  return (
    <a 
      href={whatsappUrl} 
      target="_blank" 
      rel="noopener noreferrer"
      className="whatsapp-link"
    >
      <FaWhatsapp /> {label}
    </a>
  );
};

// Utilisation
<WhatsAppLink 
  telephone="+2250700000000"
  message="Bonjour, voici votre facture..."
  label="Envoyer via WhatsApp"
/>
```

---

## Téléchargement PDF

### Gestion des fichiers PDF

```javascript
// Fonction générique pour télécharger un PDF
const downloadPDF = async (url, filename) => {
  try {
    const response = await api.get(url, {
      responseType: 'blob'
    });
    
    // Créer un blob URL
    const blob = new Blob([response.data], { type: 'application/pdf' });
    const blobUrl = window.URL.createObjectURL(blob);
    
    // Créer un lien de téléchargement
    const link = document.createElement('a');
    link.href = blobUrl;
    link.download = filename;
    document.body.appendChild(link);
    
    // Déclencher le téléchargement
    link.click();
    
    // Nettoyer
    document.body.removeChild(link);
    window.URL.revokeObjectURL(blobUrl);
    
    showNotification('PDF téléchargé avec succès', 'success');
  } catch (error) {
    handleApiError(error);
  }
};

// Composant React pour télécharger une facture
const DownloadFactureButton = ({ factureId, reference }) => {
  const handleDownload = () => {
    downloadPDF(
      `/billing/factures/${factureId}/telecharger_pdf/`,
      `facture_${reference}.pdf`
    );
  };
  
  return (
    <button onClick={handleDownload} className="btn-download">
      <DownloadIcon /> Télécharger PDF
    </button>
  );
};

// Télécharger le rapport mensuel
const DownloadRapportMensuel = ({ mois, annee }) => {
  const handleDownload = () => {
    downloadPDF(
      `/billing/factures/rapport_mensuel/?mois=${mois}&annee=${annee}`,
      `rapport_${mois}_${annee}.pdf`
    );
  };
  
  return (
    <button onClick={handleDownload}>
      Télécharger Rapport {mois}/{annee}
    </button>
  );
};

// Prévisualiser le PDF dans un iframe
const PdfPreview = ({ factureId }) => {
  const [pdfUrl, setPdfUrl] = useState(null);
  
  useEffect(() => {
    const loadPdf = async () => {
      const response = await api.get(
        `/billing/factures/${factureId}/telecharger_pdf/`,
        { responseType: 'blob' }
      );
      
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      setPdfUrl(url);
    };
    
    loadPdf();
    
    return () => {
      if (pdfUrl) window.URL.revokeObjectURL(pdfUrl);
    };
  }, [factureId]);
  
  return pdfUrl ? (
    <iframe 
      src={pdfUrl} 
      width="100%" 
      height="600px" 
      title="Facture PDF"
    />
  ) : (
    <p>Chargement du PDF...</p>
  );
};
```

---

## Exemples d'Intégration Complète

### Exemple 1: Page de facturation admin

```jsx
import React, { useState, useEffect } from 'react';
import api from './api';

const FacturationPage = () => {
  const [factures, setFactures] = useState([]);
  const [mois, setMois] = useState(new Date().getMonth() + 1);
  const [annee, setAnnee] = useState(new Date().getFullYear());
  const [loading, setLoading] = useState(false);
  
  // Charger les factures
  useEffect(() => {
    loadFactures();
  }, [mois, annee]);
  
  const loadFactures = async () => {
    setLoading(true);
    try {
      const response = await api.get('/billing/factures/', {
        params: { mois, annee }
      });
      setFactures(response.data.data.results || response.data.data);
    } catch (error) {
      console.error('Erreur:', error);
    } finally {
      setLoading(false);
    }
  };
  
  // Envoyer par WhatsApp
  const envoyerWhatsApp = async (factureId) => {
    try {
      const response = await api.get(`/billing/factures/${factureId}/lien_whatsapp/`);
      window.open(response.data.data.lien_whatsapp, '_blank');
    } catch (error) {
      console.error('Erreur WhatsApp:', error);
    }
  };
  
  // Télécharger PDF
  const telechargerPDF = async (factureId, reference) => {
    try {
      const response = await api.get(
        `/billing/factures/${factureId}/telecharger_pdf/`,
        { responseType: 'blob' }
      );
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.download = `facture_${reference}.pdf`;
      link.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Erreur PDF:', error);
    }
  };
  
  // Envoyer par email
  const envoyerEmail = async (factureId) => {
    try {
      await api.post(`/billing/factures/${factureId}/envoyer_notification/`, {
        canaux: ['email']
      });
      alert('Email envoyé avec succès');
    } catch (error) {
      console.error('Erreur email:', error);
    }
  };
  
  return (
    <div className="facturation-page">
      <h1>Gestion des Factures</h1>
      
      {/* Filtres */}
      <div className="filters">
        <select value={mois} onChange={(e) => setMois(e.target.value)}>
          {[...Array(12)].map((_, i) => (
            <option key={i+1} value={i+1}>
              {new Date(2000, i).toLocaleString('fr-FR', { month: 'long' })}
            </option>
          ))}
        </select>
        
        <input 
          type="number" 
          value={annee} 
          onChange={(e) => setAnnee(e.target.value)}
        />
        
        <button onClick={loadFactures}>Rechercher</button>
      </div>
      
      {/* Liste des factures */}
      {loading ? <p>Chargement...</p> : (
        <table className="factures-table">
          <thead>
            <tr>
              <th>Référence</th>
              <th>Locataire</th>
              <th>Type</th>
              <th>Montant</th>
              <th>Statut</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {factures.map(facture => (
              <tr key={facture.id}>
                <td>{facture.reference}</td>
                <td>{facture.locataire_nom}</td>
                <td>{facture.type_facture}</td>
                <td>{facture.montant} FCFA</td>
                <td>
                  <span className={`badge badge-${facture.statut.toLowerCase()}`}>
                    {facture.statut}
                  </span>
                </td>
                <td>
                  <button onClick={() => envoyerWhatsApp(facture.id)}>
                    📱 WhatsApp
                  </button>
                  <button onClick={() => envoyerEmail(facture.id)}>
                    ✉️ Email
                  </button>
                  <button onClick={() => telechargerPDF(facture.id, facture.reference)}>
                    📄 PDF
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
};

export default FacturationPage;
```

### Exemple 2: Dashboard Locataire

```jsx
import React, { useState, useEffect } from 'react';
import api from './api';

const DashboardLocataire = () => {
  const [dashboard, setDashboard] = useState(null);
  const [factures, setFactures] = useState([]);
  const [paiements, setPaiements] = useState([]);
  
  useEffect(() => {
    loadDashboard();
    loadFactures();
    loadPaiements();
  }, []);
  
  const loadDashboard = async () => {
    const response = await api.get('/dashboard/locataire/');
    setDashboard(response.data.data);
  };
  
  const loadFactures = async () => {
    const response = await api.get('/billing/factures/');
    setFactures(response.data.data.results || response.data.data);
  };
  
  const loadPaiements = async () => {
    const response = await api.get('/payments/paiements/mes_paiements/');
    setPaiements(response.data.data);
  };
  
  const soumettrePayement = async (factureId, montant, preuve) => {
    const formData = new FormData();
    formData.append('montant', montant);
    formData.append('mode_paiement', 'MOBILE_MONEY');
    formData.append('description', `Paiement facture ${factureId}`);
    formData.append('preuve_paiement', preuve);
    
    try {
      await api.post('/payments/paiements/', formData);
      alert('Paiement soumis avec succès, en attente de validation');
      loadPaiements();
    } catch (error) {
      alert('Erreur lors de la soumission');
    }
  };
  
  if (!dashboard) return <p>Chargement...</p>;
  
  return (
    <div className="dashboard-locataire">
      <h1>Mon Tableau de Bord</h1>
      
      {/* Statistiques */}
      <div className="stats-grid">
        <div className="stat-card">
          <h3>Ma Location</h3>
          <p>{dashboard.location.maison_titre}</p>
          <p>Loyer: {dashboard.location.loyer_mensuel} FCFA</p>
          <p>Expire dans: {dashboard.location.jours_restants} jours</p>
        </div>
        
        <div className="stat-card alert">
          <h3>Factures Impayées</h3>
          <p className="big-number">{dashboard.factures.total_impayees} FCFA</p>
          <p>{dashboard.factures.nombre_impayees} facture(s)</p>
        </div>
        
        <div className="stat-card">
          <h3>Dernier Paiement</h3>
          <p>{dashboard.paiements.dernier_paiement} FCFA</p>
          <p>{new Date(dashboard.paiements.date_dernier_paiement).toLocaleDateString('fr-FR')}</p>
        </div>
      </div>
      
      {/* Factures impayées */}
      <div className="factures-impayees">
        <h2>Factures à Payer</h2>
        {factures.filter(f => f.statut !== 'PAYEE').map(facture => (
          <div key={facture.id} className="facture-card">
            <div>
              <h4>{facture.type_facture} - {facture.mois}/{facture.annee}</h4>
              <p>Montant: {facture.montant_restant || facture.montant} FCFA</p>
              <p>Échéance: {new Date(facture.date_echeance).toLocaleDateString('fr-FR')}</p>
            </div>
            <button onClick={() => {
              const input = document.createElement('input');
              input.type = 'file';
              input.onchange = (e) => soumettrePayement(
                facture.id, 
                facture.montant_restant || facture.montant,
                e.target.files[0]
              );
              input.click();
            }}>
              Soumettre Paiement
            </button>
          </div>
        ))}
      </div>
      
      {/* Historique paiements */}
      <div className="historique-paiements">
        <h2>Mes Paiements</h2>
        <table>
          <thead>
            <tr>
              <th>Date</th>
              <th>Montant</th>
              <th>Mode</th>
              <th>Statut</th>
            </tr>
          </thead>
          <tbody>
            {paiements.map(paiement => (
              <tr key={paiement.id}>
                <td>{new Date(paiement.created_at).toLocaleDateString('fr-FR')}</td>
                <td>{paiement.montant} FCFA</td>
                <td>{paiement.mode_paiement}</td>
                <td>
                  <span className={`badge badge-${paiement.statut.toLowerCase()}`}>
                    {paiement.statut}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default DashboardLocataire;
```

---

## Résumé des Endpoints

### Authentification (9 endpoints)
- `POST /api/auth/register/` - Inscription
- `POST /api/auth/login/` - Connexion
- `POST /api/auth/logout/` - Déconnexion
- `POST /api/auth/token/refresh/` - Rafraîchir token
- `POST /api/auth/password-reset/` - Demande réinitialisation
- `POST /api/auth/password-reset/confirm/` - Confirmer réinitialisation
- `POST /api/auth/password-change/` - Changer mot de passe
- `GET /api/auth/verify-email/{uid}/{token}/` - Vérifier email
- `POST /api/auth/google/` - Connexion Google

### Utilisateurs (10 endpoints)
- `GET /api/users/` - Liste utilisateurs
- `POST /api/users/` - Créer utilisateur
- `GET /api/users/{id}/` - Détails utilisateur
- `PATCH /api/users/{id}/` - Modifier utilisateur
- `DELETE /api/users/{id}/` - Supprimer utilisateur
- `GET /api/users/me/` - Mon profil
- `POST /api/users/change_password/` - Changer mot de passe
- `PATCH /api/users/{id}/update_status/` - Modifier statut
- `GET /api/users/locataires/` - Liste locataires
- `GET/PATCH /api/users/{id}/profile/` - Profil utilisateur

### Propriétés (12 endpoints)
- `GET /api/properties/maisons/` - Liste maisons
- `POST /api/properties/maisons/` - Créer maison
- `GET /api/properties/maisons/{id}/` - Détails maison
- `PATCH /api/properties/maisons/{id}/` - Modifier maison
- `DELETE /api/properties/maisons/{id}/` - Supprimer maison
- `GET /api/properties/maisons/disponibles/` - Maisons disponibles
- `PATCH /api/properties/maisons/{id}/changer_statut/` - Changer statut
- `POST /api/properties/maisons/{id}/ajouter_images/` - Ajouter images
- `GET /api/properties/maisons/{id}/images/` - Images d'une maison
- `GET /api/properties/images/` - Toutes les images
- `DELETE /api/properties/images/{id}/` - Supprimer image
- `PATCH /api/properties/images/{id}/definir_principale/` - Image principale

### Locations (11 endpoints)
- `GET /api/rentals/` - Liste locations
- `POST /api/rentals/` - Créer location
- `GET /api/rentals/{id}/` - Détails location
- `PATCH /api/rentals/{id}/` - Modifier location
- `DELETE /api/rentals/{id}/` - Supprimer location
- `GET /api/rentals/ma_location/` - Ma location
- `POST /api/rentals/{id}/renouveler/` - Renouveler
- `POST /api/rentals/{id}/resilier/` - Résilier
- `GET /api/rentals/actives/` - Locations actives
- `GET /api/rentals/expirant/` - Locations expirant
- `GET /api/rentals/statistiques/` - Statistiques

### Facturation (28 endpoints)
**Compteurs (6):**
- `GET /api/billing/compteurs/` - Liste compteurs
- `POST /api/billing/compteurs/` - Créer compteur
- `PATCH /api/billing/compteurs/{id}/` - Modifier compteur
- `POST /api/billing/compteurs/assigner/` - Assigner compteur
- `POST /api/billing/compteurs/{id}/liberer/` - Libérer compteur
- `GET /api/billing/compteurs/par_locataire/` - Compteurs d'un locataire

**Index Compteurs (3):**
- `GET /api/billing/index-compteurs/` - Liste index
- `POST /api/billing/index-compteurs/` - Créer index
- `PATCH /api/billing/index-compteurs/{id}/` - Modifier index

**Factures (9):**
- `GET /api/billing/factures/` - Liste factures
- `POST /api/billing/factures/` - Créer facture
- `GET /api/billing/factures/{id}/` - Détails facture
- `POST /api/billing/factures/repartir/` - Répartir SODECI/CIE
- `POST /api/billing/factures/{id}/envoyer_notification/` - Envoyer notification
- `GET /api/billing/factures/{id}/lien_whatsapp/` - Lien WhatsApp
- `GET /api/billing/factures/liens_whatsapp_mois/` - Liens WhatsApp mois
- `GET /api/billing/factures/{id}/telecharger_pdf/` - PDF facture
- `GET /api/billing/factures/rapport_mensuel/` - PDF rapport mensuel

**Factures Collectives (3):**
- `GET /api/billing/factures-collectives/` - Liste
- `POST /api/billing/factures-collectives/` - Créer
- `PATCH /api/billing/factures-collectives/{id}/` - Modifier

**Rappels Loyer (5):**
- `POST /api/billing/rappels-loyer/envoyer_whatsapp/` - WhatsApp
- `POST /api/billing/rappels-loyer/envoyer_email/` - Email
- `POST /api/billing/rappels-loyer/envoyer_tous_canaux/` - Tous canaux
- `GET /api/billing/rappels-loyer/liens_whatsapp_mois/` - Liens mois
- `POST /api/billing/rappels-loyer/envoyer_rappels_tous/` - Tous locataires

### Paiements (12 endpoints)
**Validation (7):**
- `GET /api/payments/paiements/` - Liste paiements
- `POST /api/payments/paiements/` - Soumettre paiement
- `GET /api/payments/paiements/{id}/` - Détails paiement
- `GET /api/payments/paiements/mes_paiements/` - Mes paiements
- `GET /api/payments/paiements/en_attente/` - En attente
- `POST /api/payments/paiements/{id}/valider/` - Valider
- `POST /api/payments/paiements/{id}/rejeter/` - Rejeter
- `GET /api/payments/paiements/statistiques/` - Statistiques

**Encaissement Direct (5):**
- `POST /api/payments/encaissements/encaisser_loyer/` - Encaisser loyer
- `POST /api/payments/encaissements/encaisser_facture/` - Encaisser facture
- `POST /api/payments/encaissements/encaisser_multiple/` - Encaisser multiple
- `GET /api/payments/encaissements/factures_impayees/` - Factures impayées
- `GET /api/payments/encaissements/resume_mois/` - Résumé mois

### Dépenses (5 endpoints)
- `GET /api/expenses/` - Liste dépenses
- `POST /api/expenses/` - Créer dépense
- `GET /api/expenses/{id}/` - Détails dépense
- `PATCH /api/expenses/{id}/` - Modifier dépense
- `DELETE /api/expenses/{id}/` - Supprimer dépense

### Notifications (10 endpoints)
- `GET /api/notifications/` - Liste notifications
- `GET /api/notifications/{id}/` - Détails notification
- `POST /api/notifications/{id}/marquer_lue/` - Marquer lue
- `POST /api/notifications/marquer_toutes_lues/` - Marquer toutes lues
- `GET /api/notifications/non_lues/` - Count non lues
- `GET /api/notifications/recentes/` - Récentes
- `POST /api/notifications/envoyer/` - Envoyer
- `POST /api/notifications/envoyer_a_tous_locataires/` - À tous locataires
- `DELETE /api/notifications/supprimer_lues/` - Supprimer lues
- `DELETE /api/notifications/{id}/` - Supprimer

### Réservations (5 endpoints)
- `GET /api/reservations/` - Liste réservations
- `POST /api/reservations/` - Créer réservation
- `GET /api/reservations/{id}/` - Détails réservation
- `PATCH /api/reservations/{id}/` - Modifier réservation
- `DELETE /api/reservations/{id}/` - Supprimer réservation

### Dashboard (2 endpoints)
- `GET /api/dashboard/admin/` - Dashboard admin
- `GET /api/dashboard/locataire/` - Dashboard locataire

---

## **TOTAL: 114 ENDPOINTS**

---

## Notes Importantes

1. **Authentification**: Toutes les requêtes (sauf login/register) nécessitent un token JWT dans le header `Authorization: Bearer {token}`

2. **Permissions**:
   - Admin: Accès complet
   - Locataire: Accès limité à ses propres données
   - Public: Uniquement liste des maisons disponibles

3. **Pagination**: La plupart des listes supportent la pagination avec `page` et `page_size`

4. **Filtres**: Utilisez les query params pour filtrer les résultats

5. **WhatsApp**: 100% gratuit, pas de configuration nécessaire, ouvre WhatsApp Web/App

6. **PDF**: Format Blob, utiliser `responseType: 'blob'` dans Axios

7. **Upload de fichiers**: Utiliser FormData avec `Content-Type: multipart/form-data`

8. **Dates**: Format ISO 8601: `YYYY-MM-DD` ou `YYYY-MM-DDTHH:MM:SS`

9. **Montants**: En FCFA (Francs CFA), format numérique

10. **Environnement**: Adapter `API_BASE_URL` selon l'environnement (dev/prod)

---

**Documentation générée pour l'API Gestion Locative v1.0.0**
**Date: Mars 2026**
