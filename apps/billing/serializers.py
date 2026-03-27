"""
Serializers pour le module billing
"""
from rest_framework import serializers
from .models import Facture, FactureCollective, IndexCompteur, Compteur
from apps.users.serializers import UserSerializer


class CompteurSerializer(serializers.ModelSerializer):
    """Serializer pour les compteurs"""
    maison_adresse = serializers.CharField(source='maison.adresse', read_only=True)
    locataire_nom = serializers.CharField(source='locataire_actuel.get_full_name', read_only=True)
    type_compteur_display = serializers.CharField(source='get_type_compteur_display', read_only=True)
    
    class Meta:
        model = Compteur
        fields = '__all__'
        read_only_fields = ['date_installation', 'dernier_index']


class CompteurAssignationSerializer(serializers.Serializer):
    """Serializer pour assigner un compteur à un locataire"""
    compteur_id = serializers.IntegerField()
    locataire_id = serializers.IntegerField()
    index_initial = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)


class FactureNotificationSerializer(serializers.Serializer):
    """Serializer pour l'envoi de notifications"""
    facture_id = serializers.IntegerField()
    canaux = serializers.ListField(
        child=serializers.ChoiceField(choices=['email', 'app', 'whatsapp']),
        required=False,
        default=['email', 'app']
    )


class FactureSerializer(serializers.ModelSerializer):
    """Serializer pour les factures"""
    locataire_nom = serializers.CharField(source='locataire.get_full_name', read_only=True)
    type_facture_display = serializers.CharField(source='get_type_facture_display', read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    
    class Meta:
        model = Facture
        fields = '__all__'
        read_only_fields = ['reference', 'consommation', 'date_emission']


class IndexCompteurSerializer(serializers.ModelSerializer):
    """Serializer pour les index de compteur"""
    locataire_nom = serializers.CharField(source='locataire.get_full_name', read_only=True)
    
    class Meta:
        model = IndexCompteur
        fields = '__all__'
        read_only_fields = ['date_releve']


class FactureCollectiveSerializer(serializers.ModelSerializer):
    """Serializer pour les factures collectives"""
    
    class Meta:
        model = FactureCollective
        fields = '__all__'
        read_only_fields = ['consommation_totale', 'repartie', 'date_repartition']


class IndexReleveSerializer(serializers.Serializer):
    """Serializer pour un relevé d'index dans le payload de répartition"""
    locataire_id = serializers.UUIDField()
    index_valeur = serializers.DecimalField(max_digits=10, decimal_places=2)
    compteur_id = serializers.UUIDField(required=False)


class RepartitionFactureSerializer(serializers.Serializer):
    """Serializer pour la répartition des factures"""
    type_facture = serializers.ChoiceField(choices=['SODECI', 'CIE'])
    montant_total = serializers.DecimalField(max_digits=12, decimal_places=2)
    mois = serializers.IntegerField(min_value=1, max_value=12)
    annee = serializers.IntegerField(min_value=2020)
    date_echeance = serializers.DateField()
    index = IndexReleveSerializer(many=True, required=False)
