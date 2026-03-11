"""
URLs pour le module billing
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FactureViewSet, IndexCompteurViewSet, FactureCollectiveViewSet

router = DefaultRouter()
router.register(r'factures', FactureViewSet, basename='facture')
router.register(r'index-compteurs', IndexCompteurViewSet, basename='index-compteur')
router.register(r'factures-collectives', FactureCollectiveViewSet, basename='facture-collective')

urlpatterns = [
    path('', include(router.urls)),
]
