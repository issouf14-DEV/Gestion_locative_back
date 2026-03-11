from rest_framework import serializers
from .models import Depense


class DepenseSerializer(serializers.ModelSerializer):
    maison_titre = serializers.CharField(source='maison.titre', read_only=True)
    
    class Meta:
        model = Depense
        fields = '__all__'
