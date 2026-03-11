"""
Gestionnaire d'exceptions personnalisé
"""
from rest_framework.views import exception_handler
from rest_framework import status
from rest_framework.response import Response


def custom_exception_handler(exc, context):
    """
    Gestionnaire d'exceptions personnalisé pour des réponses d'erreur uniformes
    """
    response = exception_handler(exc, context)
    
    if response is not None:
        custom_response = {
            'error': True,
            'message': '',
            'details': {}
        }
        
        if isinstance(response.data, dict):
            # Extraire le message d'erreur principal
            if 'detail' in response.data:
                custom_response['message'] = response.data['detail']
            else:
                custom_response['details'] = response.data
                custom_response['message'] = "Erreur de validation"
        elif isinstance(response.data, list):
            custom_response['message'] = response.data[0] if response.data else "Une erreur s'est produite"
        else:
            custom_response['message'] = str(response.data)
        
        response.data = custom_response
    
    return response


class CustomAPIException(Exception):
    """
    Exception personnalisée pour l'API
    """
    def __init__(self, message, status_code=status.HTTP_400_BAD_REQUEST, details=None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)
