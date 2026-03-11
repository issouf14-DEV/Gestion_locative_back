"""
Serializers pour le module billing
"""
from rest_framework import serializers
from .models import Facture, FactureCollective, IndexCompteur
from apps.users.serializers import UserSerializer


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


class RepartitionFactureSerializer(serializers.Serializer):
    """Serializer pour la répartition des factures"""
    type_facture = serializers.ChoiceField(choices=['SODECI', 'CIE'])
    montant_total = serializers.DecimalField(max_digits=12, decimal_places=2)
    mois = serializers.IntegerField(min_value=1, max_value=12)
    annee = serializers.IntegerField(min_value=2020)
    date_echeance = serializers.DateField()
