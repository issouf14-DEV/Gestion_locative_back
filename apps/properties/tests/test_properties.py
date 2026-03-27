"""
Tests pour le module properties
"""
import pytest
from decimal import Decimal
from django.urls import reverse
from rest_framework import status
from apps.properties.models import Maison, ImageMaison


@pytest.mark.django_db
class TestMaisonModel:
    """Tests du modèle Maison"""
    
    def test_create_maison(self, db):
        """Test de création d'une maison"""
        maison = Maison.objects.create(
            titre='Appartement F3 Cocody',
            description='Bel appartement avec vue sur la lagune',
            type_logement='F3',
            prix=Decimal('200000.00'),
            caution=Decimal('400000.00'),
            adresse='Rue des Jardins',
            ville='Abidjan',
            commune='Cocody',
            quartier='Riviera',
            nombre_chambres=2,
            nombre_salles_bain=2
        )
        
        assert maison.titre == 'Appartement F3 Cocody'
        assert maison.statut == 'DISPONIBLE'
        assert maison.reference.startswith('MAIS-')
        assert maison.is_disponible is True
    
    def test_maison_reference_auto_generated(self, db):
        """Test que la référence est auto-générée"""
        maison = Maison.objects.create(
            titre='Test',
            description='Test description',
            type_logement='STUDIO',
            prix=Decimal('50000.00'),
            caution=Decimal('100000.00'),
            adresse='Test adresse',
            ville='Abidjan',
            commune='Plateau',
            quartier='Centre'
        )
        
        assert maison.reference is not None
        assert maison.reference != ''
        assert 'MAIS' in maison.reference
    
    def test_maison_reference_unique(self, db):
        """Test que chaque maison a une référence unique"""
        maison1 = Maison.objects.create(
            titre='Maison 1',
            description='Description 1',
            type_logement='VILLA',
            prix=Decimal('500000.00'),
            caution=Decimal('1000000.00'),
            adresse='Adresse 1',
            ville='Abidjan',
            commune='Cocody',
            quartier='Angré'
        )
        
        maison2 = Maison.objects.create(
            titre='Maison 2',
            description='Description 2',
            type_logement='VILLA',
            prix=Decimal('600000.00'),
            caution=Decimal('1200000.00'),
            adresse='Adresse 2',
            ville='Abidjan',
            commune='Cocody',
            quartier='Riviera'
        )
        
        assert maison1.reference != maison2.reference
    
    def test_is_disponible_property(self, maison):
        """Test de la propriété is_disponible"""
        assert maison.is_disponible is True
        
        maison.statut = 'LOUEE'
        maison.save()
        assert maison.is_disponible is False
    
    def test_maison_str(self, maison):
        """Test de la représentation string"""
        assert maison.titre in str(maison)
        assert maison.reference in str(maison)


@pytest.mark.django_db
class TestImageMaisonModel:
    """Tests du modèle ImageMaison"""
    
    def test_create_image(self, maison):
        """Test de création d'une image"""
        image = ImageMaison.objects.create(
            maison=maison,
            image='properties/images/test.jpg',
            legende='Vue extérieure',
            est_principale=True
        )
        
        assert image.maison == maison
        assert image.est_principale is True
    
    def test_single_image_principale(self, maison):
        """Test qu'une seule image peut être principale"""
        image1 = ImageMaison.objects.create(
            maison=maison,
            image='properties/images/test1.jpg',
            est_principale=True
        )
        
        image2 = ImageMaison.objects.create(
            maison=maison,
            image='properties/images/test2.jpg',
            est_principale=True
        )
        
        image1.refresh_from_db()
        assert image1.est_principale is False
        assert image2.est_principale is True


@pytest.mark.django_db
class TestMaisonViewSet:
    """Tests des vues maisons"""
    
    def test_list_maisons_public(self, api_client, maison):
        """Test que la liste des maisons est publique"""
        url = reverse('maison-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_list_only_disponibles_for_public(self, api_client, maison):
        """Test que seules les maisons disponibles sont listées pour les visiteurs"""
        # Créer une maison louée
        Maison.objects.create(
            titre='Maison Louée',
            description='Test',
            type_logement='F2',
            prix=Decimal('100000.00'),
            caution=Decimal('200000.00'),
            adresse='Test',
            ville='Abidjan',
            commune='Cocody',
            quartier='Test',
            statut='LOUEE'
        )
        
        url = reverse('maison-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        for item in response.data['results']:
            assert item['statut'] == 'DISPONIBLE'
    
    def test_retrieve_maison_increments_views(self, api_client, maison):
        """Test que la consultation incrémente le compteur de vues"""
        initial_views = maison.nombre_vues
        
        url = reverse('maison-detail', kwargs={'pk': maison.id})
        api_client.get(url)
        
        maison.refresh_from_db()
        assert maison.nombre_vues == initial_views + 1
    
    def test_create_maison_as_admin(self, admin_client):
        """Test création de maison par admin"""
        url = reverse('maison-list')
        data = {
            'titre': 'Nouvelle Villa',
            'description': 'Belle villa moderne',
            'type_logement': 'VILLA',
            'prix': '300000.00',
            'caution': '600000.00',
            'adresse': 'Rue Nouvelle',
            'ville': 'Abidjan',
            'commune': 'Marcory',
            'quartier': 'Zone 4',
            'nombre_chambres': 4,
            'nombre_salles_bain': 3,
            'nombre_toilettes': 3
        }
        response = admin_client.post(url, data)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert Maison.objects.filter(titre='Nouvelle Villa').exists()
    
    def test_create_maison_403_for_locataire(self, locataire_client):
        """Test que les locataires ne peuvent pas créer de maisons"""
        url = reverse('maison-list')
        data = {
            'titre': 'Test',
            'description': 'Test',
            'type_logement': 'STUDIO',
            'prix': '50000.00',
            'caution': '100000.00',
            'adresse': 'Test',
            'ville': 'Abidjan',
            'commune': 'Plateau',
            'quartier': 'Centre'
        }
        response = locataire_client.post(url, data)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_update_maison_as_admin(self, admin_client, maison):
        """Test mise à jour de maison par admin"""
        url = reverse('maison-detail', kwargs={'pk': maison.id})
        data = {'prix': '200000.00'}
        response = admin_client.patch(url, data)
        
        assert response.status_code == status.HTTP_200_OK
        maison.refresh_from_db()
        assert maison.prix == Decimal('200000.00')
    
    def test_changer_statut_maison(self, admin_client, maison):
        """Test changement de statut d'une maison"""
        url = reverse('maison-changer-statut', kwargs={'pk': maison.id})
        data = {'statut': 'EN_MAINTENANCE'}
        response = admin_client.patch(url, data)
        
        assert response.status_code == status.HTTP_200_OK
        maison.refresh_from_db()
        assert maison.statut == 'EN_MAINTENANCE'
    
    def test_disponibles_endpoint(self, api_client, maison):
        """Test de l'endpoint /disponibles/"""
        url = reverse('maison-disponibles')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_filter_by_prix(self, api_client, maison):
        """Test filtrage par prix"""
        url = reverse('maison-list')
        response = api_client.get(url, {'prix_min': '100000', 'prix_max': '200000'})
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_filter_by_commune(self, api_client, maison):
        """Test filtrage par commune"""
        url = reverse('maison-list')
        response = api_client.get(url, {'commune': 'Cocody'})
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_search_maisons(self, api_client, maison):
        """Test recherche de maisons"""
        url = reverse('maison-list')
        response = api_client.get(url, {'search': 'Villa'})
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_ordering_maisons(self, api_client, maison):
        """Test tri des maisons"""
        url = reverse('maison-list')
        response = api_client.get(url, {'ordering': 'prix'})
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_delete_maison_as_admin(self, admin_client, maison):
        """Test suppression de maison par admin"""
        maison_id = maison.id
        url = reverse('maison-detail', kwargs={'pk': maison_id})
        response = admin_client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Maison.objects.filter(id=maison_id).exists()


@pytest.mark.django_db
class TestMaisonFilters:
    """Tests des filtres de maisons"""
    
    def test_filter_by_type_logement(self, api_client, maison):
        """Test filtrage par type de logement"""
        url = reverse('maison-list')
        response = api_client.get(url, {'type_logement': 'VILLA'})
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_filter_by_equipements(self, api_client, maison):
        """Test filtrage par équipements"""
        url = reverse('maison-list')
        response = api_client.get(url, {'meublee': 'false'})
        
        assert response.status_code == status.HTTP_200_OK
