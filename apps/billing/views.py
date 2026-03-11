"""
Vues pour le module billing
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Facture, IndexCompteur, FactureCollective
from .serializers import *
from .calculators import FactureCalculator
from apps.core.permissions import IsAdminUser, IsOwnerOrAdmin
from apps.core.mixins import CustomResponseMixin


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
