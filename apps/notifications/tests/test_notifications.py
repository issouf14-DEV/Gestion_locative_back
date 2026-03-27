"""
Tests pour le module notifications
"""
import pytest
from django.urls import reverse
from rest_framework import status

from apps.notifications.models import Notification
from apps.notifications.services import NotificationService


@pytest.mark.django_db
class TestNotificationModel:
    """Tests du modèle Notification"""
    
    def test_create_notification(self, locataire_user):
        """Test de création d'une notification"""
        notification = Notification.objects.create(
            destinataire=locataire_user,
            type_notification='INFO',
            titre='Test notification',
            message='Ceci est un test'
        )
        
        assert notification.destinataire == locataire_user
        assert notification.lu is False
        assert notification.titre == 'Test notification'
    
    def test_marquer_comme_lu(self, notification):
        """Test marquage comme lu"""
        assert notification.lu is False
        
        notification.marquer_comme_lu()
        
        assert notification.lu is True
        assert notification.date_lecture is not None
    
    def test_notification_str(self, notification):
        """Test de la représentation string"""
        assert notification.titre in str(notification)


@pytest.mark.django_db
class TestNotificationService:
    """Tests du service de notifications"""
    
    def test_creer_notification(self, locataire_user):
        """Test de création via le service"""
        notif = NotificationService.creer_notification(
            destinataire=locataire_user,
            titre='Nouvelle notification',
            message='Message de test',
            type_notification='SUCCESS',
            envoyer_email=False
        )
        
        assert notif is not None
        assert notif.titre == 'Nouvelle notification'
        assert notif.destinataire == locataire_user
    
    def test_envoyer_notification_multiple(self, locataire_user, second_locataire):
        """Test d'envoi à plusieurs utilisateurs"""
        result = NotificationService.envoyer_notification_multiple(
            destinataires_ids=[locataire_user.id, second_locataire.id],
            titre='Notification groupe',
            message='Message pour tous'
        )
        
        assert result['envoyees'] == 2
        
        # Vérifier que les deux ont reçu la notification
        assert Notification.objects.filter(
            destinataire=locataire_user,
            titre='Notification groupe'
        ).exists()
        assert Notification.objects.filter(
            destinataire=second_locataire,
            titre='Notification groupe'
        ).exists()
    
    def test_envoyer_a_tous_locataires(self, locataire_user, second_locataire):
        """Test d'envoi à tous les locataires"""
        result = NotificationService.envoyer_a_tous_locataires(
            titre='Annonce générale',
            message='Message pour tous les locataires'
        )
        
        assert result['envoyees'] >= 2
    
    def test_get_non_lues(self, locataire_user):
        """Test du comptage des non lues"""
        # Créer quelques notifications
        for i in range(3):
            Notification.objects.create(
                destinataire=locataire_user,
                titre=f'Notif {i}',
                message=f'Message {i}',
                lu=False
            )
        
        count = NotificationService.get_non_lues(str(locataire_user.id))
        assert count >= 3
    
    def test_marquer_toutes_lues(self, locataire_user):
        """Test du marquage de toutes comme lues"""
        # Créer des notifications non lues
        for i in range(3):
            Notification.objects.create(
                destinataire=locataire_user,
                titre=f'Notif {i}',
                message=f'Message {i}',
                lu=False
            )
        
        count = NotificationService.marquer_toutes_lues(str(locataire_user.id))
        
        assert count >= 3
        assert Notification.objects.filter(
            destinataire=locataire_user,
            lu=False
        ).count() == 0


@pytest.mark.django_db
class TestNotificationViewSet:
    """Tests des vues notifications"""
    
    def test_list_notifications(self, locataire_client, notification):
        """Test liste des notifications"""
        url = reverse('notification-list')
        response = locataire_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_locataire_sees_only_own_notifications(self, locataire_client, locataire_user, second_locataire):
        """Test qu'un locataire ne voit que ses notifications"""
        # Notification pour le locataire connecté
        Notification.objects.create(
            destinataire=locataire_user,
            titre='Ma notification',
            message='Test'
        )
        
        # Notification pour un autre locataire
        Notification.objects.create(
            destinataire=second_locataire,
            titre='Autre notification',
            message='Test'
        )
        
        url = reverse('notification-list')
        response = locataire_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        for notif in response.data['results']:
            assert str(notif['destinataire']) == str(locataire_user.id)
    
    def test_marquer_lue(self, locataire_client, notification):
        """Test marquage comme lue"""
        url = reverse('notification-marquer-lue', kwargs={'pk': notification.id})
        response = locataire_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        
        notification.refresh_from_db()
        assert notification.lu is True
    
    def test_marquer_toutes_lues(self, locataire_client, locataire_user):
        """Test marquage de toutes comme lues"""
        # Créer plusieurs notifications
        for i in range(3):
            Notification.objects.create(
                destinataire=locataire_user,
                titre=f'Notif {i}',
                message=f'Test {i}',
                lu=False
            )
        
        url = reverse('notification-marquer-toutes-lues')
        response = locataire_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        
        # Vérifier que toutes sont lues
        non_lues = Notification.objects.filter(
            destinataire=locataire_user,
            lu=False
        ).count()
        assert non_lues == 0
    
    def test_non_lues_count(self, locataire_client, notification):
        """Test du comptage des non lues"""
        url = reverse('notification-non-lues')
        response = locataire_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'count' in response.data['data']
    
    def test_recentes_endpoint(self, locataire_client, notification):
        """Test de l'endpoint récentes"""
        url = reverse('notification-recentes')
        response = locataire_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_envoyer_notification_as_admin(self, admin_client, locataire_user):
        """Test envoi de notification par admin"""
        url = reverse('notification-envoyer')
        data = {
            'destinataires': [locataire_user.id],
            'titre': 'Notification admin',
            'message': 'Message de l\'admin',
            'type_notification': 'INFO'
        }
        
        response = admin_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert Notification.objects.filter(
            destinataire=locataire_user,
            titre='Notification admin'
        ).exists()
    
    def test_envoyer_403_for_locataire(self, locataire_client, second_locataire):
        """Test que les locataires ne peuvent pas envoyer"""
        url = reverse('notification-envoyer')
        data = {
            'destinataires': [second_locataire.id],
            'titre': 'Test',
            'message': 'Test'
        }
        
        response = locataire_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_envoyer_a_tous_locataires(self, admin_client, locataire_user, second_locataire):
        """Test envoi à tous les locataires"""
        url = reverse('notification-envoyer-a-tous-locataires')
        data = {
            'titre': 'Annonce générale',
            'message': 'Information importante'
        }
        
        response = admin_client.post(url, data)
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_supprimer_lues(self, locataire_client, locataire_user):
        """Test suppression des notifications lues"""
        # Créer des notifications lues
        for i in range(3):
            Notification.objects.create(
                destinataire=locataire_user,
                titre=f'Notif {i}',
                message=f'Test {i}',
                lu=True
            )
        
        url = reverse('notification-supprimer-lues')
        response = locataire_client.delete(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['supprimees'] >= 3
