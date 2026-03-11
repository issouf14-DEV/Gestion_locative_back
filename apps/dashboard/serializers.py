from rest_framework import serializers


class DashboardStatsSerializer(serializers.Serializer):
    """Serializer pour les statistiques du dashboard"""
    total_maisons = serializers.IntegerField()
    maisons_disponibles = serializers.IntegerField()
    maisons_louees = serializers.IntegerField()
    total_locataires = serializers.IntegerField()
    locataires_a_jour = serializers.IntegerField()
    locataires_en_retard = serializers.IntegerField()
    revenus_mois_courant = serializers.DecimalField(max_digits=15, decimal_places=2)
    depenses_mois_courant = serializers.DecimalField(max_digits=15, decimal_places=2)
    factures_impayees = serializers.IntegerField()
    montant_factures_impayees = serializers.DecimalField(max_digits=15, decimal_places=2)
