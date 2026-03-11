"""
Tests pour le module payments - Validation manuelle
"""
import pytest
from decimal import Decimal
from django.urls import reverse
from rest_framework import status
from io import BytesIO
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.payments.models import Paiement
from apps.payments.services import PaiementService


def create_test_image():
    """Crée une image de test pour les preuves de paiement"""
    image = Image.new('RGB', (100, 100), color='red')
    byte_io = BytesIO()
    image.save(byte_io, 'JPEG')
    byte_io.seek(0)
    return SimpleUploadedFile(
        name='test_preuve.jpg',
        content=byte_io.read(),
        content_type='image/jpeg'
    )


@pytest.mark.django_db
class TestPaiementModel:
    """Tests du modèle Paiement"""
    
    def test_create_paiement(self, locataire_user, facture_loyer):
        """Test de création d'un paiement"""
        paiement = Paiement.objects.create(
            locataire=locataire_user,
            montant=Decimal('150000.00'),
            factures_ids=[str(facture_loyer.id)],  # UUID en string
            preuve='payments/preuves/test.jpg',
            notes_locataire='Paiement via Orange Money'
        )
        
        assert paiement.reference.startswith('PAY-')
        assert paiement.statut == 'EN_ATTENTE'
        assert paiement.montant == Decimal('150000.00')
    
    def test_paiement_reference_auto_generated(self, locataire_user):
        """Test que la référence est auto-générée"""
        paiement = Paiement.objects.create(
            locataire=locataire_user,
            montant=Decimal('50000.00'),
            factures_ids=[],
            preuve='test.jpg'
        )
        
        assert paiement.reference is not None
        assert 'PAY' in paiement.reference
    
    def test_paiement_str(self, paiement_en_attente):
        """Test de la représentation string"""
        assert paiement_en_attente.reference in str(paiement_en_attente)
        assert str(paiement_en_attente.montant) in str(paiement_en_attente)


@pytest.mark.django_db
class TestPaiementService:
    """Tests du service de paiement"""
    
    def test_valider_paiement(self, admin_user, paiement_en_attente, facture_loyer):
        """Test de validation d'un paiement"""
        result = PaiementService.valider_paiement(
            paiement=paiement_en_attente,
            admin=admin_user,
            commentaire='Paiement reçu sur compte bancaire'
        )
        
        assert result['success'] is True
        assert result['statut'] == 'VALIDE'
        
        # Vérifier que le paiement a été mis à jour
        paiement_en_attente.refresh_from_db()
        assert paiement_en_attente.statut == 'VALIDE'
        assert paiement_en_attente.validateur == admin_user
        
        # Vérifier que la facture est marquée comme payée
        facture_loyer.refresh_from_db()
        assert facture_loyer.statut == 'PAYEE'
    
    def test_rejeter_paiement(self, admin_user, paiement_en_attente):
        """Test de rejet d'un paiement"""
        result = PaiementService.rejeter_paiement(
            paiement=paiement_en_attente,
            admin=admin_user,
            raison='Preuve de paiement illisible'
        )
        
        assert result['success'] is True
        assert result['statut'] == 'REJETE'
        
        paiement_en_attente.refresh_from_db()
        assert paiement_en_attente.statut == 'REJETE'
        assert 'illisible' in paiement_en_attente.commentaire_admin
    
    def test_rejeter_sans_raison_echoue(self, admin_user, paiement_en_attente):
        """Test que le rejet sans raison échoue"""
        with pytest.raises(ValueError) as excinfo:
            PaiementService.rejeter_paiement(
                paiement=paiement_en_attente,
                admin=admin_user,
                raison=''
            )
        
        assert "obligatoire" in str(excinfo.value)
    
    def test_valider_paiement_deja_valide_echoue(self, admin_user, paiement_en_attente):
        """Test qu'on ne peut pas valider un paiement déjà validé"""
        paiement_en_attente.statut = 'VALIDE'
        paiement_en_attente.save()
        
        with pytest.raises(ValueError) as excinfo:
            PaiementService.valider_paiement(
                paiement=paiement_en_attente,
                admin=admin_user,
                commentaire=''
            )
        
        assert "ne peut pas être validé" in str(excinfo.value)
    
    def test_get_paiements_en_attente(self, paiement_en_attente):
        """Test de récupération des paiements en attente"""
        paiements = PaiementService.get_paiements_en_attente()
        
        assert paiement_en_attente in paiements
    
    def test_get_statistiques_paiements(self, paiement_en_attente):
        """Test des statistiques de paiements"""
        stats = PaiementService.get_statistiques_paiements()
        
        assert stats['total_paiements'] >= 1
        assert stats['paiements_en_attente'] >= 1


@pytest.mark.django_db
class TestPaiementViewSet:
    """Tests des vues paiements"""
    
    def test_list_paiements_as_admin(self, admin_client, paiement_en_attente):
        """Test liste des paiements par admin"""
        url = reverse('paiement-list')
        response = admin_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_locataire_only_sees_own_paiements(self, locataire_client, paiement_en_attente, 
                                                second_locataire, locataire_user):
        """Test qu'un locataire ne voit que ses propres paiements"""
        # Créer un paiement pour un autre locataire
        Paiement.objects.create(
            locataire=second_locataire,
            montant=Decimal('100000.00'),
            factures_ids=[],
            preuve='test.jpg',
            statut='EN_ATTENTE'
        )
        
        url = reverse('paiement-list')
        response = locataire_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        for p in response.data['results']:
            assert str(p['locataire']) == str(locataire_user.id)
    
    def test_create_paiement(self, locataire_client, facture_loyer):
        """Test de soumission d'un paiement"""
        url = reverse('paiement-list')
        
        image = create_test_image()
        
        data = {
            'montant': '150000.00',
            'factures_ids': [str(facture_loyer.id)],
            'preuve': image,
            'notes_locataire': 'Paiement via Wave'
        }
        
        response = locataire_client.post(url, data, format='multipart')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert Paiement.objects.filter(montant=Decimal('150000.00')).exists()
    
    def test_valider_paiement_as_admin(self, admin_client, paiement_en_attente, facture_loyer):
        """Test validation par admin"""
        url = reverse('paiement-valider', kwargs={'pk': paiement_en_attente.id})
        data = {'commentaire': 'Vérifié sur le compte'}
        
        response = admin_client.post(url, data)
        
        assert response.status_code == status.HTTP_200_OK
        
        paiement_en_attente.refresh_from_db()
        assert paiement_en_attente.statut == 'VALIDE'
        
        facture_loyer.refresh_from_db()
        assert facture_loyer.statut == 'PAYEE'
    
    def test_rejeter_paiement_as_admin(self, admin_client, paiement_en_attente):
        """Test rejet par admin"""
        url = reverse('paiement-rejeter', kwargs={'pk': paiement_en_attente.id})
        data = {'commentaire': 'Montant incorrect'}
        
        response = admin_client.post(url, data)
        
        assert response.status_code == status.HTTP_200_OK
        
        paiement_en_attente.refresh_from_db()
        assert paiement_en_attente.statut == 'REJETE'
    
    def test_rejeter_sans_raison_400(self, admin_client, paiement_en_attente):
        """Test que le rejet sans raison retourne 400"""
        url = reverse('paiement-rejeter', kwargs={'pk': paiement_en_attente.id})
        data = {}
        
        response = admin_client.post(url, data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_valider_403_for_locataire(self, locataire_client, paiement_en_attente):
        """Test que les locataires ne peuvent pas valider"""
        url = reverse('paiement-valider', kwargs={'pk': paiement_en_attente.id})
        
        response = locataire_client.post(url, {})
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_en_attente_endpoint(self, admin_client, paiement_en_attente):
        """Test de l'endpoint paiements en attente"""
        url = reverse('paiement-en-attente')
        response = admin_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_statistiques_endpoint(self, admin_client, paiement_en_attente):
        """Test de l'endpoint statistiques"""
        url = reverse('paiement-statistiques')
        response = admin_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'total_paiements' in response.data['data']
    
    def test_mes_paiements_endpoint(self, locataire_client, paiement_en_attente):
        """Test de l'endpoint mes paiements"""
        url = reverse('paiement-mes-paiements')
        response = locataire_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestPaiementWorkflow:
    """Tests du workflow complet de paiement"""
    
    def test_workflow_paiement_valide(self, admin_user, locataire_user, facture_loyer):
        """Test du workflow complet: soumission -> validation"""
        # 1. Locataire soumet un paiement
        paiement = Paiement.objects.create(
            locataire=locataire_user,
            montant=facture_loyer.montant,
            factures_ids=[str(facture_loyer.id)],
            preuve='test.jpg',
            notes_locataire='Paiement effectué'
        )
        
        assert paiement.statut == 'EN_ATTENTE'
        assert facture_loyer.statut == 'EN_ATTENTE'
        assert locataire_user.dette_totale == facture_loyer.montant
        
        # 2. Admin valide le paiement
        PaiementService.valider_paiement(
            paiement=paiement,
            admin=admin_user,
            commentaire='OK'
        )
        
        # 3. Vérifier les mises à jour
        paiement.refresh_from_db()
        facture_loyer.refresh_from_db()
        locataire_user.refresh_from_db()
        
        assert paiement.statut == 'VALIDE'
        assert facture_loyer.statut == 'PAYEE'
        # La dette devrait être réduite
        assert locataire_user.statut == 'A_JOUR'
    
    def test_workflow_paiement_rejete_puis_resoumis(self, admin_user, locataire_user, facture_loyer):
        """Test du workflow: soumission -> rejet -> nouvelle soumission"""
        # 1. Premier paiement
        paiement1 = Paiement.objects.create(
            locataire=locataire_user,
            montant=facture_loyer.montant,
            factures_ids=[str(facture_loyer.id)],
            preuve='preuve1.jpg',
            notes_locataire='Premier essai'
        )
        
        # 2. Rejet
        PaiementService.rejeter_paiement(
            paiement=paiement1,
            admin=admin_user,
            raison='Photo floue'
        )
        
        assert paiement1.statut == 'REJETE'
        
        # 3. La facture reste impayée
        facture_loyer.refresh_from_db()
        assert facture_loyer.statut == 'EN_ATTENTE'
        
        # 4. Nouveau paiement
        paiement2 = Paiement.objects.create(
            locataire=locataire_user,
            montant=facture_loyer.montant,
            factures_ids=[str(facture_loyer.id)],
            preuve='preuve2.jpg',
            notes_locataire='Deuxième essai avec photo claire'
        )
        
        # 5. Validation
        PaiementService.valider_paiement(
            paiement=paiement2,
            admin=admin_user,
            commentaire='OK cette fois'
        )
        
        facture_loyer.refresh_from_db()
        assert facture_loyer.statut == 'PAYEE'
