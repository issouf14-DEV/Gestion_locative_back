"""
Middleware de santé : répond à /health/ avant la validation de l'hôte
et la redirection HTTPS, pour que le health check de Render passe toujours.
"""
from django.http import JsonResponse


class HealthCheckMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == '/health/':
            return JsonResponse({'status': 'ok'})
        return self.get_response(request)
