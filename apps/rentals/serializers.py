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
    # Si True, l'ancienne location active du locataire est résiliée automatiquement
    force_reassignation = serializers.BooleanField(
        required=False, default=False, write_only=True
    )

    class Meta:
        model = Location
        fields = [
            'locataire', 'maison', 'date_debut', 'duree_mois',
            'loyer_mensuel', 'caution_versee', 'notes', 'force_reassignation'
        ]

    def validate_maison(self, value):
        """Vérifie que la maison est disponible"""
        if value.statut != 'DISPONIBLE':
            raise serializers.ValidationError(
                f"Cette maison n'est pas disponible (statut: {value.get_statut_display()})"
            )
        return value

    def validate(self, attrs):
        """Vérifie que le locataire n'a pas déjà une location active (sauf si force_reassignation)"""
        locataire = attrs.get('locataire')
        force = attrs.get('force_reassignation', False)

        if locataire:
            location_active = Location.objects.filter(
                locataire=locataire,
                statut='ACTIVE'
            ).select_related('maison').first()

            if location_active and not force:
                raise serializers.ValidationError({
                    'locataire': (
                        f"Ce locataire a déjà une location active : "
                        f"contrat {location_active.numero_contrat} "
                        f"(maison : {location_active.maison.titre}). "
                        f"Passez force_reassignation=true pour résilier automatiquement."
                    )
                })

            # Stocker pour utilisation dans create()
            attrs['_location_existante'] = location_active if force else None

        return attrs

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
        from django.db import transaction

        validated_data.pop('force_reassignation', None)
        location_existante = validated_data.pop('_location_existante', None)

        date_debut = validated_data['date_debut']
        duree_mois = validated_data['duree_mois']
        validated_data['date_fin'] = LocationService._calculer_date_fin(date_debut, duree_mois)

        with transaction.atomic():
            # Résilier l'ancienne location si force_reassignation
            if location_existante:
                location_existante.statut = 'RESILIEE'
                location_existante.save(update_fields=['statut'])
                # Libérer l'ancienne maison
                ancienne_maison = location_existante.maison
                ancienne_maison.statut = 'DISPONIBLE'
                ancienne_maison.save(update_fields=['statut'])

            # Créer la nouvelle location
            location = Location.objects.create(**validated_data)

            # Marquer la nouvelle maison comme louée
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

