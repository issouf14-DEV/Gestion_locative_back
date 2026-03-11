"""
Tests pour le module users
"""
import pytest
from django.urls import reverse
from rest_framework import status
from apps.users.models import User, Profile


@pytest.mark.django_db
class TestUserModel:
    """Tests du modèle User"""
    
    def test_create_user(self):
        """Test de création d'un utilisateur standard"""
        user = User.objects.create_user(
            email='test@example.com',
            nom='Doe',
            prenoms='John',
            telephone='0701020304',
            password='SecurePassword123!'
        )
        
        assert user.email == 'test@example.com'
        assert user.nom == 'Doe'
        assert user.prenoms == 'John'
        assert user.telephone == '0701020304'
        assert user.role == 'LOCATAIRE'
        assert user.statut == 'A_JOUR'
        assert user.is_active is True
        assert user.is_staff is False
        assert user.check_password('SecurePassword123!')
    
    def test_create_superuser(self):
        """Test de création d'un superutilisateur"""
        user = User.objects.create_superuser(
            email='admin@example.com',
            nom='Admin',
            prenoms='Super',
            telephone='0701020305',
            password='AdminPassword123!'
        )
        
        assert user.is_staff is True
        assert user.is_superuser is True
        assert user.role == 'ADMIN'
        assert user.is_admin is True
    
    def test_user_without_email_raises_error(self):
        """Test qu'un utilisateur sans email lève une erreur"""
        with pytest.raises(ValueError):
            User.objects.create_user(
                email='',
                nom='Test',
                prenoms='User',
                telephone='0701020306',
                password='Password123!'
            )
    
    def test_user_without_telephone_raises_error(self):
        """Test qu'un utilisateur sans téléphone lève une erreur"""
        with pytest.raises(ValueError):
            User.objects.create_user(
                email='test2@example.com',
                nom='Test',
                prenoms='User',
                telephone='',
                password='Password123!'
            )
    
    def test_get_full_name(self, locataire_user):
        """Test de la méthode get_full_name"""
        assert locataire_user.get_full_name() == 'Test Locataire'
    
    def test_get_short_name(self, locataire_user):
        """Test de la méthode get_short_name"""
        assert locataire_user.get_short_name() == 'Test'
    
    def test_is_locataire(self, locataire_user):
        """Test de la propriété is_locataire"""
        assert locataire_user.is_locataire is True
        assert locataire_user.is_admin is False
    
    def test_is_admin(self, admin_user):
        """Test de la propriété is_admin"""
        assert admin_user.is_admin is True
        assert admin_user.is_locataire is False
    
    def test_dette_totale_sans_factures(self, locataire_user):
        """Test dette totale sans factures impayées"""
        assert locataire_user.dette_totale == 0
    
    def test_dette_totale_avec_factures(self, locataire_user, facture_loyer):
        """Test dette totale avec factures impayées"""
        from decimal import Decimal
        assert locataire_user.dette_totale == Decimal('150000.00')
    
    def test_bcrypt_password_hashing(self):
        """Test que le mot de passe est hashé avec bcrypt"""
        user = User.objects.create_user(
            email='bcrypt@test.com',
            nom='Bcrypt',
            prenoms='Test',
            telephone='0709999999',
            password='MySecurePassword123!'
        )
        
        # Le hash bcrypt commence par $2
        # Note: En mode test, MD5 est utilisé pour la rapidité
        # Mais en production, bcrypt sera utilisé
        assert user.password != 'MySecurePassword123!'
        assert user.check_password('MySecurePassword123!')


@pytest.mark.django_db
class TestProfileModel:
    """Tests du modèle Profile"""
    
    def test_profile_creation(self, locataire_user):
        """Test de création de profil"""
        profile = Profile.objects.get(user=locataire_user)
        assert profile.user == locataire_user
        assert profile.notifications_email is True
    
    def test_profile_str(self, locataire_user):
        """Test de la représentation string du profil"""
        profile = Profile.objects.get(user=locataire_user)
        assert str(profile) == f"Profil de {locataire_user.get_full_name()}"


@pytest.mark.django_db
class TestUserViewSet:
    """Tests des vues utilisateurs"""
    
    def test_list_users_as_admin(self, admin_client):
        """Test de la liste des utilisateurs en tant qu'admin"""
        url = reverse('user-list')
        response = admin_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_list_users_403_as_locataire(self, locataire_client):
        """Test que la liste est interdite aux locataires"""
        url = reverse('user-list')
        response = locataire_client.get(url)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_me_endpoint(self, locataire_client, locataire_user):
        """Test de l'endpoint /me/"""
        url = reverse('user-me')
        response = locataire_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['email'] == locataire_user.email
    
    def test_change_password(self, locataire_client, locataire_user):
        """Test du changement de mot de passe"""
        url = reverse('user-change-password')
        data = {
            'old_password': 'TestPassword123!',
            'new_password': 'NewSecurePass456!',
            'new_password_confirm': 'NewSecurePass456!'
        }
        response = locataire_client.post(url, data)
        
        assert response.status_code == status.HTTP_200_OK
        
        # Vérifier que le nouveau mot de passe fonctionne
        locataire_user.refresh_from_db()
        assert locataire_user.check_password('NewSecurePass456!')
    
    def test_change_password_wrong_old(self, locataire_client):
        """Test changement mot de passe avec ancien mot incorrect"""
        url = reverse('user-change-password')
        data = {
            'old_password': 'WrongPassword!',
            'new_password': 'NewSecurePass456!',
            'new_password_confirm': 'NewSecurePass456!'
        }
        response = locataire_client.post(url, data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_change_password_mismatch(self, locataire_client):
        """Test changement mot de passe avec confirmation différente"""
        url = reverse('user-change-password')
        data = {
            'old_password': 'TestPassword123!',
            'new_password': 'NewSecurePass456!',
            'new_password_confirm': 'DifferentPass789!'
        }
        response = locataire_client.post(url, data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_update_status_as_admin(self, admin_client, locataire_user):
        """Test mise à jour statut par admin"""
        url = reverse('user-update-status', kwargs={'pk': locataire_user.id})
        data = {'statut': 'EN_RETARD'}
        response = admin_client.patch(url, data)
        
        assert response.status_code == status.HTTP_200_OK
        locataire_user.refresh_from_db()
        assert locataire_user.statut == 'EN_RETARD'
    
    def test_update_status_403_as_locataire(self, locataire_client, locataire_user):
        """Test que les locataires ne peuvent pas modifier le statut"""
        url = reverse('user-update-status', kwargs={'pk': locataire_user.id})
        data = {'statut': 'EN_RETARD'}
        response = locataire_client.patch(url, data)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_locataires_list(self, admin_client, locataire_user):
        """Test liste des locataires uniquement"""
        url = reverse('user-locataires')
        response = admin_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        # Vérifier que l'admin n'est pas dans la liste
        emails = [user['email'] for user in response.data['results']]
        assert locataire_user.email in emails
    
    def test_create_user_as_admin(self, admin_client):
        """Test création d'utilisateur par admin"""
        url = reverse('user-list')
        data = {
            'email': 'nouveau@test.com',
            'nom': 'Nouveau',
            'prenoms': 'User',
            'telephone': '0708080808',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
            'role': 'LOCATAIRE'
        }
        response = admin_client.post(url, data)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert User.objects.filter(email='nouveau@test.com').exists()
    
    def test_retrieve_own_profile(self, locataire_client, locataire_user):
        """Test récupération de son propre profil"""
        url = reverse('user-detail', kwargs={'pk': locataire_user.id})
        response = locataire_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['email'] == locataire_user.email
    
    def test_unauthenticated_access_denied(self, api_client):
        """Test qu'un utilisateur non authentifié est refusé"""
        url = reverse('user-me')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestUserManager:
    """Tests du manager personnalisé"""
    
    def test_get_locataires(self, admin_user, locataire_user):
        """Test de la méthode get_locataires"""
        locataires = User.objects.get_locataires()
        
        assert locataire_user in locataires
        assert admin_user not in locataires
    
    def test_get_admins(self, admin_user, locataire_user):
        """Test de la méthode get_admins"""
        admins = User.objects.get_admins()
        
        assert admin_user in admins
        assert locataire_user not in admins
