from rest_framework import serializers


class ReservationRecenteSerializer(serializers.Serializer):
    """Serializer pour une réservation récente dans le dashboard"""
    id = serializers.UUIDField()
    reference = serializers.CharField()
    statut = serializers.CharField()
    date_debut_souhaitee = serializers.DateField()
    duree_mois = serializers.IntegerField()
    message = serializers.CharField()
    created_at = serializers.DateTimeField()
    user__prenoms = serializers.CharField()
    user__nom = serializers.CharField()
    user__telephone = serializers.CharField()
    user__email = serializers.EmailField()
    maison__titre = serializers.CharField()
    maison__reference = serializers.CharField()


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
    reservations_en_attente = serializers.IntegerField()
    reservations_recentes = ReservationRecenteSerializer(many=True)
