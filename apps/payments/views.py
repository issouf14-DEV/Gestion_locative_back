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


class EncaissementViewSet(CustomResponseMixin, viewsets.ViewSet):
    """
    ViewSet pour l'encaissement direct des loyers et factures (Admin)
    
    encaisser_loyer: Encaisser le loyer d'un locataire
    encaisser_facture: Encaisser une facture spécifique  
    encaisser_multiple: Encaisser plusieurs factures
    factures_impayees: Liste des factures impayées d'un locataire
    resume_mois: Résumé des encaissements du mois
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    @action(detail=False, methods=['post'])
    def encaisser_loyer(self, request):
        """
        Encaisser le loyer d'un locataire
        
        Body:
            - locataire_id: ID du locataire (requis)
            - mois: Mois du loyer (requis)
            - annee: Année (requis)
            - montant: Montant encaissé (requis)
            - mode_paiement: ESPECES, VIREMENT, MOBILE_MONEY, CHEQUE (défaut: ESPECES)
            - reference_paiement: Référence externe (optionnel)
            - notes: Notes (optionnel)
        """
        from .services import EncaissementService
        from decimal import Decimal
        
        required_fields = ['locataire_id', 'mois', 'annee', 'montant']
        for field in required_fields:
            if not request.data.get(field):
                return self.error_response(message=f"Le champ '{field}' est requis")
        
        try:
            result = EncaissementService.encaisser_loyer(
                locataire_id=request.data['locataire_id'],
                mois=int(request.data['mois']),
                annee=int(request.data['annee']),
                montant=Decimal(str(request.data['montant'])),
                mode_paiement=request.data.get('mode_paiement', 'ESPECES'),
                reference_paiement=request.data.get('reference_paiement', ''),
                notes=request.data.get('notes', ''),
                admin=request.user
            )
            return self.success_response(data=result, message=result['message'])
        except Exception as e:
            return self.error_response(message=str(e))
    
    @action(detail=False, methods=['post'])
    def encaisser_facture(self, request):
        """
        Encaisser une facture spécifique (loyer, SODECI, CIE, etc.)
        
        Body:
            - facture_id: ID de la facture (requis)
            - montant: Montant encaissé (requis)
            - mode_paiement: Mode de paiement (défaut: ESPECES)
            - reference_paiement: Référence externe (optionnel)
            - notes: Notes (optionnel)
        """
        from .services import EncaissementService
        from decimal import Decimal
        
        facture_id = request.data.get('facture_id')
        montant = request.data.get('montant')
        
        if not facture_id or not montant:
            return self.error_response(message="facture_id et montant sont requis")
        
        try:
            result = EncaissementService.encaisser_facture(
                facture_id=facture_id,
                montant=Decimal(str(montant)),
                mode_paiement=request.data.get('mode_paiement', 'ESPECES'),
                reference_paiement=request.data.get('reference_paiement', ''),
                notes=request.data.get('notes', ''),
                admin=request.user
            )
            return self.success_response(data=result, message=result['message'])
        except Exception as e:
            return self.error_response(message=str(e))
    
    @action(detail=False, methods=['post'])
    def encaisser_multiple(self, request):
        """
        Encaisser plusieurs factures en une seule opération
        
        Body:
            - factures_ids: Liste des IDs de factures (requis)
            - montant_total: Montant total encaissé (requis)
            - mode_paiement: Mode de paiement (défaut: ESPECES)
            - reference_paiement: Référence externe (optionnel)
            - notes: Notes (optionnel)
        """
        from .services import EncaissementService
        from decimal import Decimal
        
        factures_ids = request.data.get('factures_ids', [])
        montant_total = request.data.get('montant_total')
        
        if not factures_ids or not montant_total:
            return self.error_response(message="factures_ids et montant_total sont requis")
        
        try:
            result = EncaissementService.encaisser_multiple(
                factures_ids=factures_ids,
                montant_total=Decimal(str(montant_total)),
                mode_paiement=request.data.get('mode_paiement', 'ESPECES'),
                reference_paiement=request.data.get('reference_paiement', ''),
                notes=request.data.get('notes', ''),
                admin=request.user
            )
            return self.success_response(data=result, message=result['message'])
        except Exception as e:
            return self.error_response(message=str(e))
    
    @action(detail=False, methods=['get'])
    def factures_impayees(self, request):
        """
        Liste les factures impayées d'un locataire
        
        Query params:
            - locataire_id: ID du locataire (requis)
        """
        from .services import EncaissementService
        
        locataire_id = request.query_params.get('locataire_id')
        if not locataire_id:
            return self.error_response(message="locataire_id requis")
        
        try:
            factures = EncaissementService.get_factures_impayees_locataire(locataire_id)
            return self.success_response(
                data=factures,
                message=f"{len(factures)} facture(s) impayée(s)"
            )
        except Exception as e:
            return self.error_response(message=str(e))
    
    @action(detail=False, methods=['get'])
    def resume_mois(self, request):
        """
        Résumé des encaissements du mois
        
        Query params:
            - mois: Mois (requis)
            - annee: Année (requis)
        """
        from .services import EncaissementService
        
        mois = request.query_params.get('mois')
        annee = request.query_params.get('annee')
        
        if not mois or not annee:
            return self.error_response(message="mois et annee requis")
        
        try:
            resume = EncaissementService.get_resume_encaissements_mois(int(mois), int(annee))
            return self.success_response(data=resume)
        except Exception as e:
            return self.error_response(message=str(e))