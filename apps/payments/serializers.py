"""
Serializers pour le module payments
"""
from rest_framework import serializers
from .models import Paiement
from apps.billing.models import Facture


class PaiementSerializer(serializers.ModelSerializer):
    """Serializer complet pour les paiements"""
    locataire_nom = serializers.CharField(source='locataire.get_full_name', read_only=True)
    locataire_email = serializers.CharField(source='locataire.email', read_only=True)
    validateur_nom = serializers.CharField(source='validateur.get_full_name', read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    factures_details = serializers.SerializerMethodField()
    
    class Meta:
        model = Paiement
        fields = [
            'id', 'reference', 'locataire', 'locataire_nom', 'locataire_email',
            'montant', 'factures_ids', 'factures_details', 'preuve',
            'notes_locataire', 'statut', 'statut_display',
            'validateur', 'validateur_nom', 'date_validation', 'commentaire_admin',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'reference', 'locataire', 'validateur', 'date_validation',
            'created_at', 'updated_at'
        ]
    
    def get_factures_details(self, obj):
        """Retourne les détails des factures concernées"""
        factures = Facture.objects.filter(id__in=obj.factures_ids)
        return [
            {
                'id': str(f.id),
                'reference': f.reference,
                'type': f.get_type_facture_display(),
                'montant': float(f.montant),
                'mois': f.mois,
                'annee': f.annee,
                'statut': f.statut
            }
            for f in factures
        ]


class PaiementCreateSerializer(serializers.ModelSerializer):
    """Serializer pour la création d'un paiement"""
    factures_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        help_text="Liste des IDs (UUID) des factures concernées"
    )
    
    class Meta:
        model = Paiement
        fields = ['montant', 'factures_ids', 'preuve', 'notes_locataire']
    
    def validate_montant(self, value):
        """Valide que le montant est positif"""
        if value <= 0:
            raise serializers.ValidationError("Le montant doit être supérieur à 0")
        return value
    
    def validate_factures_ids(self, value):
        """Valide que les factures existent et sont impayées"""
        user = self.context['request'].user
        
        factures = Facture.objects.filter(
            id__in=value,
            locataire=user
        )
        
        if factures.count() != len(value):
            raise serializers.ValidationError(
                "Certaines factures n'existent pas ou ne vous appartiennent pas"
            )
        
        # Vérifier que les factures ne sont pas déjà payées
        factures_payees = factures.filter(statut='PAYEE')
        if factures_payees.exists():
            refs = ", ".join([f.reference for f in factures_payees])
            raise serializers.ValidationError(
                f"Ces factures sont déjà payées: {refs}"
            )
        
        return value
    
    def validate_preuve(self, value):
        """Valide le fichier de preuve"""
        if value:
            # Taille max: 5 MB
            if value.size > 5 * 1024 * 1024:
                raise serializers.ValidationError(
                    "La taille du fichier ne doit pas dépasser 5 MB"
                )
            
            # Types acceptés
            allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'application/pdf']
            if value.content_type not in allowed_types:
                raise serializers.ValidationError(
                    "Type de fichier non accepté. Formats: JPEG, PNG, GIF, PDF"
                )
        
        return value
    
    def create(self, validated_data):
        """Crée un paiement avec les UUIDs convertis en strings"""
        # Convertir les UUIDs en strings pour le JSONField
        factures_ids = validated_data.pop('factures_ids', [])
        validated_data['factures_ids'] = [str(f_id) for f_id in factures_ids]
        validated_data['locataire'] = self.context['request'].user
        return super().create(validated_data)


class PaiementValidationSerializer(serializers.Serializer):
    """Serializer pour la validation/rejet d'un paiement"""
    commentaire = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=500
    )


class PaiementListeSerializer(serializers.ModelSerializer):
    """Serializer simplifié pour la liste des paiements"""
    locataire_nom = serializers.CharField(source='locataire.get_full_name', read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    
    class Meta:
        model = Paiement
        fields = [
            'id', 'reference', 'locataire_nom', 'montant',
            'statut', 'statut_display', 'created_at'
        ]

