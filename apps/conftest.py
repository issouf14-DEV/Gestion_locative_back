"""
Fixtures partagées pour tous les tests
"""
import pytest
from decimal import Decimal
from datetime import date, timedelta
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import User
from apps.properties.models import Maison
from apps.rentals.models import Location
from apps.billing.models import Facture, FactureCollective, IndexCompteur
from apps.payments.models import Paiement
from apps.reservations.models import Reservation
from apps.expenses.models import Depense
from apps.notifications.models import Notification


@pytest.fixture
def api_client():
    """Client API pour les tests"""
    return APIClient()


@pytest.fixture
def admin_user(db):
    """Crée un utilisateur administrateur"""
    user = User.objects.create_user(
        email='admin@test.com',
        nom='Admin',
        prenoms='Test',
        telephone='0700000001',
        password='TestPassword123!',
        role='ADMIN',
        is_staff=True
    )
    # Profile créé automatiquement via signal post_save
    return user


@pytest.fixture
def locataire_user(db):
    """Crée un utilisateur locataire"""
    user = User.objects.create_user(
        email='locataire@test.com',
        nom='Locataire',
        prenoms='Test',
        telephone='0700000002',
        password='TestPassword123!',
        role='LOCATAIRE'
    )
    # Profile créé automatiquement via signal post_save
    return user


@pytest.fixture
def second_locataire(db):
    """Crée un deuxième locataire pour les tests de calcul"""
    user = User.objects.create_user(
        email='locataire2@test.com',
        nom='Konan',
        prenoms='Marie',
        telephone='0700000003',
        password='TestPassword123!',
        role='LOCATAIRE'
    )
    # Profile créé automatiquement via signal post_save
    return user


@pytest.fixture
def admin_client(api_client, admin_user):
    """Client API authentifié en tant qu'admin"""
    refresh = RefreshToken.for_user(admin_user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return api_client


@pytest.fixture
def locataire_client(api_client, locataire_user):
    """Client API authentifié en tant que locataire"""
    refresh = RefreshToken.for_user(locataire_user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return api_client


@pytest.fixture
def maison(db):
    """Crée une maison de test"""
    return Maison.objects.create(
        titre='Villa Test',
        description='Une belle villa pour les tests',
        type_logement='VILLA',
        prix=Decimal('150000.00'),
        caution=Decimal('300000.00'),
        adresse='123 Rue des Tests',
        ville='Abidjan',
        commune='Cocody',
        quartier='Angré',
        nombre_chambres=3,
        nombre_salles_bain=2,
        nombre_toilettes=2,
        superficie=Decimal('120.00'),
        statut='DISPONIBLE',
        equipements=['climatisation', 'cuisine équipée', 'gardien'],
        commodites=['école', 'supermarché', 'transport']
    )


@pytest.fixture
def maison_louee(db, maison, locataire_user):
    """Crée une maison louée"""
    maison.statut = 'LOUEE'
    maison.save()
    return maison


@pytest.fixture
def location_active(db, locataire_user, maison):
    """Crée une location active"""
    maison.statut = 'LOUEE'
    maison.save()
    
    today = date.today()
    return Location.objects.create(
        locataire=locataire_user,
        maison=maison,
        date_debut=today,
        date_fin=today + timedelta(days=365),
        duree_mois=12,
        loyer_mensuel=Decimal('150000.00'),
        caution_versee=Decimal('300000.00'),
        statut='ACTIVE'
    )


@pytest.fixture
def facture_loyer(db, locataire_user):
    """Crée une facture de loyer"""
    today = date.today()
    return Facture.objects.create(
        locataire=locataire_user,
        type_facture='LOYER',
        montant=Decimal('150000.00'),
        mois=today.month,
        annee=today.year,
        date_echeance=today + timedelta(days=5),
        statut='EN_ATTENTE'
    )


@pytest.fixture
def facture_collective_sodeci(db):
    """Crée une facture collective SODECI"""
    today = date.today()
    return FactureCollective.objects.create(
        type_facture='SODECI',
        montant_total=Decimal('29206.00'),
        mois=today.month,
        annee=today.year,
        consommation_totale=Decimal('1028.00')
    )


@pytest.fixture
def index_compteur_locataire(db, locataire_user):
    """Crée des index de compteur pour un locataire"""
    today = date.today()
    mois_prec = today.month - 1 if today.month > 1 else 12
    annee_prec = today.year if today.month > 1 else today.year - 1
    
    # Index précédent
    IndexCompteur.objects.create(
        locataire=locataire_user,
        type_compteur='SODECI',
        index_valeur=Decimal('2138.00'),
        mois=mois_prec,
        annee=annee_prec
    )
    
    # Index actuel
    return IndexCompteur.objects.create(
        locataire=locataire_user,
        type_compteur='SODECI',
        index_valeur=Decimal('2312.00'),
        mois=today.month,
        annee=today.year
    )


@pytest.fixture
def paiement_en_attente(db, locataire_user, facture_loyer):
    """Crée un paiement en attente de validation"""
    return Paiement.objects.create(
        locataire=locataire_user,
        montant=Decimal('150000.00'),
        factures_ids=[str(facture_loyer.id)],  # Convertir UUID en string
        preuve='payments/preuves/test.jpg',
        notes_locataire='Paiement via Mobile Money',
        statut='EN_ATTENTE'
    )


@pytest.fixture
def reservation(db, locataire_user, maison):
    """Crée une réservation"""
    today = date.today()
    return Reservation.objects.create(
        user=locataire_user,
        maison=maison,
        date_debut_souhaitee=today + timedelta(days=30),
        duree_mois=12,
        message='Je suis intéressé par ce logement',
        statut='EN_ATTENTE'
    )


@pytest.fixture
def depense(db, admin_user, maison):
    """Crée une dépense"""
    return Depense.objects.create(
        maison=maison,
        categorie='ENTRETIEN',
        montant=Decimal('50000.00'),
        description='Réparation plomberie',
        date_depense=date.today()
    )


@pytest.fixture
def notification(db, locataire_user):
    """Crée une notification"""
    return Notification.objects.create(
        destinataire=locataire_user,
        type_notification='FACTURE',
        titre='Nouvelle facture',
        message='Votre facture de loyer est disponible',
        lu=False
    )
