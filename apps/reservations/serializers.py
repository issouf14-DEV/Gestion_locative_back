from rest_framework import serializers
from .models import Reservation


class ReservationSerializer(serializers.ModelSerializer):
    user_nom = serializers.CharField(source='user.get_full_name', read_only=True)
    maison_titre = serializers.CharField(source='maison.titre', read_only=True)
    
    class Meta:
        model = Reservation
        fields = '__all__'
        read_only_fields = ['reference', 'user', 'date_reponse']
