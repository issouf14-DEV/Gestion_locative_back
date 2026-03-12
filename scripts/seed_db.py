"""
Script pour peupler la base de données avec des données de test
⚠️ ATTENTION: Ce script est UNIQUEMENT pour le développement local!
⚠️ Ne JAMAIS l'utiliser en production!
"""
import os
import django
from datetime import date, timedelta
from decimal import Decimal
from decouple import config

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.users.models import User
from apps.properties.models import Maison
from apps.rentals.models import Location
from apps.billing.models import Facture, IndexCompteur


def get_admin_config():
    """Récupérer la configuration admin depuis l'environnement."""
    return {
        'email': config('ADMIN_DEV_EMAIL'),
        'password': config('ADMIN_DEV_PASSWORD'),
        'nom': config('ADMIN_DEV_NOM'),
        'prenoms': config('ADMIN_DEV_PRENOMS'),
        'telephone': config('ADMIN_DEV_PHONE'),
    }


def create_users(admin_config):
    """Créer des utilisateurs de test"""
    print("Création des utilisateurs...")

    # Admin
    admin, created = User.objects.get_or_create(
        email=admin_config['email'],
        defaults={
            'nom': admin_config['nom'],
            'prenoms': admin_config['prenoms'],
            'telephone': admin_config['telephone'],
            'role': 'ADMIN',
            'is_staff': True,
            'is_superuser': True
        }
    )
    if created:
        admin.set_password(admin_config['password'])
        admin.save()
        print(f"✓ Admin créé: {admin.email}")
    else:
        admin.nom = admin_config['nom']
        admin.prenoms = admin_config['prenoms']
        admin.telephone = admin_config['telephone']
        admin.role = 'ADMIN'
        admin.is_staff = True
        admin.is_superuser = True
        admin.set_password(admin_config['password'])
        admin.save()
        print(f"✓ Admin mis à jour: {admin.email}")
    
    # Locataires
    locataires_data = [
        {'email': 'bebert@test.com', 'nom': 'Kouassi', 'prenoms': 'Bebert', 'tel': '0701020304'},
        {'email': 'elvire@test.com', 'nom': 'Koffi', 'prenoms': 'Elvire', 'tel': '0702030405'},
        {'email': 'mamadou@test.com', 'nom': 'Diouf', 'prenoms': 'Mamadou', 'tel': '0703040506'},
        {'email': 'papy@test.com', 'nom': 'Yao', 'prenoms': 'Papy', 'tel': '0704050607'},
        {'email': 'alfred@test.com', 'nom': 'Bamba', 'prenoms': 'Alfred', 'tel': '0705060708'},
    ]
    
    locataires = []
    for data in locataires_data:
        user, created = User.objects.get_or_create(
            email=data['email'],
            defaults={
                'nom': data['nom'],
                'prenoms': data['prenoms'],
                'telephone': data['tel'],
                'role': 'LOCATAIRE'
            }
        )
        if created:
            user.set_password('test1234')
            user.save()
            print(f"✓ Locataire créé: {user.get_full_name()}")
        locataires.append(user)
    
    return admin, locataires


def create_properties():
    """Créer des maisons de test"""
    print("\nCréation des maisons...")
    
    maisons_data = [
        {
            'titre': 'Villa F4 Cocody',
            'description': 'Magnifique villa moderne avec jardin',
            'type_logement': 'F4',
            'prix': 200000,
            'caution': 400000,
            'ville': 'Abidjan',
            'commune': 'Cocody',
            'quartier': 'Riviera',
            'chambres': 4,
            'salles_bain': 3,
            'statut': 'LOUEE'
        },
        {
            'titre': 'Appartement F2 Marcory',
            'description': 'Joli F2 bien situé proche des commodités',
            'type_logement': 'F2',
            'prix': 80000,
            'caution': 160000,
            'ville': 'Abidjan',
            'commune': 'Marcory',
            'quartier': 'Zone 4',
            'chambres': 2,
            'salles_bain': 1,
            'statut': 'LOUEE'
        },
        {
            'titre': 'Studio Plateau',
            'description': 'Studio moderne idéal pour célibataire',
            'type_logement': 'STUDIO',
            'prix': 65000,
            'caution': 130000,
            'ville': 'Abidjan',
            'commune': 'Plateau',
            'quartier': 'Centre',
            'chambres': 1,
            'salles_bain': 1,
            'statut': 'DISPONIBLE'
        },
        {
            'titre': 'Duplex F5 Deux-Plateaux',
            'description': 'Spacieux duplex avec terrasse',
            'type_logement': 'DUPLEX',
            'prix': 350000,
            'caution': 700000,
            'ville': 'Abidjan',
            'commune': 'Cocody',
            'quartier': 'Deux-Plateaux',
            'chambres': 5,
            'salles_bain': 4,
            'statut': 'DISPONIBLE'
        }
    ]
    
    maisons = []
    for data in maisons_data:
        maison, created = Maison.objects.get_or_create(
            titre=data['titre'],
            defaults={
                'description': data['description'],
                'type_logement': data['type_logement'],
                'prix': data['prix'],
                'caution': data['caution'],
                'adresse': f"{data['quartier']}, {data['commune']}",
                'ville': data['ville'],
                'commune': data['commune'],
                'quartier': data['quartier'],
                'nombre_chambres': data['chambres'],
                'nombre_salles_bain': data['salles_bain'],
                'nombre_toilettes': data['salles_bain'],
                'superficie': Decimal('75.50'),
                'statut': data['statut'],
                'equipements': ['Climatisation', 'Cuisine équipée', 'Parking'],
                'commodites': ['Ecole', 'Supermarché', 'Transport']
            }
        )
        if created:
            print(f"✓ Maison créée: {maison.titre} ({maison.reference})")
        maisons.append(maison)
    
    return maisons


def create_rentals(locataires, maisons):
    """Créer des locations"""
    print("\nCréation des locations...")
    
    # Location pour les 2 premières maisons
    for i in range(min(2, len(locataires), len(maisons))):
        location, created = Location.objects.get_or_create(
            locataire=locataires[i],
            maison=maisons[i],
            defaults={
                'date_debut': date.today() - timedelta(days=90),
                'date_fin': date.today() + timedelta(days=275),
                'duree_mois': 12,
                'loyer_mensuel': maisons[i].prix,
                'caution_versee': maisons[i].caution,
                'statut': 'ACTIVE'
            }
        )
        if created:
            print(f"✓ Location créée: {location.numero_contrat}")


def create_index_and_factures(locataires):
    """Créer des index de compteurs et factures"""
    print("\nCréation des index et factures...")
    
    # Index SODECI pour février 2026
    index_data = [
        {'locataire': locataires[0], 'ancien': 2138, 'nouveau': 2312},
        {'locataire': locataires[1], 'ancien': 709, 'nouveau': 744},
        {'locataire': locataires[2], 'ancien': 671, 'nouveau': 715},
        {'locataire': locataires[3], 'ancien': 1862, 'nouveau': 1906},
        {'locataire': locataires[4], 'ancien': 2552, 'nouveau': 2595},
    ]
    
    for data in index_data:
        # Index mois précédent (février)
        IndexCompteur.objects.get_or_create(
            locataire=data['locataire'],
            type_compteur='SODECI',
            mois=2,
            annee=2026,
            defaults={'index_valeur': Decimal(str(data['ancien']))}
        )
        
        # Index mois actuel (mars)
        IndexCompteur.objects.get_or_create(
            locataire=data['locataire'],
            type_compteur='SODECI',
            mois=3,
            annee=2026,
            defaults={'index_valeur': Decimal(str(data['nouveau']))}
        )
    
    print("✓ Index de compteurs créés")
    
    # Créer factures de loyer de mars
    for locataire in locataires[:2]:
        Facture.objects.get_or_create(
            locataire=locataire,
            type_facture='LOYER',
            mois=3,
            annee=2026,
            defaults={
                'montant': Decimal('100000'),
                'date_echeance': date(2026, 3, 25),
                'statut': 'EN_ATTENTE'
            }
        )
    
    print("✓ Factures de loyer créées")


def main():
    print("=" * 50)
    print("SEED DATABASE - Gestion Locative")
    print("⚠️  DÉVELOPPEMENT LOCAL UNIQUEMENT")
    print("=" * 50)

    admin_config = get_admin_config()

    _, locataires = create_users(admin_config)
    maisons = create_properties()
    create_rentals(locataires, maisons)
    create_index_and_factures(locataires)
    
    print("\n" + "=" * 50)
    print("✓ Base de données peuplée avec succès!")
    print("=" * 50)
    print("\n🔐 Identifiants de connexion:")
    print(f"Email Admin: {admin_config['email']}")
    print(f"Mot de passe: {admin_config['password']}")
    print(f"\nEmail Locataire: bebert@test.com")
    print(f"Mot de passe: test1234")
    print("\n📍 URLs:")
    print("API: http://localhost:8000/api/")
    print("Admin Django: http://localhost:8000/admin/")
    print("Swagger: http://localhost:8000/api/docs/")
    print("\n⚠️  IMPORTANT: Ces identifiants sont pour le développement UNIQUEMENT!")
    print("⚠️  En production, utilisez: python manage.py createsuperuser")
    print("=" * 50)


if __name__ == '__main__':
    main()
