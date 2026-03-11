"""
Vues pour le module rentals - Gestion des locations
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import Location
from .serializers import (
    LocationSerializer, LocationCreateSerializer,
    LocationDetailSerializer, LocationRenouvellementSerializer,
    LocationResiliationSerializer
)
from .services import LocationService
from apps.core.permissions import IsAdminUser, IsOwnerOrAdmin
from apps.core.mixins import CustomResponseMixin


class LocationViewSet(CustomResponseMixin, viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des locations
    
    list: Liste toutes les locations (admin) ou la sienne (locataire)
    retrieve: Détails d'une location
    create: Créer une nouvelle location (admin)
    renouveler: Renouveler une location (admin)
    resilier: Résilier une location (admin)
    """
    queryset = Location.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['statut', 'locataire', 'maison']
    search_fields = ['numero_contrat', 'locataire__nom', 'locataire__prenoms', 'maison__titre']
    ordering_fields = ['date_debut', 'date_fin', 'loyer_mensuel', 'created_at']
    ordering = ['-date_debut']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return LocationCreateSerializer
        elif self.action == 'retrieve':
            return LocationDetailSerializer
        elif self.action == 'renouveler':
            return LocationRenouvellementSerializer
        elif self.action == 'resilier':
            return LocationResiliationSerializer
        return LocationSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy', 
                          'renouveler', 'resilier', 'statistiques', 'expirant']:
            permission_classes = [IsAuthenticated, IsAdminUser]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        user = self.request.user
        queryset = Location.objects.select_related('locataire', 'maison')
        
        if user.is_admin:
            return queryset.all()
        return queryset.filter(locataire=user)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def ma_location(self, request):
        """
        Récupère la location active du locataire connecté
        """
        location = LocationService.get_location_active(str(request.user.id))
        
        if not location:
            return self.error_response(
                message="Vous n'avez pas de location active",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        serializer = LocationDetailSerializer(location)
        return self.success_response(
            data=serializer.data,
            message="Location active récupérée"
        )
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAdminUser])
    def renouveler(self, request, pk=None):
        """
        Renouveler une location (Admin)
        
        Body:
            - duree_supplementaire_mois: Nombre de mois à ajouter
        """
        location = self.get_object()
        serializer = LocationRenouvellementSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                result = LocationService.renouveler_location(
                    location=location,
                    duree_supplementaire_mois=serializer.validated_data['duree_supplementaire_mois']
                )
                return self.success_response(
                    data=result,
                    message="Location renouvelée avec succès"
                )
            except ValueError as e:
                return self.error_response(message=str(e))
        
        return self.error_response(errors=serializer.errors)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAdminUser])
    def resilier(self, request, pk=None):
        """
        Résilier une location (Admin)
        
        Body (optionnel):
            - raison: Raison de la résiliation
        """
        location = self.get_object()
        raison = request.data.get('raison', '')
        
        try:
            result = LocationService.resilier_location(
                location=location,
                raison=raison
            )
            return self.success_response(
                data=result,
                message="Location résiliée"
            )
        except ValueError as e:
            return self.error_response(message=str(e))
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsAdminUser])
    def actives(self, request):
        """
        Liste toutes les locations actives (Admin)
        """
        locations = Location.objects.filter(statut='ACTIVE').select_related('locataire', 'maison')
        
        page = self.paginate_queryset(locations)
        if page is not None:
            serializer = LocationSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = LocationSerializer(locations, many=True)
        return self.success_response(
            data=serializer.data,
            message=f"{locations.count()} location(s) active(s)"
        )
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsAdminUser])
    def expirant(self, request):
        """
        Liste les locations qui expirent bientôt (Admin)
        
        Query params:
            - jours: Nombre de jours (défaut: 30)
        """
        jours = int(request.query_params.get('jours', 30))
        locations = LocationService.get_locations_expirant_bientot(jours=jours)
        
        serializer = LocationSerializer(locations, many=True)
        return self.success_response(
            data=serializer.data,
            message=f"{len(locations)} location(s) expirant dans les {jours} prochains jours"
        )
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsAdminUser])
    def statistiques(self, request):
        """
        Statistiques des locations (Admin)
        """
        stats = LocationService.get_statistiques_locations()
        return self.success_response(
            data=stats,
            message="Statistiques des locations"
        )

