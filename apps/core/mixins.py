"""
Mixins réutilisables pour les vues
"""
from rest_framework import status
from rest_framework.response import Response


class CustomResponseMixin:
    """
    Mixin pour des réponses API uniformes
    """
    
    def success_response(self, data=None, message="Succès", status_code=status.HTTP_200_OK):
        """
        Réponse de succès standardisée
        """
        return Response({
            'success': True,
            'message': message,
            'data': data
        }, status=status_code)
    
    def error_response(self, message="Erreur", errors=None, status_code=status.HTTP_400_BAD_REQUEST):
        """
        Réponse d'erreur standardisée
        """
        return Response({
            'success': False,
            'message': message,
            'errors': errors or {}
        }, status=status_code)
