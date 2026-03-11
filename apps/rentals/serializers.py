"""
Serializers pour le module rentals
"""
from rest_framework import serializers
from .models import Location
from apps.users.serializers import UserSerializer
from apps.properties.serializers import MaisonListSerializer


class LocationSerializer(serializers.ModelSerializer):
    """Serializer complet pour les locations"""
    locataire_nom = serializers.CharField(source='locataire.get_full_name', read_only=True)
    locataire_email = serializers.CharField(source='locataire.email', read_only=True)
    maison_titre = serializers.CharField(source='maison.titre', read_only=True)
    maison_adresse = serializers.CharField(source='maison.adresse', read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    duree_restante = serializers.SerializerMethodField()
    
    class Meta:
        model = Location
        fields = [
            'id', 'numero_contrat', 'locataire', 'locataire_nom', 'locataire_email',
            'maison', 'maison_titre', 'maison_adresse',
            'date_debut', 'date_fin', 'duree_mois', 'duree_restante',
            'loyer_mensuel', 'caution_versee', 'statut', 'statut_display',
            'contrat_pdf', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'numero_contrat', 'created_at', 'updated_at']
    
    def get_duree_restante(self, obj):
        """Calcule la durée restante"""
        from .services import LocationService
        return LocationService.calculer_duree_restante(obj)


class LocationCreateSerializer(serializers.ModelSerializer):
    """Serializer pour créer une location"""
    
    class Meta:
        model = Location
        fields = [
            'locataire', 'maison', 'date_debut', 'duree_mois',
            'loyer_mensuel', 'caution_versee', 'notes'
        ]
    
    def validate_maison(self, value):
        """Vérifie que la maison est disponible"""
        if value.statut != 'DISPONIBLE':
            raise serializers.ValidationError(
                f"Cette maison n'est pas disponible (statut: {value.get_statut_display()})"
            )
        return value
    
    def validate_locataire(self, value):
        """Vérifie que le locataire n'a pas déjà une location active"""
        location_active = Location.objects.filter(
            locataire=value,
            statut='ACTIVE'
        ).first()
        
        if location_active:
            raise serializers.ValidationError(
                f"Ce locataire a déjà une location active ({location_active.numero_contrat})"
            )
        return value
    
    def validate_duree_mois(self, value):
        """Vérifie que la durée est valide"""
        if value < 1:
            raise serializers.ValidationError("La durée doit être d'au moins 1 mois")
        if value > 60:
            raise serializers.ValidationError("La durée ne peut pas dépasser 60 mois")
        return value
    
    def create(self, validated_data):
        """Crée la location avec calcul de la date de fin"""
        from .services import LocationService
        
        date_debut = validated_data['date_debut']
        duree_mois = validated_data['duree_mois']
        
        # Calculer la date de fin
        validated_data['date_fin'] = LocationService._calculer_date_fin(date_debut, duree_mois)
        
        # Créer la location
        location = Location.objects.create(**validated_data)
        
        # Mettre à jour le statut de la maison
        maison = validated_data['maison']
        maison.statut = 'LOUEE'
        maison.save(update_fields=['statut'])
        
        return location


class LocationRenouvellementSerializer(serializers.Serializer):
    """Serializer pour le renouvellement d'une location"""
    duree_supplementaire_mois = serializers.IntegerField(min_value=1, max_value=36)


class LocationResiliationSerializer(serializers.Serializer):
    """Serializer pour la résiliation d'une location"""
    raison = serializers.CharField(required=False, allow_blank=True, max_length=500)


class LocationDetailSerializer(LocationSerializer):
    """Serializer détaillé avec relations"""
    locataire = UserSerializer(read_only=True)
    maison = MaisonListSerializer(read_only=True)

