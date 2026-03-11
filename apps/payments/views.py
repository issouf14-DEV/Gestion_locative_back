"""
Vues pour le module payments - Validation manuelle des paiements
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import Paiement
from .serializers import PaiementSerializer, PaiementCreateSerializer, PaiementValidationSerializer
from .services import PaiementService
from apps.core.permissions import IsAdminUser
from apps.core.mixins import CustomResponseMixin


class PaiementViewSet(CustomResponseMixin, viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des paiements
    
    list: Liste les paiements (admin: tous, locataire: les siens)
    retrieve: Détails d'un paiement
    create: Soumettre un paiement (locataire)
    valider: Valider un paiement (admin)
    rejeter: Rejeter un paiement (admin)
    """
    queryset = Paiement.objects.all()
    parser_classes = [MultiPartParser, FormParser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['statut', 'locataire']
    search_fields = ['reference', 'locataire__nom', 'locataire__prenoms']
    ordering_fields = ['created_at', 'montant', 'date_validation']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return PaiementCreateSerializer
        elif self.action in ['valider', 'rejeter']:
            return PaiementValidationSerializer
        return PaiementSerializer
    
    def get_permissions(self):
        if self.action in ['valider', 'rejeter', 'en_attente', 'statistiques']:
            permission_classes = [IsAuthenticated, IsAdminUser]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin:  # type: ignore[union-attr]
            return Paiement.objects.all().select_related('locataire', 'validateur')
        return Paiement.objects.filter(locataire=user).select_related('validateur')
    
    def perform_create(self, serializer):
        """Crée un paiement pour le locataire connecté"""
        serializer.save(locataire=self.request.user)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsAdminUser])
    def en_attente(self, request):
        """
        Liste tous les paiements en attente de validation (Admin)
        """
        paiements = PaiementService.get_paiements_en_attente()
        
        page = self.paginate_queryset(paiements)
        if page is not None:
            serializer = PaiementSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = PaiementSerializer(paiements, many=True)
        return self.success_response(
            data=serializer.data,
            message=f"{len(paiements)} paiement(s) en attente"
        )
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAdminUser])
    def valider(self, request, pk=None):
        """
        Valider un paiement (Admin uniquement)
        
        Body (optionnel):
            - commentaire: Commentaire de validation
        """
        paiement = self.get_object()
        commentaire = request.data.get('commentaire', '')
        
        try:
            result = PaiementService.valider_paiement(
                paiement=paiement,
                admin=request.user,
                commentaire=commentaire
            )
            return self.success_response(
                data=result,
                message="Paiement validé avec succès"
            )
        except ValueError as e:
            return self.error_response(message=str(e))
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAdminUser])
    def rejeter(self, request, pk=None):
        """
        Rejeter un paiement (Admin uniquement)
        
        Body:
            - commentaire: Raison du rejet (obligatoire)
        """
        paiement = self.get_object()
        raison = request.data.get('commentaire', '')
        
        if not raison:
            return self.error_response(
                message="Une raison de rejet est obligatoire",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            result = PaiementService.rejeter_paiement(
                paiement=paiement,
                admin=request.user,
                raison=raison
            )
            return self.success_response(
                data=result,
                message="Paiement rejeté"
            )
        except ValueError as e:
            return self.error_response(message=str(e))
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsAdminUser])
    def statistiques(self, request):
        """
        Obtenir les statistiques des paiements (Admin)
        
        Query params optionnels:
            - mois: Mois (1-12)
            - annee: Année
        """
        mois = request.query_params.get('mois')
        annee = request.query_params.get('annee')
        
        stats = PaiementService.get_statistiques_paiements(
            mois=int(mois) if mois else None,
            annee=int(annee) if annee else None
        )
        
        return self.success_response(
            data=stats,
            message="Statistiques récupérées avec succès"
        )
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def mes_paiements(self, request):
        """
        Liste des paiements du locataire connecté
        """
        paiements = Paiement.objects.filter(
            locataire=request.user
        ).order_by('-created_at')
        
        page = self.paginate_queryset(paiements)
        if page is not None:
            serializer = PaiementSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = PaiementSerializer(paiements, many=True)
        return self.success_response(
            data=serializer.data,
            message="Historique de vos paiements"
        )

