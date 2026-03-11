from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PaiementViewSet, EncaissementViewSet

router = DefaultRouter()
router.register(r'paiements', PaiementViewSet, basename='paiement')
router.register(r'encaissements', EncaissementViewSet, basename='encaissement')

urlpatterns = [
    path('', include(router.urls)),
]
