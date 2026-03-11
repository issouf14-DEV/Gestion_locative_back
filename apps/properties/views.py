"""
Vues pour le module properties
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import Maison, ImageMaison
from .serializers import (
    MaisonListSerializer, MaisonDetailSerializer,
    MaisonCreateUpdateSerializer, ImageMaisonSerializer,
    ImageMaisonCreateSerializer
)
from .filters import MaisonFilter
from apps.core.permissions import IsAdminUser, IsAdminOrReadOnly
from apps.core.mixins import CustomResponseMixin


class MaisonViewSet(CustomResponseMixin, viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des maisons
    
    list: Liste toutes les maisons (public)
    retrieve: Détails d'une maison (public)
    create: Créer une maison (Admin uniquement)
    update: Modifier une maison (Admin uniquement)
    destroy: Supprimer une maison (Admin uniquement)
    """
    queryset = Maison.objects.prefetch_related('images').all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = MaisonFilter
    search_fields = ['titre', 'description', 'commune', 'quartier', 'reference']
    ordering_fields = ['prix', 'created_at', 'nombre_vues', 'superficie']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Retourne le serializer approprié selon l'action"""
        if self.action == 'list':
            return MaisonListSerializer
        elif self.action == 'retrieve':
            return MaisonDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return MaisonCreateUpdateSerializer
        return MaisonDetailSerializer
    
    def get_permissions(self):
        """Définit les permissions selon l'action"""
        if self.action in ['list', 'retrieve', 'disponibles']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated, IsAdminUser]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Filtre le queryset selon le rôle"""
        queryset = super().get_queryset()
        
        # Les visiteurs ne voient que les maisons disponibles
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(statut='DISPONIBLE')
        
        return queryset
    
    def retrieve(self, request, *args, **kwargs):
        """Incrémente le nombre de vues lors de la consultation"""
        instance = self.get_object()
        
        # Incrémenter le nombre de vues
        instance.nombre_vues += 1
        instance.save(update_fields=['nombre_vues'])
        
        serializer = self.get_serializer(instance)
        return self.success_response(
            data=serializer.data,
            message="Détails de la maison récupérés avec succès"
        )
    
    @action(detail=False, methods=['get'], permission_classes=[AllowAny], authentication_classes=[])
    def disponibles(self, request):
        """
        Retourne uniquement les maisons disponibles
        """
        maisons = self.get_queryset().filter(statut='DISPONIBLE')
        
        page = self.paginate_queryset(maisons)
        if page is not None:
            serializer = MaisonListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = MaisonListSerializer(maisons, many=True)
        return self.success_response(
            data=serializer.data,
            message="Maisons disponibles récupérées avec succès"
        )
    
    @action(detail=True, methods=['patch'], permission_classes=[IsAuthenticated, IsAdminUser])
    def changer_statut(self, request, pk=None):
        """
        Change le statut d'une maison (Admin uniquement)
        """
        maison = self.get_object()
        statut = request.data.get('statut')
        
        if statut not in ['DISPONIBLE', 'LOUEE', 'EN_MAINTENANCE', 'INDISPONIBLE']:
            return self.error_response(
                message="Statut invalide",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        maison.statut = statut
        maison.save()
        
        return self.success_response(
            data=MaisonDetailSerializer(maison).data,
            message=f"Statut changé à '{statut}'"
        )
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAdminUser])
    def ajouter_images(self, request, pk=None):
        """
        Ajoute des images à une maison (Admin uniquement)
        """
        maison = self.get_object()
        images = request.FILES.getlist('images')
        
        if not images:
            return self.error_response(
                message="Aucune image fournie",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        images_creees = []
        for index, image in enumerate(images):
            image_obj = ImageMaison.objects.create(
                maison=maison,
                image=image,
                ordre=index,
                est_principale=(index == 0 and not maison.images.filter(est_principale=True).exists())
            )
            images_creees.append(image_obj)
        
        serializer = ImageMaisonSerializer(images_creees, many=True)
        return self.success_response(
            data=serializer.data,
            message=f"{len(images_creees)} image(s) ajoutée(s) avec succès",
            status_code=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['get'], permission_classes=[AllowAny])
    def images(self, request, pk=None):
        """
        Retourne toutes les images d'une maison
        """
        maison = self.get_object()
        images = maison.images.all()
        
        serializer = ImageMaisonSerializer(images, many=True)
        return self.success_response(
            data=serializer.data,
            message="Images récupérées avec succès"
        )


class ImageMaisonViewSet(CustomResponseMixin, viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des images de maisons
    """
    queryset = ImageMaison.objects.all()
    serializer_class = ImageMaisonSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ImageMaisonCreateSerializer
        return ImageMaisonSerializer
    
    @action(detail=True, methods=['patch'], permission_classes=[IsAuthenticated, IsAdminUser])
    def definir_principale(self, request, pk=None):
        """
        Définit une image comme image principale
        """
        image = self.get_object()
        image.est_principale = True
        image.save()
        
        return self.success_response(
            data=ImageMaisonSerializer(image).data,
            message="Image définie comme principale"
        )
