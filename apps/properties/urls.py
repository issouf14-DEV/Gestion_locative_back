"""
URLs pour le module properties
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MaisonViewSet, ImageMaisonViewSet

router = DefaultRouter()
router.register(r'maisons', MaisonViewSet, basename='maison')
router.register(r'images', ImageMaisonViewSet, basename='image-maison')

urlpatterns = [
    path('', include(router.urls)),
]
