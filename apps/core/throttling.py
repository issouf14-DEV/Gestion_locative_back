"""
Classes de throttling personnalisées pour la limitation de requêtes
"""
from rest_framework.throttling import AnonRateThrottle


class LoginRateThrottle(AnonRateThrottle):
    """
    Throttle pour les tentatives de connexion
    Limite: 5 tentatives par minute
    """
    scope = 'login'


class PasswordResetRateThrottle(AnonRateThrottle):
    """
    Throttle pour les demandes de réinitialisation de mot de passe
    Limite: 3 demandes par heure
    """
    scope = 'password_reset'


class RegisterRateThrottle(AnonRateThrottle):
    """
    Throttle pour les inscriptions
    Limite: 10 inscriptions par heure par IP
    """
    scope = 'anon'
