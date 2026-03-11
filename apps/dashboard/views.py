"""
Vues pour le dashboard
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Sum, Count, Q
from apps.core.permissions import IsAdminUser
from apps.core.mixins import CustomResponseMixin
from .serializers import DashboardStatsSerializer
from .services import DashboardService


class DashboardStatsView(CustomResponseMixin, APIView):
    """
    Vue pour les statistiques du dashboard admin
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get(self, request):
        stats = DashboardService.get_admin_stats()
        serializer = DashboardStatsSerializer(stats)
        return self.success_response(
            data=serializer.data,
            message="Statistiques récupérées avec succès"
        )


class LocataireDashboardView(CustomResponseMixin, APIView):
    """
    Vue pour le dashboard d'un locataire
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        stats = DashboardService.get_locataire_stats(request.user)
        return self.success_response(
            data=stats,
            message="Informations récupérées avec succès"
        )
