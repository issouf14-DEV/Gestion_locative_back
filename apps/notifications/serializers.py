"""
Serializers pour le module notifications
"""
from rest_framework import serializers
from .models import Notification
from apps.users.models import User


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer pour les notifications"""
    destinataire_nom = serializers.CharField(source='destinataire.get_full_name', read_only=True)
    type_display = serializers.CharField(source='get_type_notification_display', read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id', 'destinataire', 'destinataire_nom',
            'type_notification', 'type_display',
            'titre', 'message', 'lu', 'date_lecture',
            'lien', 'metadata', 'created_at'
        ]
        read_only_fields = ['id', 'destinataire', 'date_lecture', 'created_at']


class NotificationCreateSerializer(serializers.Serializer):
    """Serializer pour créer des notifications"""
    destinataires = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        help_text="Liste des IDs des destinataires"
    )
    titre = serializers.CharField(max_length=200)
    message = serializers.CharField()
    type_notification = serializers.ChoiceField(
        choices=Notification.TYPE_CHOICES,
        default='INFO'
    )
    lien = serializers.CharField(required=False, allow_blank=True, max_length=500)
    
    def validate_destinataires(self, value):
        """Vérifie que les destinataires existent"""
        users = User.objects.filter(id__in=value, is_active=True)
        if users.count() != len(value):
            raise serializers.ValidationError(
                "Certains destinataires n'existent pas ou sont inactifs"
            )
        return value


class NotificationListeSerializer(serializers.ModelSerializer):
    """Serializer simplifié pour la liste"""
    
    class Meta:
        model = Notification
        fields = ['id', 'titre', 'type_notification', 'lu', 'created_at']
