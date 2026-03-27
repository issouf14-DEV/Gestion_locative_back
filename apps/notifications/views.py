"""
Vues pour le module notifications
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from django.utils import timezone

from .models import Notification
from .serializers import NotificationSerializer, NotificationCreateSerializer
from .services import NotificationService
from apps.core.permissions import IsAdminUser
from apps.core.mixins import CustomResponseMixin


class NotificationViewSet(CustomResponseMixin, viewsets.ModelViewSet):
    """
    ViewSet pour les notifications
    
    list: Liste les notifications de l'utilisateur
    retrieve: Détails d'une notification
    marquer_lue: Marquer une notification comme lue
    marquer_toutes_lues: Marquer toutes comme lues
    non_lues: Compter les notifications non lues
    """
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['type_notification', 'lu']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'envoyer':
            return NotificationCreateSerializer
        return NotificationSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin and self.action == 'list':
            # Les admins peuvent voir toutes les notifications
            return Notification.objects.all().select_related('destinataire')
        return Notification.objects.filter(destinataire=user)
    
    @action(detail=True, methods=['post'])
    def marquer_lue(self, request, pk=None):
        """Marquer une notification comme lue"""
        notification = self.get_object()
        notification.marquer_comme_lu()
        
        return self.success_response(
            data=NotificationSerializer(notification).data,
            message="Notification marquée comme lue"
        )
    
    @action(detail=False, methods=['post'])
    def marquer_toutes_lues(self, request):
        """Marquer toutes les notifications comme lues"""
        count = self.get_queryset().filter(lu=False).update(
            lu=True,
            date_lecture=timezone.now()
        )
        
        return self.success_response(
            data={'notifications_marquees': count},
            message=f"{count} notification(s) marquée(s) comme lue(s)"
        )
    
    @action(detail=False, methods=['get'])
    def non_lues(self, request):
        """Compte les notifications non lues"""
        count = self.get_queryset().filter(lu=False).count()
        
        return self.success_response(
            data={'count': count},
            message=f"{count} notification(s) non lue(s)"
        )
    
    @action(detail=False, methods=['get'])
    def recentes(self, request):
        """Récupère les 10 dernières notifications"""
        notifications = self.get_queryset()[:10]
        serializer = NotificationSerializer(notifications, many=True)
        
        return self.success_response(
            data=serializer.data,
            message="Notifications récentes"
        )
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, IsAdminUser])
    def envoyer(self, request):
        """
        Envoyer une notification à un ou plusieurs utilisateurs (Admin)
        
        Body:
            - destinataires: Liste d'IDs utilisateurs
            - titre: Titre de la notification
            - message: Message
            - type_notification: Type (optionnel, défaut: INFO)
        """
        serializer = NotificationCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            result = NotificationService.envoyer_notification_multiple(
                destinataires_ids=serializer.validated_data['destinataires'],
                titre=serializer.validated_data['titre'],
                message=serializer.validated_data['message'],
                type_notification=serializer.validated_data.get('type_notification', 'INFO')
            )
            return self.success_response(
                data=result,
                message=f"{result['envoyees']} notification(s) envoyée(s)"
            )
        
        return self.error_response(errors=serializer.errors)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, IsAdminUser])
    def envoyer_a_tous_locataires(self, request):
        """
        Envoyer une notification à tous les locataires (Admin)
        
        Body:
            - titre: Titre
            - message: Message
            - type_notification: Type (optionnel)
        """
        titre = request.data.get('titre')
        message = request.data.get('message')
        type_notif = request.data.get('type_notification', 'INFO')
        
        if not titre or not message:
            return self.error_response(
                message="Titre et message sont obligatoires",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        result = NotificationService.envoyer_a_tous_locataires(
            titre=titre,
            message=message,
            type_notification=type_notif
        )
        
        return self.success_response(
            data=result,
            message=f"Notification envoyée à {result['envoyees']} locataire(s)"
        )
    
    @action(detail=False, methods=['delete'])
    def supprimer_lues(self, request):
        """Supprime toutes les notifications lues"""
        count, _ = self.get_queryset().filter(lu=True).delete()
        
        return self.success_response(
            data={'supprimees': count},
            message=f"{count} notification(s) supprimée(s)"
        )
