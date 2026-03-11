"""
Tests pour le module authentication
"""
import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
class TestAuthentication:
    """Tests d'authentification"""
    
    def test_register_user(self, api_client):
        """Test inscription d'un nouvel utilisateur"""
        url = reverse('auth-register')
        data = {
            'email': 'nouveau@example.com',
            'nom': 'Nouveau',
            'prenoms': 'Utilisateur',
            'telephone': '0707070707',
            'password': 'SecurePassword123!',
            'password_confirm': 'SecurePassword123!'
        }
        
        response = api_client.post(url, data)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert 'tokens' in response.data['data']
        assert 'user' in response.data['data']
    
    def test_register_password_mismatch(self, api_client):
        """Test inscription avec mots de passe différents"""
        url = reverse('auth-register')
        data = {
            'email': 'test@example.com',
            'nom': 'Test',
            'prenoms': 'User',
            'telephone': '0707070708',
            'password': 'Password123!',
            'password_confirm': 'DifferentPassword456!'
        }
        
        response = api_client.post(url, data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_register_duplicate_email(self, api_client, locataire_user):
        """Test inscription avec email existant"""
        url = reverse('auth-register')
        data = {
            'email': locataire_user.email,  # Email déjà utilisé
            'nom': 'Test',
            'prenoms': 'User',
            'telephone': '0707070709',
            'password': 'Password123!',
            'password_confirm': 'Password123!'
        }
        
        response = api_client.post(url, data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_login_success(self, api_client, locataire_user):
        """Test connexion réussie"""
        url = reverse('auth-login')
        data = {
            'email': locataire_user.email,
            'password': 'TestPassword123!'
        }
        
        response = api_client.post(url, data)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'tokens' in response.data['data']
        assert 'access' in response.data['data']['tokens']
        assert 'refresh' in response.data['data']['tokens']
    
    def test_login_wrong_password(self, api_client, locataire_user):
        """Test connexion avec mauvais mot de passe"""
        url = reverse('auth-login')
        data = {
            'email': locataire_user.email,
            'password': 'WrongPassword!'
        }
        
        response = api_client.post(url, data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_login_nonexistent_user(self, api_client):
        """Test connexion avec utilisateur inexistant"""
        url = reverse('auth-login')
        data = {
            'email': 'inexistant@example.com',
            'password': 'Password123!'
        }
        
        response = api_client.post(url, data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_token_refresh(self, api_client, locataire_user):
        """Test rafraîchissement du token"""
        # D'abord se connecter pour obtenir les tokens
        login_url = reverse('auth-login')
        login_data = {
            'email': locataire_user.email,
            'password': 'TestPassword123!'
        }
        login_response = api_client.post(login_url, login_data)
        refresh_token = login_response.data['data']['tokens']['refresh']
        
        # Utiliser le refresh token
        refresh_url = reverse('token_refresh')
        refresh_data = {'refresh': refresh_token}
        
        response = api_client.post(refresh_url, refresh_data)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
    
    def test_protected_route_without_token(self, api_client):
        """Test accès à une route protégée sans token"""
        url = reverse('user-me')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_protected_route_with_token(self, locataire_client, locataire_user):
        """Test accès à une route protégée avec token valide"""
        url = reverse('user-me')
        response = locataire_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['email'] == locataire_user.email


@pytest.mark.django_db
class TestPasswordSecurity:
    """Tests de sécurité des mots de passe"""
    
    def test_password_is_hashed(self, locataire_user):
        """Test que le mot de passe est hashé"""
        assert locataire_user.password != 'TestPassword123!'
        assert locataire_user.check_password('TestPassword123!')
    
    def test_weak_password_rejected(self, api_client):
        """Test qu'un mot de passe faible est rejeté"""
        url = reverse('auth-register')
        data = {
            'email': 'test@example.com',
            'nom': 'Test',
            'prenoms': 'User',
            'telephone': '0707070710',
            'password': '123',  # Trop court
            'password_confirm': '123'
        }
        
        response = api_client.post(url, data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_common_password_rejected(self, api_client):
        """Test qu'un mot de passe commun est rejeté"""
        url = reverse('auth-register')
        data = {
            'email': 'test2@example.com',
            'nom': 'Test',
            'prenoms': 'User',
            'telephone': '0707070711',
            'password': 'password123',  # Mot de passe commun
            'password_confirm': 'password123'
        }
        
        response = api_client.post(url, data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
