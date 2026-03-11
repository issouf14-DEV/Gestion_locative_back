"""
Vues pour le module users
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import User, Profile
from .serializers import (
    UserSerializer, UserCreateSerializer, UserUpdateSerializer,
    ChangePasswordSerializer, UserDetailSerializer, ProfileSerializer
)
from apps.core.permissions import IsAdminUser, IsOwnerOrAdmin
from apps.core.mixins import CustomResponseMixin


class UserViewSet(CustomResponseMixin, viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des utilisateurs
    
    list: Liste tous les utilisateurs (Admin uniquement)
    retrieve: Détails d'un utilisateur
    create: Créer un nouvel utilisateur (Admin uniquement)
    update: Mettre à jour un utilisateur
    destroy: Supprimer un utilisateur (Admin uniquement)
    """
    queryset = User.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['role', 'statut', 'is_active']
    search_fields = ['email', 'nom', 'prenoms', 'telephone']
    ordering_fields = ['date_joined', 'nom', 'prenoms']
    ordering = ['-date_joined']
    
    def get_serializer_class(self):
        """Retourne le serializer approprié selon l'action"""
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        elif self.action == 'retrieve':
            return UserDetailSerializer
        return UserSerializer
    
    def get_permissions(self):
        """Définit les permissions selon l'action"""
        if self.action in ['create', 'list', 'destroy', 'update_status', 'locataires']:
            permission_classes = [IsAuthenticated, IsAdminUser]
        elif self.action in ['update', 'partial_update', 'retrieve', 'profile']:
            permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Retourne le queryset approprié selon le rôle"""
        user = self.request.user
        if user.is_admin:  # type: ignore[union-attr]
            return User.objects.all()
        return User.objects.filter(id=user.id)  # type: ignore[union-attr]
    
    def retrieve(self, request, *args, **kwargs):
        """Récupère les détails d'un utilisateur avec réponse standardisée"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return self.success_response(
            data=serializer.data,
            message="Utilisateur récupéré avec succès"
        )
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """
        Retourne les informations de l'utilisateur connecté
        """
        serializer = UserDetailSerializer(request.user)
        return self.success_response(
            data=serializer.data,
            message="Informations de l'utilisateur récupérées avec succès"
        )
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def change_password(self, request):
        """
        Permet à l'utilisateur de changer son mot de passe
        """
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])  # type: ignore[index]
            user.save()
            
            return self.success_response(
                message="Mot de passe modifié avec succès"
            )
        
        return self.error_response(
            message="Erreur de validation",
            errors=serializer.errors
        )
    
    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """
        Met à jour le statut d'un locataire (Admin uniquement)
        """
        # La permission est vérifiée via get_permissions()
        user = self.get_object()
        statut = request.data.get('statut')
        
        if statut not in ['A_JOUR', 'EN_RETARD', 'SUSPENDU']:
            return self.error_response(
                message="Statut invalide",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        user.statut = statut
        user.save()
        
        return self.success_response(
            data=UserSerializer(user).data,
            message=f"Statut mis à jour à '{statut}'"
        )
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsAdminUser])
    def locataires(self, request):
        """
        Retourne uniquement les locataires (Admin uniquement)
        """
        locataires = User.objects.get_locataires()  # type: ignore[attr-defined]
        
        # Filtres optionnels
        statut = request.query_params.get('statut', None)
        if statut:
            locataires = locataires.filter(statut=statut)
        
        page = self.paginate_queryset(locataires)
        if page is not None:
            serializer = UserSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = UserSerializer(locataires, many=True)
        return self.success_response(
            data=serializer.data,
            message="Liste des locataires récupérée avec succès"
        )
    
    @action(detail=True, methods=['get', 'patch'], permission_classes=[IsAuthenticated, IsOwnerOrAdmin])
    def profile(self, request, pk=None):
        """
        Récupère ou met à jour le profil d'un utilisateur
        """
        user = self.get_object()
        profile, created = Profile.objects.get_or_create(user=user)
        
        if request.method == 'GET':
            serializer = ProfileSerializer(profile)
            return self.success_response(
                data=serializer.data,
                message="Profil récupéré avec succès"
            )
        
        elif request.method == 'PATCH':
            serializer = ProfileSerializer(profile, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return self.success_response(
                    data=serializer.data,
                    message="Profil mis à jour avec succès"
                )
            return self.error_response(
                message="Erreur de validation",
                errors=serializer.errors
            )
