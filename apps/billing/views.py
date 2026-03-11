"""
Vues pour le module billing
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse
from .models import Facture, IndexCompteur, FactureCollective, Compteur
from .serializers import (
    FactureSerializer, IndexCompteurSerializer, FactureCollectiveSerializer,
    RepartitionFactureSerializer, CompteurSerializer, CompteurAssignationSerializer,
    FactureNotificationSerializer
)
from .calculators import FactureCalculator
from .services import CompteurService, FactureNotificationService
from .reports import FacturePDFGenerator
from apps.core.permissions import IsAdminUser, IsOwnerOrAdmin
from apps.core.mixins import CustomResponseMixin


class CompteurViewSet(CustomResponseMixin, viewsets.ModelViewSet):
    """ViewSet pour les compteurs"""
    queryset = Compteur.objects.all()
    serializer_class = CompteurSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get_queryset(self):
        queryset = Compteur.objects.select_related('maison', 'locataire_actuel')
        
        # Filtres
        maison_id = self.request.query_params.get('maison')
        locataire_id = self.request.query_params.get('locataire')
        type_compteur = self.request.query_params.get('type')
        actif = self.request.query_params.get('actif')
        
        if maison_id:
            queryset = queryset.filter(maison_id=maison_id)
        if locataire_id:
            queryset = queryset.filter(locataire_actuel_id=locataire_id)
        if type_compteur:
            queryset = queryset.filter(type_compteur=type_compteur)
        if actif is not None:
            queryset = queryset.filter(actif=actif.lower() == 'true')
        
        return queryset
    
    @action(detail=False, methods=['post'])
    def assigner(self, request):
        """Assigner un compteur à un locataire"""
        serializer = CompteurAssignationSerializer(data=request.data)
        if serializer.is_valid():
            try:
                compteur = CompteurService.assigner_compteur_locataire(
                    compteur_id=serializer.validated_data['compteur_id'],
                    locataire_id=serializer.validated_data['locataire_id'],
                    index_initial=serializer.validated_data.get('index_initial')
                )
                return self.success_response(
                    data=CompteurSerializer(compteur).data,
                    message="Compteur assigné avec succès"
                )
            except Exception as e:
                return self.error_response(message=str(e))
        return self.error_response(errors=serializer.errors)
    
    @action(detail=True, methods=['post'])
    def liberer(self, request, pk=None):
        """Libérer un compteur d'un locataire"""
        try:
            compteur = CompteurService.liberer_compteur(compteur_id=pk)
            return self.success_response(
                data=CompteurSerializer(compteur).data,
                message="Compteur libéré avec succès"
            )
        except Exception as e:
            return self.error_response(message=str(e))
    
    @action(detail=False, methods=['get'])
    def par_locataire(self, request):
        """Lister les compteurs d'un locataire"""
        locataire_id = request.query_params.get('locataire_id')
        if not locataire_id:
            return self.error_response(message="locataire_id requis")
        
        compteurs = CompteurService.lister_compteurs_locataire(locataire_id)
        return self.success_response(
            data=CompteurSerializer(compteurs, many=True).data
        )


class FactureViewSet(CustomResponseMixin, viewsets.ModelViewSet):
    """ViewSet pour les factures"""
    queryset = Facture.objects.all()
    serializer_class = FactureSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin:
            return Facture.objects.all()
        return Facture.objects.filter(locataire=user)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, IsAdminUser])
    def repartir(self, request):
        """Répartir une facture collective SODECI/CIE"""
        serializer = RepartitionFactureSerializer(data=request.data)
        if serializer.is_valid():
            try:
                result = FactureCalculator.calculer_repartition(**serializer.validated_data)
                return self.success_response(data=result, message="Répartition effectuée avec succès")
            except Exception as e:
                return self.error_response(message=str(e))
        return self.error_response(errors=serializer.errors)
    
    @action(detail=True, methods=['post'])
    def envoyer_notification(self, request, pk=None):
        """Envoyer une notification pour une facture"""
        facture = self.get_object()
        canaux = request.data.get('canaux', ['email', 'app'])
        
        try:
            resultats = FactureNotificationService.envoyer_facture_tous_canaux(
                facture, canaux
            )
            return self.success_response(
                data=resultats,
                message="Notifications envoyées"
            )
        except Exception as e:
            return self.error_response(message=str(e))
    
    @action(detail=True, methods=['get'])
    def lien_whatsapp(self, request, pk=None):
        """
        Obtenir le lien WhatsApp pour une facture
        L'admin clique sur ce lien → WhatsApp Web s'ouvre avec le message pré-rempli
        """
        facture = self.get_object()
        
        try:
            result = FactureNotificationService.envoyer_facture_whatsapp(facture)
            return self.success_response(data=result)
        except Exception as e:
            return self.error_response(message=str(e))
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsAdminUser])
    def liens_whatsapp_mois(self, request):
        """
        Obtenir tous les liens WhatsApp pour les factures d'un mois
        L'admin peut ouvrir chaque lien pour envoyer via WhatsApp Web
        """
        mois = request.query_params.get('mois')
        annee = request.query_params.get('annee')
        type_facture = request.query_params.get('type')
        
        if not mois or not annee:
            return self.error_response(message="mois et annee requis")
        
        try:
            result = FactureNotificationService.generer_liens_whatsapp_mois(
                int(mois), int(annee), type_facture
            )
            return self.success_response(
                data=result,
                message=f"{result['nombre_factures']} liens WhatsApp générés"
            )
        except Exception as e:
            return self.error_response(message=str(e))
    
    @action(detail=True, methods=['get'])
    def telecharger_pdf(self, request, pk=None):
        """Télécharger le PDF d'une facture"""
        facture = self.get_object()
        
        try:
            pdf_buffer = FacturePDFGenerator.generer_facture_individuelle(facture)
            
            response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="facture_{facture.reference}.pdf"'
            return response
        except Exception as e:
            return self.error_response(message=str(e))
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsAdminUser])
    def rapport_mensuel(self, request):
        """Générer un rapport mensuel en PDF"""
        mois = request.query_params.get('mois')
        annee = request.query_params.get('annee')
        
        if not mois or not annee:
            return self.error_response(message="mois et annee requis")
        
        try:
            pdf_buffer = FacturePDFGenerator.generer_rapport_mensuel(
                int(mois), int(annee)
            )
            
            response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="rapport_{mois}_{annee}.pdf"'
            return response
        except Exception as e:
            return self.error_response(message=str(e))


class IndexCompteurViewSet(CustomResponseMixin, viewsets.ModelViewSet):
    """ViewSet pour les index de compteurs"""
    queryset = IndexCompteur.objects.all()
    serializer_class = IndexCompteurSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]


class FactureCollectiveViewSet(CustomResponseMixin, viewsets.ModelViewSet):
    """ViewSet pour les factures collectives"""
    queryset = FactureCollective.objects.all()
    serializer_class = FactureCollectiveSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]


class RappelLoyerViewSet(CustomResponseMixin, viewsets.ViewSet):
    """
    ViewSet pour envoyer des rappels de loyer aux locataires
    Via WhatsApp et/ou Email
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    @action(detail=False, methods=['post'])
    def envoyer_whatsapp(self, request):
        """
        Génère le lien WhatsApp pour envoyer un rappel de loyer
        
        Body:
            - locataire_id: ID du locataire (requis)
            - montant: Montant du loyer (requis)
            - mois: Mois (requis)
            - annee: Année (requis)
        
        Retourne un lien WhatsApp que l'admin peut ouvrir
        """
        from .services import RappelLoyerService
        from decimal import Decimal
        
        required = ['locataire_id', 'montant', 'mois', 'annee']
        for field in required:
            if not request.data.get(field):
                return self.error_response(message=f"Le champ '{field}' est requis")
        
        try:
            result = RappelLoyerService.envoyer_rappel_whatsapp(
                locataire_id=request.data['locataire_id'],
                montant=Decimal(str(request.data['montant'])),
                mois=int(request.data['mois']),
                annee=int(request.data['annee'])
            )
            return self.success_response(data=result)
        except Exception as e:
            return self.error_response(message=str(e))
    
    @action(detail=False, methods=['post'])
    def envoyer_email(self, request):
        """
        Envoie un rappel de loyer par email
        
        Body:
            - locataire_id: ID du locataire (requis)
            - montant: Montant du loyer (requis)
            - mois: Mois (requis)
            - annee: Année (requis)
        """
        from .services import RappelLoyerService
        from decimal import Decimal
        
        required = ['locataire_id', 'montant', 'mois', 'annee']
        for field in required:
            if not request.data.get(field):
                return self.error_response(message=f"Le champ '{field}' est requis")
        
        try:
            result = RappelLoyerService.envoyer_rappel_email(
                locataire_id=request.data['locataire_id'],
                montant=Decimal(str(request.data['montant'])),
                mois=int(request.data['mois']),
                annee=int(request.data['annee'])
            )
            return self.success_response(data=result, message=result.get('message'))
        except Exception as e:
            return self.error_response(message=str(e))
    
    @action(detail=False, methods=['post'])
    def envoyer_tous_canaux(self, request):
        """
        Envoie un rappel de loyer par email ET génère le lien WhatsApp
        
        Body:
            - locataire_id: ID du locataire (requis)
            - montant: Montant du loyer (requis)
            - mois: Mois (requis)
            - annee: Année (requis)
            - canaux: ['email', 'whatsapp'] (optionnel, défaut: les deux)
        """
        from .services import RappelLoyerService
        from decimal import Decimal
        
        required = ['locataire_id', 'montant', 'mois', 'annee']
        for field in required:
            if not request.data.get(field):
                return self.error_response(message=f"Le champ '{field}' est requis")
        
        try:
            result = RappelLoyerService.envoyer_rappel_tous_canaux(
                locataire_id=request.data['locataire_id'],
                montant=Decimal(str(request.data['montant'])),
                mois=int(request.data['mois']),
                annee=int(request.data['annee']),
                canaux=request.data.get('canaux')
            )
            return self.success_response(data=result)
        except Exception as e:
            return self.error_response(message=str(e))
    
    @action(detail=False, methods=['get'])
    def liens_whatsapp_mois(self, request):
        """
        Génère les liens WhatsApp pour tous les loyers impayés d'un mois
        
        Query params:
            - mois: Mois (requis)
            - annee: Année (requis)
        
        Retourne une liste de liens WhatsApp (un par locataire)
        """
        from .services import RappelLoyerService
        
        mois = request.query_params.get('mois')
        annee = request.query_params.get('annee')
        
        if not mois or not annee:
            return self.error_response(message="mois et annee requis")
        
        try:
            result = RappelLoyerService.generer_liens_whatsapp_loyers(
                int(mois), int(annee)
            )
            return self.success_response(
                data=result,
                message=f"{result['nombre_locataires']} lien(s) WhatsApp généré(s)"
            )
        except Exception as e:
            return self.error_response(message=str(e))
    
    @action(detail=False, methods=['post'])
    def envoyer_rappels_tous(self, request):
        """
        Envoie des rappels de loyer à tous les locataires avec loyers impayés
        
        Body:
            - mois: Mois (requis)
            - annee: Année (requis)
            - canaux: ['email', 'whatsapp'] (optionnel)
        
        Note: Pour WhatsApp, retourne les liens à ouvrir manuellement
        """
        from .services import RappelLoyerService
        
        mois = request.data.get('mois')
        annee = request.data.get('annee')
        
        if not mois or not annee:
            return self.error_response(message="mois et annee requis")
        
        try:
            result = RappelLoyerService.envoyer_rappels_tous_locataires(
                mois=int(mois),
                annee=int(annee),
                canaux=request.data.get('canaux')
            )
            return self.success_response(
                data=result,
                message=f"{result['nombre_rappels']} rappel(s) envoyé(s)"
            )
        except Exception as e:
            return self.error_response(message=str(e))