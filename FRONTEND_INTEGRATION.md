# Intégration Frontend - API Gestion Locative

## Configuration

### URL de l'API

```
https://gestion-locative-fqax.onrender.com/api
```

### Variable d'environnement (.env)

```env
VITE_API_URL=https://gestion-locative-fqax.onrender.com/api
```

---

## Inscription (Register)

### Endpoint

```
POST /api/auth/register/
```

### Données à envoyer

```json
{
  "email": "utilisateur@example.com",
  "telephone": "+225XXXXXXXXXX",
  "nom": "Dupont",
  "prenoms": "Jean",
  "password": "MotDePasse123",
  "password_confirm": "MotDePasse123",
  "adresse": "Abidjan, Cocody"
}
```

### Champs obligatoires

| Champ | Type | Validation |
|-------|------|------------|
| `email` | string | Format email valide, unique |
| `telephone` | string | Max 20 caractères, unique |
| `nom` | string | Max 100 caractères |
| `prenoms` | string | Max 100 caractères |
| `password` | string | Min 8 caractères, pas entièrement numérique |
| `password_confirm` | string | Doit correspondre à `password` |
| `adresse` | string | Optionnel |

### Validation du mot de passe

Le backend rejette les mots de passe qui :
- Ont moins de 8 caractères
- Sont entièrement numériques (ex: "12345678")
- Sont trop communs (ex: "password", "azerty123")
- Ressemblent trop à l'email ou au nom

### Réponse succès (201)

```json
{
  "success": true,
  "message": "Inscription réussie",
  "data": {
    "user": {
      "id": 1,
      "email": "utilisateur@example.com",
      "nom": "Dupont",
      "prenoms": "Jean",
      "telephone": "+225XXXXXXXXXX",
      "role": "LOCATAIRE"
    },
    "tokens": {
      "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
      "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    }
  }
}
```

### Réponse erreur (400)

```json
{
  "success": false,
  "message": "Erreur d'inscription",
  "errors": {
    "email": ["Un utilisateur avec cet email existe deja."],
    "password": ["Ce mot de passe est trop court. Il doit contenir au moins 8 caractères."]
  }
}
```

---

## Code Frontend

### Service API

```javascript
// src/services/api.js

const API_URL = import.meta.env.VITE_API_URL || 'https://gestion-locative-fqax.onrender.com/api';

export async function register(formData) {
  const response = await fetch(`${API_URL}/auth/register/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      email: formData.email.toLowerCase().trim(),
      telephone: formData.telephone.trim(),
      nom: formData.nom.trim(),
      prenoms: formData.prenoms.trim(),
      password: formData.password,
      password_confirm: formData.passwordConfirm,
      adresse: formData.adresse || ''
    })
  });

  const data = await response.json();

  if (!response.ok) {
    throw {
      message: data.message || "Erreur d'inscription",
      errors: data.errors || data.details || {}
    };
  }

  return data;
}

export async function login(email, password) {
  const response = await fetch(`${API_URL}/auth/login/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email, password })
  });

  const data = await response.json();

  if (!response.ok) {
    throw {
      message: data.message || "Erreur de connexion",
      errors: data.errors || {}
    };
  }

  return data;
}
```

### Validation Frontend

```javascript
// src/utils/validation.js

export function validateRegisterForm(formData) {
  const errors = {};

  // Email
  if (!formData.email) {
    errors.email = "L'email est requis";
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
    errors.email = "Format d'email invalide";
  }

  // Téléphone
  if (!formData.telephone) {
    errors.telephone = "Le téléphone est requis";
  } else if (formData.telephone.length > 20) {
    errors.telephone = "20 caractères maximum";
  }

  // Nom
  if (!formData.nom) {
    errors.nom = "Le nom est requis";
  }

  // Prénoms
  if (!formData.prenoms) {
    errors.prenoms = "Les prénoms sont requis";
  }

  // Mot de passe
  if (!formData.password) {
    errors.password = "Le mot de passe est requis";
  } else if (formData.password.length < 8) {
    errors.password = "Minimum 8 caractères";
  } else if (/^\d+$/.test(formData.password)) {
    errors.password = "Le mot de passe ne peut pas être entièrement numérique";
  }

  // Confirmation
  if (formData.password !== formData.passwordConfirm) {
    errors.passwordConfirm = "Les mots de passe ne correspondent pas";
  }

  return {
    isValid: Object.keys(errors).length === 0,
    errors
  };
}
```

### Composant React

```jsx
// src/components/RegisterForm.jsx

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { register } from '../services/api';
import { validateRegisterForm } from '../utils/validation';

export default function RegisterForm() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});
  const [formData, setFormData] = useState({
    email: '',
    telephone: '',
    nom: '',
    prenoms: '',
    password: '',
    passwordConfirm: '',
    adresse: ''
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    // Clear error on change
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: null }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrors({});

    // Validation frontend
    const validation = validateRegisterForm(formData);
    if (!validation.isValid) {
      setErrors(validation.errors);
      return;
    }

    setLoading(true);

    try {
      const result = await register(formData);

      // Stocker les tokens
      localStorage.setItem('accessToken', result.data.tokens.access);
      localStorage.setItem('refreshToken', result.data.tokens.refresh);
      localStorage.setItem('user', JSON.stringify(result.data.user));

      // Rediriger
      navigate('/dashboard');
    } catch (error) {
      // Mapper les erreurs backend
      if (error.errors) {
        const fieldErrors = {};
        Object.entries(error.errors).forEach(([field, messages]) => {
          fieldErrors[field] = Array.isArray(messages) ? messages[0] : messages;
        });
        setErrors(fieldErrors);
      } else {
        setErrors({ general: error.message || "Erreur d'inscription" });
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      {errors.general && (
        <div className="error-message">{errors.general}</div>
      )}

      <div>
        <label>Email *</label>
        <input
          type="email"
          name="email"
          value={formData.email}
          onChange={handleChange}
          required
        />
        {errors.email && <span className="error">{errors.email}</span>}
      </div>

      <div>
        <label>Téléphone *</label>
        <input
          type="tel"
          name="telephone"
          value={formData.telephone}
          onChange={handleChange}
          placeholder="+225XXXXXXXXXX"
          required
        />
        {errors.telephone && <span className="error">{errors.telephone}</span>}
      </div>

      <div>
        <label>Nom *</label>
        <input
          type="text"
          name="nom"
          value={formData.nom}
          onChange={handleChange}
          required
        />
        {errors.nom && <span className="error">{errors.nom}</span>}
      </div>

      <div>
        <label>Prénoms *</label>
        <input
          type="text"
          name="prenoms"
          value={formData.prenoms}
          onChange={handleChange}
          required
        />
        {errors.prenoms && <span className="error">{errors.prenoms}</span>}
      </div>

      <div>
        <label>Mot de passe *</label>
        <input
          type="password"
          name="password"
          value={formData.password}
          onChange={handleChange}
          placeholder="Min 8 caractères"
          required
        />
        {errors.password && <span className="error">{errors.password}</span>}
      </div>

      <div>
        <label>Confirmer le mot de passe *</label>
        <input
          type="password"
          name="passwordConfirm"
          value={formData.passwordConfirm}
          onChange={handleChange}
          required
        />
        {errors.passwordConfirm && <span className="error">{errors.passwordConfirm}</span>}
      </div>

      <div>
        <label>Adresse</label>
        <input
          type="text"
          name="adresse"
          value={formData.adresse}
          onChange={handleChange}
        />
      </div>

      <button type="submit" disabled={loading}>
        {loading ? 'Inscription...' : "S'inscrire"}
      </button>
    </form>
  );
}
```

---

## Connexion (Login)

### Endpoint

```
POST /api/auth/login/
```

### Données à envoyer

```json
{
  "email": "utilisateur@example.com",
  "password": "MotDePasse123"
}
```

### Réponse succès (200)

```json
{
  "success": true,
  "message": "Connexion réussie",
  "data": {
    "user": {
      "id": 1,
      "email": "utilisateur@example.com",
      "nom": "Dupont",
      "prenoms": "Jean",
      "role": "LOCATAIRE"
    },
    "tokens": {
      "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
      "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    }
  }
}
```

---

## Requêtes authentifiées

### Header Authorization

```javascript
const response = await fetch(`${API_URL}/endpoint/`, {
  method: 'GET',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
  }
});
```

### Rafraîchir le token

```
POST /api/auth/token/refresh/
```

```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

---

## Checklist

- [ ] Variable d'environnement `VITE_API_URL` configurée
- [ ] Utiliser `password_confirm` (pas `confirmPassword`)
- [ ] Mot de passe 8+ caractères
- [ ] Mot de passe pas entièrement numérique
- [ ] Stocker les tokens dans localStorage après connexion/inscription
- [ ] Envoyer le header `Authorization: Bearer <token>` pour les requêtes protégées
