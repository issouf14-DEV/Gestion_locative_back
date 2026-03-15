# Configuration de la Base de Données sur Render

## Problème actuel
L'application ne peut pas se connecter à la base de données PostgreSQL car le hostname `dpg-d6pc8bs50q8c73cb73l0-a` n'est pas accessible.

## Solution : Créer et configurer une base de données PostgreSQL

### Étape 1 : Créer une base de données PostgreSQL

1. Allez sur https://dashboard.render.com
2. Cliquez sur **"New +"** en haut à droite
3. Sélectionnez **"PostgreSQL"**
4. Configurez :
   - **Name** : `gestion-locative-db` (ou un nom de votre choix)
   - **Database** : `gestion_locative`
   - **User** : `gestion_locative_user` (ou laissez par défaut)
   - **Region** : Choisissez la même région que votre service web (ex: Frankfurt)
   - **Plan** : Free (ou Starter selon vos besoins)
5. Cliquez sur **"Create Database"**

⏱️ Attendez 2-3 minutes que la base de données soit créée et disponible.

### Étape 2 : Récupérer l'URL de connexion INTERNE

Une fois la base de données créée :

1. Cliquez sur votre base de données dans le dashboard
2. Dans l'onglet **"Info"** ou **"Connections"**, cherchez :
   - 🔴 **NE PAS UTILISER** : "External Database URL" (pour connexions depuis l'extérieur)
   - ✅ **UTILISER** : "Internal Database URL" (pour connexions entre services Render)

3. Copiez l'URL **interne** qui ressemble à ceci :
   ```
   postgresql://user:password@dpg-xxxxx-a.frankfurt-postgres.render.com/dbname
   ```

### Étape 3 : Configurer la variable d'environnement DATABASE_URL

1. Retournez sur votre **service web backend** (`gestion-locative-fqax`)
2. Allez dans **"Environment"** dans le menu de gauche
3. Cherchez la variable **`DATABASE_URL`** :
   - Si elle existe : Cliquez sur **"Edit"** et remplacez par l'URL interne copiée
   - Si elle n'existe pas : Cliquez sur **"Add Environment Variable"**
     - Key : `DATABASE_URL`
     - Value : Collez l'URL interne copiée
4. Cliquez sur **"Save Changes"**

### Étape 4 : Vérifier les autres variables d'environnement requises

Assurez-vous que ces variables sont également configurées :

| Variable | Valeur | Description |
|----------|--------|-------------|
| `DJANGO_SETTINGS_MODULE` | `config.settings.production` | Module de settings Django |
| `SECRET_KEY` | Une longue chaîne aléatoire | Clé secrète Django (générer avec `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`) |
| `ALLOWED_HOSTS` | `gestion-locative-fqax.onrender.com,.onrender.com` | Hosts autorisés |
| `REDIS_URL` | `redis://red-xxxxx:6379` | URL Redis (optionnel, pour Celery) |

### Étape 5 : Appliquer les migrations

Une fois la database connectée, vous devez appliquer les migrations :

#### Option A : Via le Shell Render

1. Dans votre service web, cliquez sur **"Shell"** dans le menu
2. Exécutez :
   ```bash
   python manage.py migrate
   python manage.py createsuperuser  # Optionnel : créer un admin
   ```

#### Option B : Via un Build Command

1. Dans les settings de votre service web, trouvez **"Build Command"**
2. Ajoutez :
   ```bash
   pip install -r requirements/production.txt && python manage.py collectstatic --noinput && python manage.py migrate
   ```

### Étape 6 : Redéployer

- Le service devrait redémarrer automatiquement après avoir sauvegardé les variables d'environnement
- Sinon, cliquez sur **"Manual Deploy"** → **"Deploy latest commit"**

### Étape 7 : Vérifier les logs

1. Allez dans **"Logs"** de votre service web
2. Vérifiez qu'il n'y a plus d'erreurs de connexion à la base de données
3. Vous devriez voir : `Applying migrations...` suivi de `Starting gunicorn...`

---

## Alternative : Si vous avez déjà une base de données PostgreSQL

Si vous avez déjà créé une base de données PostgreSQL sur Render :

1. Allez sur cette base de données dans le dashboard
2. Vérifiez qu'elle est dans l'état **"Available"** (pas "Suspended" ou "Deleted")
3. Copiez l'**Internal Database URL**
4. Suivez les étapes 3-7 ci-dessus

---

## Vérification finale

Une fois tout configuré, testez l'inscription depuis votre frontend :

```bash
# L'erreur devrait disparaître et vous devriez pouvoir créer un compte
```

Si vous voyez toujours une erreur 500, consultez les logs et cherchez un message d'erreur différent.

---

## Contacts et Support

- Dashboard Render : https://dashboard.render.com
- Documentation Render PostgreSQL : https://render.com/docs/databases
- Si problème persiste : Partagez les nouveaux logs d'erreur
