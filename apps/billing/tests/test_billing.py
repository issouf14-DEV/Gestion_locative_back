"""
Tests pour le module billing
"""
import pytest
from decimal import Decimal
from datetime import date, timedelta
from django.urls import reverse
from rest_framework import status

from apps.billing.models import Facture, IndexCompteur
from apps.billing.calculators import FactureCalculator
from apps.billing.services import BillingService


@pytest.mark.django_db
class TestFactureModel:
    """Tests du modèle Facture"""
    
    def test_create_facture_loyer(self, locataire_user):
        """Test création d'une facture de loyer"""
        today = date.today()
        facture = Facture.objects.create(
            locataire=locataire_user,
            type_facture='LOYER',
            montant=Decimal('150000.00'),
            mois=today.month,
            annee=today.year,
            date_echeance=today + timedelta(days=5)
        )
        
        assert facture.reference.startswith('LOY-')
        assert facture.statut == 'EN_ATTENTE'
        assert facture.locataire == locataire_user
    
    def test_facture_reference_auto_generated(self, locataire_user):
        """Test que la référence est auto-générée"""
        facture = Facture.objects.create(
            locataire=locataire_user,
            type_facture='SODECI',
            montant=Decimal('5000.00'),
            mois=3,
            annee=2026,
            date_echeance=date.today() + timedelta(days=10),
            index_ancien=Decimal('100.00'),
            index_nouveau=Decimal('150.00')
        )
        
        assert facture.reference is not None
        assert facture.consommation == Decimal('50.00')
    
    def test_is_en_retard(self, locataire_user):
        """Test de la propriété is_en_retard"""
        # Facture non en retard
        facture = Facture.objects.create(
            locataire=locataire_user,
            type_facture='LOYER',
            montant=Decimal('100000.00'),
            mois=date.today().month,
            annee=date.today().year,
            date_echeance=date.today() + timedelta(days=5)
        )
        
        assert facture.is_en_retard is False
        
        # Modifier pour être en retard
        facture.date_echeance = date.today() - timedelta(days=1)
        facture.save()
        
        assert facture.is_en_retard is True
    
    def test_facture_unique_par_mois(self, locataire_user):
        """Test qu'on ne peut pas avoir deux factures du même type pour le même mois"""
        Facture.objects.create(
            locataire=locataire_user,
            type_facture='LOYER',
            montant=Decimal('100000.00'),
            mois=1,
            annee=2026,
            date_echeance=date(2026, 1, 10)
        )
        
        with pytest.raises(Exception):  # IntegrityError
            Facture.objects.create(
                locataire=locataire_user,
                type_facture='LOYER',
                montant=Decimal('100000.00'),
                mois=1,
                annee=2026,
                date_echeance=date(2026, 1, 10)
            )


@pytest.mark.django_db
class TestIndexCompteurModel:
    """Tests du modèle IndexCompteur"""
    
    def test_create_index(self, locataire_user):
        """Test création d'un index de compteur"""
        index = IndexCompteur.objects.create(
            locataire=locataire_user,
            type_compteur='SODECI',
            index_valeur=Decimal('2500.00'),
            mois=3,
            annee=2026
        )
        
        assert index.type_compteur == 'SODECI'
        assert index.index_valeur == Decimal('2500.00')


@pytest.mark.django_db
class TestFactureCalculator:
    """Tests du calculateur de facturation"""
    
    def test_calculer_repartition_sodeci(self, locataire_user, second_locataire):
        """Test du calcul de répartition SODECI"""
        today = date.today()
        mois_prec = today.month - 1 if today.month > 1 else 12
        annee_prec = today.year if today.month > 1 else today.year - 1
        
        # Index précédents
        IndexCompteur.objects.create(
            locataire=locataire_user,
            type_compteur='SODECI',
            index_valeur=Decimal('2138.00'),
            mois=mois_prec,
            annee=annee_prec
        )
        IndexCompteur.objects.create(
            locataire=second_locataire,
            type_compteur='SODECI',
            index_valeur=Decimal('1000.00'),
            mois=mois_prec,
            annee=annee_prec
        )
        
        # Index actuels
        IndexCompteur.objects.create(
            locataire=locataire_user,
            type_compteur='SODECI',
            index_valeur=Decimal('2312.00'),  # Consommation: 174
            mois=today.month,
            annee=today.year
        )
        IndexCompteur.objects.create(
            locataire=second_locataire,
            type_compteur='SODECI',
            index_valeur=Decimal('1035.00'),  # Consommation: 35
            mois=today.month,
            annee=today.year
        )
        
        # Total consommation: 174 + 35 = 209
        # Locataire 1: 174/209 = 83.25%
        # Locataire 2: 35/209 = 16.75%
        
        result = FactureCalculator.calculer_repartition(
            type_facture='SODECI',
            montant_total=Decimal('29206.00'),
            mois=today.month,
            annee=today.year,
            date_echeance=today + timedelta(days=10)
        )
        
        assert result['success'] is True
        assert result['consommation_totale'] == 209.0
        assert len(result['details']) == 2
        
        # Vérifier que les factures ont été créées
        assert Facture.objects.filter(
            type_facture='SODECI',
            mois=today.month,
            annee=today.year
        ).count() == 2
    
    def test_calculer_repartition_sans_index(self):
        """Test d'erreur si aucun index n'est trouvé"""
        today = date.today()
        
        with pytest.raises(ValueError) as excinfo:
            FactureCalculator.calculer_repartition(
                type_facture='CIE',
                montant_total=Decimal('50000.00'),
                mois=today.month,
                annee=today.year,
                date_echeance=today + timedelta(days=10)
            )
        
        assert "Aucun index trouvé" in str(excinfo.value)
    
    def test_generer_factures_loyer(self, location_active):
        """Test de génération automatique des factures de loyer"""
        today = date.today()
        
        result = FactureCalculator.generer_factures_loyer(
            mois=today.month,
            annee=today.year,
            date_echeance=today + timedelta(days=5)
        )
        
        assert result['success'] is True
        assert result['nombre_factures'] >= 1
        
        # Vérifier que la facture a été créée
        assert Facture.objects.filter(
            type_facture='LOYER',
            locataire=location_active.locataire,
            mois=today.month,
            annee=today.year
        ).exists()


@pytest.mark.django_db
class TestBillingService:
    """Tests du service de facturation"""
    
    def test_calculer_dette_locataire(self, locataire_user, facture_loyer):
        """Test du calcul de dette"""
        result = BillingService.calculer_dette_locataire(str(locataire_user.id))
        
        assert result['dette_totale'] == 150000.0
        assert result['dette_loyer'] == 150000.0
        assert result['nombre_factures_impayees'] == 1
    
    def test_marquer_factures_en_retard(self, locataire_user):
        """Test du marquage automatique des factures en retard"""
        # Créer une facture en retard
        Facture.objects.create(
            locataire=locataire_user,
            type_facture='LOYER',
            montant=Decimal('100000.00'),
            mois=1,
            annee=2026,
            date_echeance=date.today() - timedelta(days=5),
            statut='EN_ATTENTE'
        )
        
        result = BillingService.marquer_factures_en_retard()
        
        assert result['nombre_factures_marquees'] >= 1
    
    def test_calculer_dette_sans_factures(self, locataire_user):
        """Test dette à zéro si pas de factures impayées"""
        # Supprimer toutes les factures existantes
        Facture.objects.filter(locataire=locataire_user).delete()
        
        result = BillingService.calculer_dette_locataire(str(locataire_user.id))
        
        assert result['dette_totale'] == 0
        assert result['nombre_factures_impayees'] == 0


@pytest.mark.django_db
class TestFactureViewSet:
    """Tests des vues factures"""
    
    def test_list_factures_as_admin(self, admin_client, facture_loyer):
        """Test liste des factures par admin"""
        url = reverse('facture-list')
        response = admin_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_locataire_sees_only_own_factures(self, locataire_client, locataire_user, second_locataire):
        """Test qu'un locataire ne voit que ses propres factures"""
        # Créer une facture pour un autre locataire
        Facture.objects.create(
            locataire=second_locataire,
            type_facture='LOYER',
            montant=Decimal('100000.00'),
            mois=date.today().month,
            annee=date.today().year,
            date_echeance=date.today() + timedelta(days=5)
        )
        
        # Créer une facture pour le locataire connecté
        Facture.objects.create(
            locataire=locataire_user,
            type_facture='LOYER',
            montant=Decimal('150000.00'),
            mois=date.today().month,
            annee=date.today().year,
            date_echeance=date.today() + timedelta(days=5)
        )
        
        url = reverse('facture-list')
        response = locataire_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        # Vérifier que seules les factures du locataire sont retournées
        for facture in response.data['results']:
            assert str(facture['locataire']) == str(locataire_user.id)
    
    def test_repartir_facture_as_admin(self, admin_client, locataire_user, second_locataire):
        """Test de la répartition par admin"""
        today = date.today()
        mois_prec = today.month - 1 if today.month > 1 else 12
        annee_prec = today.year if today.month > 1 else today.year - 1
        
        # Créer les index nécessaires
        IndexCompteur.objects.create(
            locataire=locataire_user,
            type_compteur='CIE',
            index_valeur=Decimal('500.00'),
            mois=mois_prec,
            annee=annee_prec
        )
        IndexCompteur.objects.create(
            locataire=locataire_user,
            type_compteur='CIE',
            index_valeur=Decimal('600.00'),
            mois=today.month,
            annee=today.year
        )
        IndexCompteur.objects.create(
            locataire=second_locataire,
            type_compteur='CIE',
            index_valeur=Decimal('200.00'),
            mois=mois_prec,
            annee=annee_prec
        )
        IndexCompteur.objects.create(
            locataire=second_locataire,
            type_compteur='CIE',
            index_valeur=Decimal('300.00'),
            mois=today.month,
            annee=today.year
        )
        
        url = reverse('facture-repartir')
        data = {
            'type_facture': 'CIE',
            'montant_total': '50000.00',
            'mois': today.month,
            'annee': today.year,
            'date_echeance': (today + timedelta(days=10)).isoformat()
        }
        response = admin_client.post(url, data)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['success'] is True
    
    def test_repartir_403_for_locataire(self, locataire_client):
        """Test que la répartition est interdite aux locataires"""
        url = reverse('facture-repartir')
        data = {
            'type_facture': 'SODECI',
            'montant_total': '30000.00',
            'mois': date.today().month,
            'annee': date.today().year,
            'date_echeance': (date.today() + timedelta(days=10)).isoformat()
        }
        response = locataire_client.post(url, data)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
