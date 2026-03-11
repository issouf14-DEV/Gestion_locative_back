"""
Tests pour le module rentals
"""
import pytest
from decimal import Decimal
from datetime import date, timedelta
from django.urls import reverse
from rest_framework import status

from apps.rentals.models import Location
from apps.rentals.services import LocationService
from apps.properties.models import Maison


@pytest.mark.django_db
class TestLocationModel:
    """Tests du modèle Location"""
    
    def test_create_location(self, locataire_user, maison):
        """Test de création d'une location"""
        today = date.today()
        location = Location.objects.create(
            locataire=locataire_user,
            maison=maison,
            date_debut=today,
            date_fin=today + timedelta(days=365),
            duree_mois=12,
            loyer_mensuel=Decimal('150000.00'),
            caution_versee=Decimal('300000.00')
        )
        
        assert location.numero_contrat.startswith('LOC-')
        assert location.statut == 'ACTIVE'
        assert location.locataire == locataire_user
        assert location.maison == maison
    
    def test_location_numero_contrat_auto_generated(self, locataire_user, maison):
        """Test que le numéro de contrat est auto-généré"""
        location = Location.objects.create(
            locataire=locataire_user,
            maison=maison,
            date_debut=date.today(),
            date_fin=date.today() + timedelta(days=180),
            duree_mois=6,
            loyer_mensuel=Decimal('100000.00'),
            caution_versee=Decimal('200000.00')
        )
        
        assert location.numero_contrat is not None
        assert 'LOC' in location.numero_contrat
    
    def test_location_str(self, location_active):
        """Test de la représentation string"""
        assert location_active.numero_contrat in str(location_active)


@pytest.mark.django_db
class TestLocationService:
    """Tests du service de location"""
    
    def test_creer_location(self, locataire_user, maison):
        """Test de création via le service"""
        result = LocationService.creer_location(
            locataire=locataire_user,
            maison=maison,
            date_debut=date.today(),
            duree_mois=12,
            loyer_mensuel=Decimal('150000.00'),
            caution_versee=Decimal('300000.00')
        )
        
        assert result['success'] is True
        assert 'numero_contrat' in result
        
        # Vérifier que la maison est marquée comme louée
        maison.refresh_from_db()
        assert maison.statut == 'LOUEE'
    
    def test_creer_location_maison_non_disponible(self, locataire_user):
        """Test échec si maison non disponible"""
        maison = Maison.objects.create(
            titre='Test',
            description='Test',
            type_logement='F2',
            prix=Decimal('100000.00'),
            caution=Decimal('200000.00'),
            adresse='Test',
            ville='Abidjan',
            commune='Cocody',
            quartier='Test',
            statut='LOUEE'  # Déjà louée
        )
        
        with pytest.raises(ValueError) as excinfo:
            LocationService.creer_location(
                locataire=locataire_user,
                maison=maison,
                date_debut=date.today(),
                duree_mois=12,
                loyer_mensuel=Decimal('100000.00'),
                caution_versee=Decimal('200000.00')
            )
        
        assert "pas disponible" in str(excinfo.value)
    
    def test_renouveler_location(self, location_active):
        """Test de renouvellement"""
        ancienne_date_fin = location_active.date_fin
        
        result = LocationService.renouveler_location(
            location=location_active,
            duree_supplementaire_mois=6
        )
        
        assert result['success'] is True
        
        location_active.refresh_from_db()
        assert location_active.date_fin > ancienne_date_fin
        assert location_active.duree_mois == 18  # 12 + 6
    
    def test_resilier_location(self, location_active):
        """Test de résiliation"""
        maison = location_active.maison
        
        result = LocationService.resilier_location(
            location=location_active,
            raison="Fin anticipée"
        )
        
        assert result['success'] is True
        
        location_active.refresh_from_db()
        assert location_active.statut == 'RESILIEE'
        
        maison.refresh_from_db()
        assert maison.statut == 'DISPONIBLE'
    
    def test_get_location_active(self, locataire_user, location_active):
        """Test récupération de location active"""
        location = LocationService.get_location_active(str(locataire_user.id))
        
        assert location is not None
        assert location.id == location_active.id
    
    def test_calculer_duree_restante(self, location_active):
        """Test du calcul de durée restante"""
        duree = LocationService.calculer_duree_restante(location_active)
        
        assert 'jours_restants' in duree
        assert 'mois_restants' in duree
        assert 'pourcentage_ecoule' in duree
        assert duree['jours_restants'] > 0


@pytest.mark.django_db
class TestLocationViewSet:
    """Tests des vues locations"""
    
    def test_list_locations_as_admin(self, admin_client, location_active):
        """Test liste des locations par admin"""
        url = reverse('location-list')
        response = admin_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_locataire_sees_only_own_location(self, locataire_client, location_active, second_locataire):
        """Test qu'un locataire ne voit que sa propre location"""
        # Créer une location pour un autre locataire
        another_maison = Maison.objects.create(
            titre='Autre Maison',
            description='Test',
            type_logement='F2',
            prix=Decimal('100000.00'),
            caution=Decimal('200000.00'),
            adresse='Test',
            ville='Abidjan',
            commune='Yopougon',
            quartier='Test',
            statut='DISPONIBLE'
        )
        Location.objects.create(
            locataire=second_locataire,
            maison=another_maison,
            date_debut=date.today(),
            date_fin=date.today() + timedelta(days=180),
            duree_mois=6,
            loyer_mensuel=Decimal('100000.00'),
            caution_versee=Decimal('200000.00')
        )
        
        url = reverse('location-list')
        response = locataire_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        # Seule la location du locataire connecté
        for loc in response.data['results']:
            assert str(loc['locataire']) == str(location_active.locataire.id)
    
    def test_ma_location_endpoint(self, locataire_client, location_active):
        """Test de l'endpoint ma-location"""
        url = reverse('location-ma-location')
        response = locataire_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['id'] == str(location_active.id)
    
    def test_ma_location_404_sans_location(self, locataire_client, locataire_user):
        """Test 404 si pas de location active"""
        # Supprimer les locations existantes pour ce locataire
        Location.objects.filter(locataire=locataire_user).delete()
        
        url = reverse('location-ma-location')
        response = locataire_client.get(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_create_location_as_admin(self, admin_client, locataire_user, maison):
        """Test création de location par admin"""
        url = reverse('location-list')
        data = {
            'locataire': locataire_user.id,
            'maison': maison.id,
            'date_debut': date.today().isoformat(),
            'duree_mois': 12,
            'loyer_mensuel': '150000.00',
            'caution_versee': '300000.00'
        }
        response = admin_client.post(url, data)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert Location.objects.filter(locataire=locataire_user).exists()
    
    def test_create_location_403_for_locataire(self, locataire_client, maison):
        """Test que les locataires ne peuvent pas créer de locations"""
        url = reverse('location-list')
        data = {
            'maison': maison.id,
            'date_debut': date.today().isoformat(),
            'duree_mois': 6,
            'loyer_mensuel': '100000.00',
            'caution_versee': '200000.00'
        }
        response = locataire_client.post(url, data)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_renouveler_location(self, admin_client, location_active):
        """Test renouvellement par admin"""
        url = reverse('location-renouveler', kwargs={'pk': location_active.id})
        data = {'duree_supplementaire_mois': 6}
        
        response = admin_client.post(url, data)
        
        assert response.status_code == status.HTTP_200_OK
        
        location_active.refresh_from_db()
        assert location_active.duree_mois == 18
    
    def test_resilier_location(self, admin_client, location_active):
        """Test résiliation par admin"""
        url = reverse('location-resilier', kwargs={'pk': location_active.id})
        data = {'raison': 'Test de résiliation'}
        
        response = admin_client.post(url, data)
        
        assert response.status_code == status.HTTP_200_OK
        
        location_active.refresh_from_db()
        assert location_active.statut == 'RESILIEE'
    
    def test_actives_endpoint(self, admin_client, location_active):
        """Test de l'endpoint locations actives"""
        url = reverse('location-actives')
        response = admin_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_expirant_endpoint(self, admin_client, location_active):
        """Test de l'endpoint locations expirant"""
        url = reverse('location-expirant')
        response = admin_client.get(url, {'jours': 365})  # 365 jours pour inclure notre location
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_statistiques_endpoint(self, admin_client, location_active):
        """Test de l'endpoint statistiques"""
        url = reverse('location-statistiques')
        response = admin_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'locations_actives' in response.data['data']
