"""
URL Configuration principale
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.views.generic import RedirectView
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)


def api_root(request):
    """Vue racine de l'API"""
    return JsonResponse({
        'message': 'Bienvenue sur l\'API Gestion Locative',
        'version': '1.0.0',
        'endpoints': {
            'documentation': '/api/docs/',
            'redoc': '/api/redoc/',
            'auth': '/api/auth/',
            'users': '/api/users/',
            'properties': '/api/properties/',
            'reservations': '/api/reservations/',
            'rentals': '/api/rentals/',
            'billing': '/api/billing/',
            'payments': '/api/payments/',
            'expenses': '/api/expenses/',
            'notifications': '/api/notifications/',
            'dashboard': '/api/dashboard/',
        }
    })


urlpatterns = [
    # Racine - Redirection vers la documentation
    path('', RedirectView.as_view(url='/api/docs/', permanent=False), name='root'),
    path('api/', api_root, name='api-root'),
    
    # Admin
    path('admin/', admin.site.urls),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # API Endpoints
    path('api/auth/', include('apps.authentication.urls')),
    path('api/users/', include('apps.users.urls')),
    path('api/properties/', include('apps.properties.urls')),
    path('api/reservations/', include('apps.reservations.urls')),
    path('api/rentals/', include('apps.rentals.urls')),
    path('api/billing/', include('apps.billing.urls')),
    path('api/payments/', include('apps.payments.urls')),
    path('api/expenses/', include('apps.expenses.urls')),
    path('api/notifications/', include('apps.notifications.urls')),
    path('api/dashboard/', include('apps.dashboard.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Customize admin site
admin.site.site_header = "Gestion Locative - Administration"
admin.site.site_title = "Gestion Locative Admin"
admin.site.index_title = "Tableau de bord administrateur"
