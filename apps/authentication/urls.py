"""
URLs pour l'authentification
"""
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    CustomTokenObtainPairView,
    register,
    login,
    logout,
    password_reset_request,
    password_reset_confirm,
    password_change,
    verify_email,
    google_login,
)

urlpatterns = [
    # Authentification JWT
    path('login/', login, name='auth-login'),
    path('register/', register, name='auth-register'),
    path('logout/', logout, name='auth-logout'),
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Réinitialisation mot de passe (oublié)
    path('password-reset/', password_reset_request, name='auth-password-reset'),
    path('password-reset/confirm/', password_reset_confirm, name='auth-password-reset-confirm'),
    
    # Changement de mot de passe (utilisateur connecté)
    path('password-change/', password_change, name='auth-password-change'),
    
    # Vérification email
    path('verify-email/<str:uid>/<str:token>/', verify_email, name='auth-verify-email'),
    
    # Authentification sociale
    path('google/', google_login, name='auth-google'),
]
