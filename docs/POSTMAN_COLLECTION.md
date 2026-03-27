# Collection Postman - API Gestion Locative

## Import dans Postman

1. Ouvrez Postman
2. Cliquez sur **Import** (en haut à gauche)
3. Copiez le contenu JSON ci-dessous
4. Collez dans Postman
5. Cliquez sur **Import**

---

## Variables d'Environnement

Créez un environnement avec ces variables:

| Variable | Initial Value | Current Value |
|----------|---------------|---------------|
| `base_url` | `http://localhost:8000/api` | `http://localhost:8000/api` |
| `access_token` | `` | (automatiquement rempli après login) |
| `refresh_token` | `` | (automatiquement rempli après login) |
| `user_id` | `` | (automatiquement rempli après login) |
| `maison_id` | `1` | `1` |
| `locataire_id` | `1` | `1` |
| `facture_id` | `1` | `1` |

---

## Collection JSON (Copier-Coller dans Postman)

```json
{
  "info": {
    "name": "Gestion Locative API",
    "_postman_id": "gestion-locative-api",
    "description": "API complète pour la gestion locative - 114 endpoints",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "auth": {
    "type": "bearer",
    "bearer": [
      {
        "key": "token",
        "value": "{{access_token}}",
        "type": "string"
      }
    ]
  },
  "variable": [
    {
      "key": "base_url",
      "value": "http://localhost:8000/api",
      "type": "string"
    }
  ],
  "item": [
    {
      "name": "01. Authentification",
      "item": [
        {
          "name": "1. Inscription",
          "event": [
            {
              "listen": "test",
              "script": {
                "exec": [
                  "if (pm.response.code === 201) {",
                  "    const jsonData = pm.response.json();",
                  "    if (jsonData.data?.access) {",
                  "        pm.environment.set('access_token', jsonData.data.access);",
                  "        pm.environment.set('refresh_token', jsonData.data.refresh);",
                  "        pm.environment.set('user_id', jsonData.data.user.id);",
                  "    }",
                  "}"
                ],
                "type": "text/javascript"
              }
            }
          ],
          "request": {
            "auth": {
              "type": "noauth"
            },
            "method": "POST",
            "header": [],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"email\": \"locataire@example.com\",\n  \"password\": \"SecurePass123!\",\n  \"password2\": \"SecurePass123!\",\n  \"nom\": \"Kouassi\",\n  \"prenoms\": \"Jean\",\n  \"telephone\": \"+225 07 00 00 00 00\",\n  \"role\": \"LOCATAIRE\"\n}",
              "options": {
                "raw": {
                  "language": "json"
                }
              }
            },
            "url": {
              "raw": "{{base_url}}/auth/register/",
              "host": ["{{base_url}}"],
              "path": ["auth", "register", ""]
            }
          }
        },
        {
          "name": "2. Connexion",
          "event": [
            {
              "listen": "test",
              "script": {
                "exec": [
                  "if (pm.response.code === 200) {",
                  "    const jsonData = pm.response.json();",
                  "    pm.environment.set('access_token', jsonData.data.access);",
                  "    pm.environment.set('refresh_token', jsonData.data.refresh);",
                  "    pm.environment.set('user_id', jsonData.data.user.id);",
                  "    console.log('✅ Connecté avec succès');",
                  "}"
                ],
                "type": "text/javascript"
              }
            }
          ],
          "request": {
            "auth": {
              "type": "noauth"
            },
            "method": "POST",
            "header": [],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"email\": \"admin@example.com\",\n  \"password\": \"admin123\"\n}",
              "options": {
                "raw": {
                  "language": "json"
                }
              }
            },
            "url": {
              "raw": "{{base_url}}/auth/login/",
              "host": ["{{base_url}}"],
              "path": ["auth", "login", ""]
            }
          }
        },
        {
          "name": "3. Rafraîchir Token",
          "event": [
            {
              "listen": "test",
              "script": {
                "exec": [
                  "if (pm.response.code === 200) {",
                  "    const jsonData = pm.response.json();",
                  "    pm.environment.set('access_token', jsonData.access);",
                  "}"
                ],
                "type": "text/javascript"
              }
            }
          ],
          "request": {
            "auth": {
              "type": "noauth"
            },
            "method": "POST",
            "header": [],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"refresh\": \"{{refresh_token}}\"\n}",
              "options": {
                "raw": {
                  "language": "json"
                }
              }
            },
            "url": {
              "raw": "{{base_url}}/auth/token/refresh/",
              "host": ["{{base_url}}"],
              "path": ["auth", "token", "refresh", ""]
            }
          }
        },
        {
          "name": "4. Déconnexion",
          "request": {
            "method": "POST",
            "header": [],
            "url": {
              "raw": "{{base_url}}/auth/logout/",
              "host": ["{{base_url}}"],
              "path": ["auth", "logout", ""]
            }
          }
        },
        {
          "name": "5. Mot de passe oublié",
          "request": {
            "auth": {
              "type": "noauth"
            },
            "method": "POST",
            "header": [],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"email\": \"user@example.com\"\n}",
              "options": {
                "raw": {
                  "language": "json"
                }
              }
            },
            "url": {
              "raw": "{{base_url}}/auth/password-reset/",
              "host": ["{{base_url}}"],
              "path": ["auth", "password-reset", ""]
            }
          }
        },
        {
          "name": "6. Changer mot de passe",
          "request": {
            "method": "POST",
            "header": [],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"old_password\": \"OldPass123!\",\n  \"new_password\": \"NewPass123!\",\n  \"confirm_password\": \"NewPass123!\"\n}",
              "options": {
                "raw": {
                  "language": "json"
                }
              }
            },
            "url": {
              "raw": "{{base_url}}/auth/password-change/",
              "host": ["{{base_url}}"],
              "path": ["auth", "password-change", ""]
            }
          }
        }
      ]
    },
    {
      "name": "02. Utilisateurs",
      "item": [
        {
          "name": "1. Mon profil",
          "request": {
            "method": "GET",
            "header": [],
            "url": {
              "raw": "{{base_url}}/users/me/",
              "host": ["{{base_url}}"],
              "path": ["users", "me", ""]
            }
          }
        },
        {
          "name": "2. Liste utilisateurs",
          "request": {
            "method": "GET",
            "header": [],
            "url": {
              "raw": "{{base_url}}/users/?role=LOCATAIRE&statut=ACTIF&page=1&page_size=10",
              "host": ["{{base_url}}"],
              "path": ["users", ""],
              "query": [
                {"key": "role", "value": "LOCATAIRE"},
                {"key": "statut", "value": "ACTIF"},
                {"key": "page", "value": "1"},
                {"key": "page_size", "value": "10"}
              ]
            }
          }
        },
        {
          "name": "3. Créer utilisateur (Admin)",
          "request": {
            "method": "POST",
            "header": [],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"email\": \"nouveau@example.com\",\n  \"password\": \"SecurePass123!\",\n  \"nom\": \"Kouadio\",\n  \"prenoms\": \"Marie\",\n  \"telephone\": \"+225 07 11 22 33 44\",\n  \"role\": \"LOCATAIRE\",\n  \"date_naissance\": \"1995-05-15\",\n  \"lieu_naissance\": \"Abidjan\",\n  \"nationalite\": \"Ivoirienne\",\n  \"numero_piece\": \"CI987654\",\n  \"type_piece\": \"CNI\"\n}",
              "options": {
                "raw": {
                  "language": "json"
                }
              }
            },
            "url": {
              "raw": "{{base_url}}/users/",
              "host": ["{{base_url}}"],
              "path": ["users", ""]
            }
          }
        },
        {
          "name": "4. Liste locataires (Admin)",
          "request": {
            "method": "GET",
            "header": [],
            "url": {
              "raw": "{{base_url}}/users/locataires/",
              "host": ["{{base_url}}"],
              "path": ["users", "locataires", ""]
            }
          }
        }
      ]
    },
    {
      "name": "03. Propriétés",
      "item": [
        {
          "name": "1. Liste maisons",
          "request": {
            "auth": {
              "type": "noauth"
            },
            "method": "GET",
            "header": [],
            "url": {
              "raw": "{{base_url}}/properties/maisons/?statut=DISPONIBLE&commune=Cocody&min_prix=100000&max_prix=500000",
              "host": ["{{base_url}}"],
              "path": ["properties", "maisons", ""],
              "query": [
                {"key": "statut", "value": "DISPONIBLE"},
                {"key": "commune", "value": "Cocody"},
                {"key": "min_prix", "value": "100000"},
                {"key": "max_prix", "value": "500000"}
              ]
            }
          }
        },
        {
          "name": "2. Maisons disponibles",
          "request": {
            "auth": {
              "type": "noauth"
            },
            "method": "GET",
            "header": [],
            "url": {
              "raw": "{{base_url}}/properties/maisons/disponibles/",
              "host": ["{{base_url}}"],
              "path": ["properties", "maisons", "disponibles", ""]
            }
          }
        },
        {
          "name": "3. Détails maison",
          "request": {
            "auth": {
              "type": "noauth"
            },
            "method": "GET",
            "header": [],
            "url": {
              "raw": "{{base_url}}/properties/maisons/{{maison_id}}/",
              "host": ["{{base_url}}"],
              "path": ["properties", "maisons", "{{maison_id}}", ""]
            }
          }
        },
        {
          "name": "4. Créer maison (Admin)",
          "request": {
            "method": "POST",
            "header": [],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"titre\": \"Belle villa moderne à Cocody\",\n  \"description\": \"Magnifique villa de 3 chambres avec jardin dans un quartier calme\",\n  \"type_propriete\": \"VILLA\",\n  \"prix\": 350000,\n  \"commune\": \"Cocody\",\n  \"quartier\": \"Angré\",\n  \"adresse\": \"7ème tranche, lot 245\",\n  \"superficie\": 180.5,\n  \"nombre_chambres\": 3,\n  \"nombre_salles_bain\": 2,\n  \"nombre_salons\": 1,\n  \"meublee\": true,\n  \"equipements\": [\"Climatisation\", \"Cuisine équipée\", \"Parking\", \"Jardin\", \"Terrasse\"],\n  \"disponible_le\": \"2026-04-01\",\n  \"statut\": \"DISPONIBLE\"\n}",
              "options": {
                "raw": {
                  "language": "json"
                }
              }
            },
            "url": {
              "raw": "{{base_url}}/properties/maisons/",
              "host": ["{{base_url}}"],
              "path": ["properties", "maisons", ""]
            }
          }
        },
        {
          "name": "5. Changer statut (Admin)",
          "request": {
            "method": "PATCH",
            "header": [],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"statut\": \"LOUEE\"\n}",
              "options": {
                "raw": {
                  "language": "json"
                }
              }
            },
            "url": {
              "raw": "{{base_url}}/properties/maisons/{{maison_id}}/changer_statut/",
              "host": ["{{base_url}}"],
              "path": ["properties", "maisons", "{{maison_id}}", "changer_statut", ""]
            }
          }
        }
      ]
    },
    {
      "name": "04. Locations",
      "item": [
        {
          "name": "1. Ma location (Locataire)",
          "request": {
            "method": "GET",
            "header": [],
            "url": {
              "raw": "{{base_url}}/rentals/ma_location/",
              "host": ["{{base_url}}"],
              "path": ["rentals", "ma_location", ""]
            }
          }
        },
        {
          "name": "2. Liste locations",
          "request": {
            "method": "GET",
            "header": [],
            "url": {
              "raw": "{{base_url}}/rentals/?statut=ACTIVE",
              "host": ["{{base_url}}"],
              "path": ["rentals", ""],
              "query": [
                {"key": "statut", "value": "ACTIVE"}
              ]
            }
          }
        },
        {
          "name": "3. Créer location (Admin)",
          "request": {
            "method": "POST",
            "header": [],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"locataire\": {{locataire_id}},\n  \"maison\": {{maison_id}},\n  \"date_debut\": \"2026-04-01\",\n  \"duree_mois\": 12,\n  \"loyer_mensuel\": 250000,\n  \"caution\": 500000,\n  \"avance_loyer_mois\": 2,\n  \"frais_agence\": 50000,\n  \"charges_mensuelles\": 15000,\n  \"conditions_particulieres\": \"Entretien du jardin à la charge du locataire\"\n}",
              "options": {
                "raw": {
                  "language": "json"
                }
              }
            },
            "url": {
              "raw": "{{base_url}}/rentals/",
              "host": ["{{base_url}}"],
              "path": ["rentals", ""]
            }
          }
        },
        {
          "name": "4. Locations actives (Admin)",
          "request": {
            "method": "GET",
            "header": [],
            "url": {
              "raw": "{{base_url}}/rentals/actives/",
              "host": ["{{base_url}}"],
              "path": ["rentals", "actives", ""]
            }
          }
        },
        {
          "name": "5. Statistiques (Admin)",
          "request": {
            "method": "GET",
            "header": [],
            "url": {
              "raw": "{{base_url}}/rentals/statistiques/",
              "host": ["{{base_url}}"],
              "path": ["rentals", "statistiques", ""]
            }
          }
        }
      ]
    },
    {
      "name": "05. Facturation - Compteurs",
      "item": [
        {
          "name": "1. Liste compteurs",
          "request": {
            "method": "GET",
            "header": [],
            "url": {
              "raw": "{{base_url}}/billing/compteurs/?maison={{maison_id}}&type=SODECI",
              "host": ["{{base_url}}"],
              "path": ["billing", "compteurs", ""],
              "query": [
                {"key": "maison", "value": "{{maison_id}}"},
                {"key": "type", "value": "SODECI"}
              ]
            }
          }
        },
        {
          "name": "2. Créer compteur (Admin)",
          "request": {
            "method": "POST",
            "header": [],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"numero\": \"SODECI-2026-001\",\n  \"type_compteur\": \"SODECI\",\n  \"maison\": {{maison_id}},\n  \"dernier_index\": 0,\n  \"date_installation\": \"2026-03-01\",\n  \"actif\": true\n}",
              "options": {
                "raw": {
                  "language": "json"
                }
              }
            },
            "url": {
              "raw": "{{base_url}}/billing/compteurs/",
              "host": ["{{base_url}}"],
              "path": ["billing", "compteurs", ""]
            }
          }
        },
        {
          "name": "3. Assigner compteur (Admin)",
          "request": {
            "method": "POST",
            "header": [],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"compteur_id\": 1,\n  \"locataire_id\": {{locataire_id}},\n  \"index_initial\": 1000\n}",
              "options": {
                "raw": {
                  "language": "json"
                }
              }
            },
            "url": {
              "raw": "{{base_url}}/billing/compteurs/assigner/",
              "host": ["{{base_url}}"],
              "path": ["billing", "compteurs", "assigner", ""]
            }
          }
        },
        {
          "name": "4. Compteurs d'un locataire",
          "request": {
            "method": "GET",
            "header": [],
            "url": {
              "raw": "{{base_url}}/billing/compteurs/par_locataire/?locataire_id={{locataire_id}}",
              "host": ["{{base_url}}"],
              "path": ["billing", "compteurs", "par_locataire", ""],
              "query": [
                {"key": "locataire_id", "value": "{{locataire_id}}"}
              ]
            }
          }
        }
      ]
    },
    {
      "name": "06. Facturation - Factures",
      "item": [
        {
          "name": "1. Liste factures",
          "request": {
            "method": "GET",
            "header": [],
            "url": {
              "raw": "{{base_url}}/billing/factures/?mois=3&annee=2026&type_facture=LOYER&statut=IMPAYEE",
              "host": ["{{base_url}}"],
              "path": ["billing", "factures", ""],
              "query": [
                {"key": "mois", "value": "3"},
                {"key": "annee", "value": "2026"},
                {"key": "type_facture", "value": "LOYER"},
                {"key": "statut", "value": "IMPAYEE"}
              ]
            }
          }
        },
        {
          "name": "2. Créer facture (Admin)",
          "request": {
            "method": "POST",
            "header": [],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"locataire\": {{locataire_id}},\n  \"type_facture\": \"LOYER\",\n  \"mois\": 3,\n  \"annee\": 2026,\n  \"montant\": 250000,\n  \"date_echeance\": \"2026-04-05\",\n  \"description\": \"Loyer du mois de Mars 2026\"\n}",
              "options": {
                "raw": {
                  "language": "json"
                }
              }
            },
            "url": {
              "raw": "{{base_url}}/billing/factures/",
              "host": ["{{base_url}}"],
              "path": ["billing", "factures", ""]
            }
          }
        },
        {
          "name": "3. Répartir facture SODECI/CIE",
          "request": {
            "method": "POST",
            "header": [],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"mois\": 3,\n  \"annee\": 2026,\n  \"montant_sodeci\": 50000,\n  \"montant_cie\": 75000\n}",
              "options": {
                "raw": {
                  "language": "json"
                }
              }
            },
            "url": {
              "raw": "{{base_url}}/billing/factures/repartir/",
              "host": ["{{base_url}}"],
              "path": ["billing", "factures", "repartir", ""]
            }
          }
        },
        {
          "name": "4. Lien WhatsApp facture",
          "request": {
            "method": "GET",
            "header": [],
            "url": {
              "raw": "{{base_url}}/billing/factures/{{facture_id}}/lien_whatsapp/",
              "host": ["{{base_url}}"],
              "path": ["billing", "factures", "{{facture_id}}", "lien_whatsapp", ""]
            }
          }
        },
        {
          "name": "5. Liens WhatsApp du mois",
          "request": {
            "method": "GET",
            "header": [],
            "url": {
              "raw": "{{base_url}}/billing/factures/liens_whatsapp_mois/?mois=3&annee=2026&type=LOYER",
              "host": ["{{base_url}}"],
              "path": ["billing", "factures", "liens_whatsapp_mois", ""],
              "query": [
                {"key": "mois", "value": "3"},
                {"key": "annee", "value": "2026"},
                {"key": "type", "value": "LOYER"}
              ]
            }
          }
        },
        {
          "name": "6. Envoyer notification",
          "request": {
            "method": "POST",
            "header": [],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"canaux\": [\"email\", \"app\", \"whatsapp\"]\n}",
              "options": {
                "raw": {
                  "language": "json"
                }
              }
            },
            "url": {
              "raw": "{{base_url}}/billing/factures/{{facture_id}}/envoyer_notification/",
              "host": ["{{base_url}}"],
              "path": ["billing", "factures", "{{facture_id}}", "envoyer_notification", ""]
            }
          }
        },
        {
          "name": "7. Télécharger PDF facture",
          "request": {
            "method": "GET",
            "header": [],
            "url": {
              "raw": "{{base_url}}/billing/factures/{{facture_id}}/telecharger_pdf/",
              "host": ["{{base_url}}"],
              "path": ["billing", "factures", "{{facture_id}}", "telecharger_pdf", ""]
            }
          }
        },
        {
          "name": "8. Rapport mensuel PDF",
          "request": {
            "method": "GET",
            "header": [],
            "url": {
              "raw": "{{base_url}}/billing/factures/rapport_mensuel/?mois=3&annee=2026",
              "host": ["{{base_url}}"],
              "path": ["billing", "factures", "rapport_mensuel", ""],
              "query": [
                {"key": "mois", "value": "3"},
                {"key": "annee", "value": "2026"}
              ]
            }
          }
        }
      ]
    },
    {
      "name": "07. Facturation - Rappels Loyer",
      "item": [
        {
          "name": "1. Rappel WhatsApp",
          "request": {
            "method": "POST",
            "header": [],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"locataire_id\": {{locataire_id}},\n  \"montant\": 250000,\n  \"mois\": 3,\n  \"annee\": 2026\n}",
              "options": {
                "raw": {
                  "language": "json"
                }
              }
            },
            "url": {
              "raw": "{{base_url}}/billing/rappels-loyer/envoyer_whatsapp/",
              "host": ["{{base_url}}"],
              "path": ["billing", "rappels-loyer", "envoyer_whatsapp", ""]
            }
          }
        },
        {
          "name": "2. Rappel Email",
          "request": {
            "method": "POST",
            "header": [],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"locataire_id\": {{locataire_id}},\n  \"montant\": 250000,\n  \"mois\": 3,\n  \"annee\": 2026\n}",
              "options": {
                "raw": {
                  "language": "json"
                }
              }
            },
            "url": {
              "raw": "{{base_url}}/billing/rappels-loyer/envoyer_email/",
              "host": ["{{base_url}}"],
              "path": ["billing", "rappels-loyer", "envoyer_email", ""]
            }
          }
        },
        {
          "name": "3. Rappel tous canaux",
          "request": {
            "method": "POST",
            "header": [],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"locataire_id\": {{locataire_id}},\n  \"montant\": 250000,\n  \"mois\": 3,\n  \"annee\": 2026,\n  \"canaux\": [\"email\", \"whatsapp\"]\n}",
              "options": {
                "raw": {
                  "language": "json"
                }
              }
            },
            "url": {
              "raw": "{{base_url}}/billing/rappels-loyer/envoyer_tous_canaux/",
              "host": ["{{base_url}}"],
              "path": ["billing", "rappels-loyer", "envoyer_tous_canaux", ""]
            }
          }
        },
        {
          "name": "4. Liens WhatsApp loyers mois",
          "request": {
            "method": "GET",
            "header": [],
            "url": {
              "raw": "{{base_url}}/billing/rappels-loyer/liens_whatsapp_mois/?mois=3&annee=2026",
              "host": ["{{base_url}}"],
              "path": ["billing", "rappels-loyer", "liens_whatsapp_mois", ""],
              "query": [
                {"key": "mois", "value": "3"},
                {"key": "annee", "value": "2026"}
              ]
            }
          }
        },
        {
          "name": "5. Rappels à tous",
          "request": {
            "method": "POST",
            "header": [],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"mois\": 3,\n  \"annee\": 2026,\n  \"canaux\": [\"email\", \"whatsapp\"]\n}",
              "options": {
                "raw": {
                  "language": "json"
                }
              }
            },
            "url": {
              "raw": "{{base_url}}/billing/rappels-loyer/envoyer_rappels_tous/",
              "host": ["{{base_url}}"],
              "path": ["billing", "rappels-loyer", "envoyer_rappels_tous", ""]
            }
          }
        }
      ]
    },
    {
      "name": "08. Paiements - Validation",
      "item": [
        {
          "name": "1. Mes paiements (Locataire)",
          "request": {
            "method": "GET",
            "header": [],
            "url": {
              "raw": "{{base_url}}/payments/paiements/mes_paiements/",
              "host": ["{{base_url}}"],
              "path": ["payments", "paiements", "mes_paiements", ""]
            }
          }
        },
        {
          "name": "2. Soumettre paiement (Locataire)",
          "request": {
            "method": "POST",
            "header": [],
            "body": {
              "mode": "formdata",
              "formdata": [
                {"key": "montant", "value": "250000", "type": "text"},
                {"key": "mode_paiement", "value": "MOBILE_MONEY", "type": "text"},
                {"key": "reference_paiement", "value": "MTN-20260315-001", "type": "text"},
                {"key": "description", "value": "Paiement loyer mars 2026", "type": "text"},
                {"key": "preuve_paiement", "type": "file", "src": []}
              ]
            },
            "url": {
              "raw": "{{base_url}}/payments/paiements/",
              "host": ["{{base_url}}"],
              "path": ["payments", "paiements", ""]
            }
          }
        },
        {
          "name": "3. Paiements en attente (Admin)",
          "request": {
            "method": "GET",
            "header": [],
            "url": {
              "raw": "{{base_url}}/payments/paiements/en_attente/",
              "host": ["{{base_url}}"],
              "path": ["payments", "paiements", "en_attente", ""]
            }
          }
        },
        {
          "name": "4. Valider paiement (Admin)",
          "request": {
            "method": "POST",
            "header": [],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"commentaire\": \"Paiement confirmé, merci\"\n}",
              "options": {
                "raw": {
                  "language": "json"
                }
              }
            },
            "url": {
              "raw": "{{base_url}}/payments/paiements/1/valider/",
              "host": ["{{base_url}}"],
              "path": ["payments", "paiements", "1", "valider", ""]
            }
          }
        },
        {
          "name": "5. Rejeter paiement (Admin)",
          "request": {
            "method": "POST",
            "header": [],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"commentaire\": \"Montant incorrect, veuillez vérifier\"\n}",
              "options": {
                "raw": {
                  "language": "json"
                }
              }
            },
            "url": {
              "raw": "{{base_url}}/payments/paiements/1/rejeter/",
              "host": ["{{base_url}}"],
              "path": ["payments", "paiements", "1", "rejeter", ""]
            }
          }
        },
        {
          "name": "6. Statistiques (Admin)",
          "request": {
            "method": "GET",
            "header": [],
            "url": {
              "raw": "{{base_url}}/payments/paiements/statistiques/?mois=3&annee=2026",
              "host": ["{{base_url}}"],
              "path": ["payments", "paiements", "statistiques", ""],
              "query": [
                {"key": "mois", "value": "3"},
                {"key": "annee", "value": "2026"}
              ]
            }
          }
        }
      ]
    },
    {
      "name": "09. Paiements - Encaissement Direct",
      "item": [
        {
          "name": "1. Encaisser loyer (Admin)",
          "request": {
            "method": "POST",
            "header": [],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"locataire_id\": {{locataire_id}},\n  \"mois\": 3,\n  \"annee\": 2026,\n  \"montant\": 250000,\n  \"mode_paiement\": \"ESPECES\",\n  \"reference_paiement\": \"\",\n  \"notes\": \"Paiement reçu en espèces\"\n}",
              "options": {
                "raw": {
                  "language": "json"
                }
              }
            },
            "url": {
              "raw": "{{base_url}}/payments/encaissements/encaisser_loyer/",
              "host": ["{{base_url}}"],
              "path": ["payments", "encaissements", "encaisser_loyer", ""]
            }
          }
        },
        {
          "name": "2. Encaisser facture (Admin)",
          "request": {
            "method": "POST",
            "header": [],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"facture_id\": {{facture_id}},\n  \"montant\": 250000,\n  \"mode_paiement\": \"VIREMENT\",\n  \"reference_paiement\": \"VIR-2026-03-15\",\n  \"notes\": \"Virement bancaire\"\n}",
              "options": {
                "raw": {
                  "language": "json"
                }
              }
            },
            "url": {
              "raw": "{{base_url}}/payments/encaissements/encaisser_facture/",
              "host": ["{{base_url}}"],
              "path": ["payments", "encaissements", "encaisser_facture", ""]
            }
          }
        },
        {
          "name": "3. Encaisser multiple (Admin)",
          "request": {
            "method": "POST",
            "header": [],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"factures_ids\": [1, 2, 3],\n  \"montant_total\": 500000,\n  \"mode_paiement\": \"CHEQUE\",\n  \"reference_paiement\": \"CHQ-20260315-001\",\n  \"notes\": \"Paiement groupé par chèque\"\n}",
              "options": {
                "raw": {
                  "language": "json"
                }
              }
            },
            "url": {
              "raw": "{{base_url}}/payments/encaissements/encaisser_multiple/",
              "host": ["{{base_url}}"],
              "path": ["payments", "encaissements", "encaisser_multiple", ""]
            }
          }
        },
        {
          "name": "4. Factures impayées (Admin)",
          "request": {
            "method": "GET",
            "header": [],
            "url": {
              "raw": "{{base_url}}/payments/encaissements/factures_impayees/?locataire_id={{locataire_id}}",
              "host": ["{{base_url}}"],
              "path": ["payments", "encaissements", "factures_impayees", ""],
              "query": [
                {"key": "locataire_id", "value": "{{locataire_id}}"}
              ]
            }
          }
        },
        {
          "name": "5. Résumé mois (Admin)",
          "request": {
            "method": "GET",
            "header": [],
            "url": {
              "raw": "{{base_url}}/payments/encaissements/resume_mois/?mois=3&annee=2026",
              "host": ["{{base_url}}"],
              "path": ["payments", "encaissements", "resume_mois", ""],
              "query": [
                {"key": "mois", "value": "3"},
                {"key": "annee", "value": "2026"}
              ]
            }
          }
        }
      ]
    },
    {
      "name": "10. Notifications",
      "item": [
        {
          "name": "1. Liste notifications",
          "request": {
            "method": "GET",
            "header": [],
            "url": {
              "raw": "{{base_url}}/notifications/?lu=false&type_notification=ALERTE",
              "host": ["{{base_url}}"],
              "path": ["notifications", ""],
              "query": [
                {"key": "lu", "value": "false"},
                {"key": "type_notification", "value": "ALERTE"}
              ]
            }
          }
        },
        {
          "name": "2. Notifications récentes",
          "request": {
            "method": "GET",
            "header": [],
            "url": {
              "raw": "{{base_url}}/notifications/recentes/",
              "host": ["{{base_url}}"],
              "path": ["notifications", "recentes", ""]
            }
          }
        },
        {
          "name": "3. Count non lues",
          "request": {
            "method": "GET",
            "header": [],
            "url": {
              "raw": "{{base_url}}/notifications/non_lues/",
              "host": ["{{base_url}}"],
              "path": ["notifications", "non_lues", ""]
            }
          }
        },
        {
          "name": "4. Marquer lue",
          "request": {
            "method": "POST",
            "header": [],
            "url": {
              "raw": "{{base_url}}/notifications/1/marquer_lue/",
              "host": ["{{base_url}}"],
              "path": ["notifications", "1", "marquer_lue", ""]
            }
          }
        },
        {
          "name": "5. Marquer toutes lues",
          "request": {
            "method": "POST",
            "header": [],
            "url": {
              "raw": "{{base_url}}/notifications/marquer_toutes_lues/",
              "host": ["{{base_url}}"],
              "path": ["notifications", "marquer_toutes_lues", ""]
            }
          }
        },
        {
          "name": "6. Envoyer (Admin)",
          "request": {
            "method": "POST",
            "header": [],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"destinataires\": [1, 2, 3],\n  \"titre\": \"Information importante\",\n  \"message\": \"Rappel: Paiement des loyers avant le 5 du mois\",\n  \"type_notification\": \"INFO\"\n}",
              "options": {
                "raw": {
                  "language": "json"
                }
              }
            },
            "url": {
              "raw": "{{base_url}}/notifications/envoyer/",
              "host": ["{{base_url}}"],
              "path": ["notifications", "envoyer", ""]
            }
          }
        },
        {
          "name": "7. Envoyer à tous (Admin)",
          "request": {
            "method": "POST",
            "header": [],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"titre\": \"Maintenance programmée\",\n  \"message\": \"Maintenance du réseau électrique le 20 mars de 9h à 12h\",\n  \"type_notification\": \"ALERTE\"\n}",
              "options": {
                "raw": {
                  "language": "json"
                }
              }
            },
            "url": {
              "raw": "{{base_url}}/notifications/envoyer_a_tous_locataires/",
              "host": ["{{base_url}}"],
              "path": ["notifications", "envoyer_a_tous_locataires", ""]
            }
          }
        }
      ]
    },
    {
      "name": "11. Dashboard",
      "item": [
        {
          "name": "1. Dashboard Admin",
          "request": {
            "method": "GET",
            "header": [],
            "url": {
              "raw": "{{base_url}}/dashboard/admin/",
              "host": ["{{base_url}}"],
              "path": ["dashboard", "admin", ""]
            }
          }
        },
        {
          "name": "2. Dashboard Locataire",
          "request": {
            "method": "GET",
            "header": [],
            "url": {
              "raw": "{{base_url}}/dashboard/locataire/",
              "host": ["{{base_url}}"],
              "path": ["dashboard", "locataire", ""]
            }
          }
        }
      ]
    }
  ]
}
```

---

## Guide d'Utilisation

### 1. Configuration Initiale

1. **Importer la collection** dans Postman (voir JSON ci-dessus)
2. **Créer un environnement** nommé "Gestion Locative - Dev"
3. **Ajouter les variables** d'environnement:
   - `base_url`: `http://localhost:8000/api`
   - `access_token`: (vide au départ)
   - `refresh_token`: (vide au départ)

### 2. Workflow de Test

1. **Authentification** :
   - Exécuter "02. Authentification → 2. Connexion"
   - Le token sera automatiquement sauvegardé dans les variables

2. **Tester les endpoints** :
   - Tous les endpoints utilisent automatiquement le token
   - Testez dans l'ordre logique (créer avant modifier/supprimer)

3. **Refresh token** :
   - Si vous obtenez une erreur 401, exécutez "03. Rafraîchir Token"

### 3. Tests Recommandés

#### Scénario 1: Créer une Location Complète
```
1. Créer maison (03. Propriétés → 4)
2. Créer utilisateur locataire (02. Utilisateurs → 3)
3. Créer compteur SODECI (05. Compteurs → 2)
4. Assigner compteur (05. Compteurs → 3)
5. Créer location (04. Locations → 3)
6. Créer facture loyer (06. Factures → 2)
7. Obtenir lien WhatsApp (06. Factures → 4)
```

#### Scénario 2: Workflow Paiement
```
1. Soumettre paiement en tant que locataire (08. → 2)
2. Vérifier paiements en attente admin (08. → 3)
3. Valider le paiement (08. → 4)
4. Vérifier statistiques (08. → 6)
```

#### Scénario 3: Encaissement Direct
```
1. Lister factures impayées (09. → 4)
2. Encaisser plusieurs factures (09. → 3)
3. Consulter résumé du mois (09. → 5)
```

### 4. Tests WhatsApp

Pour tester les fonctionnalités WhatsApp:

1. Créer une facture
2. Appeler `GET /billing/factures/{id}/lien_whatsapp/`
3. Copier le lien retourné
4. Coller dans votre navigateur
5. WhatsApp Web/App s'ouvre avec le message pré-rempli

### 5. Tests PDF

Pour tester les PDF:

1. Appeler un endpoint PDF (ex: `/billing/factures/{id}/telecharger_pdf/`)
2. Dans Postman, cliquer sur "Send and Download"
3. Le PDF sera téléchargé automatiquement

---

## Scripts Postman Utiles

### Auto-Save Token (Tests)
```javascript
// À ajouter dans l'onglet "Tests" des endpoints de login
if (pm.response.code === 200) {
    const jsonData = pm.response.json();
    pm.environment.set('access_token', jsonData.data.access);
    pm.environment.set('refresh_token', jsonData.data.refresh);
    pm.environment.set('user_id', jsonData.data.user.id);
    console.log('✅ Token sauvegardé');
}
```

### Auto-Refresh Token (Pre-request)
```javascript
// À ajouter dans Settings → Pre-request Script (au niveau de la collection)
const token = pm.environment.get('access_token');
if (!token) {
    console.log('⚠️ Aucun token, veuillez vous connecter');
}
```

### Validation Réponse (Tests)
```javascript
// À ajouter dans les tests pour valider la structure
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Response has success field", function () {
    const jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('success');
    pm.expect(jsonData.success).to.be.true;
});

pm.test("Response has data", function () {
    const jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('data');
});
```

---

## Raccourcis Clavier Postman

- `Ctrl + Enter` : Envoyer la requête
- `Ctrl + S` : Sauvegarder la requête
- `Ctrl + /` : Rechercher dans la collection
- `Alt + ↑/↓` : Naviguer entre les requêtes

---

## Notes Importantes

1. **URL de base** : Modifier `base_url` pour passer en production
2. **Authentification** : Toujours se connecter avant de tester les endpoints protégés
3. **Upload fichiers** : Utiliser "form-data" et sélectionner le fichier
4. **PDF/Blobs** : Utiliser "Send and Download" dans Postman
5. **WhatsApp** : Les liens retournés doivent être ouverts dans un navigateur

---

## Documentation Complète

📚 [Guide d'intégration Frontend (FRONTEND_INTEGRATION.md)](./FRONTEND_INTEGRATION.md)
📋 [Référence rapide API (API_QUICK_REFERENCE.md)](./API_QUICK_REFERENCE.md)

---

**Collection Postman pour Gestion Locative API v1.0.0**
**114 endpoints | Mars 2026**
