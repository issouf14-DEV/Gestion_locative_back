"""
Serializers pour le module properties
"""
from rest_framework import serializers
from .models import Maison, ImageMaison


class ImageMaisonSerializer(serializers.ModelSerializer):
    """Serializer pour les images de maison"""

    class Meta:
        model = ImageMaison
        fields = ['id', 'image', 'legende', 'est_principale', 'ordre', 'created_at']
        read_only_fields = ['id', 'created_at']


class MaisonListSerializer(serializers.ModelSerializer):
    """Serializer pour la liste des maisons (vue simplifiée)"""
    image_principale = serializers.URLField(read_only=True)
    locataire_actuel = serializers.SerializerMethodField()

    class Meta:
        model = Maison
        fields = [
            'id', 'reference', 'titre', 'type_logement', 'prix',
            'ville', 'commune', 'quartier', 'statut',
            'nombre_chambres', 'nombre_salles_bain', 'superficie',
            'image_principale', 'meublee', 'created_at', 'locataire_actuel'
        ]
        read_only_fields = ['id', 'reference', 'created_at']

    def get_locataire_actuel(self, obj):
        location = obj.locations.filter(statut='ACTIVE').select_related('locataire').first()
        if location:
            locataire = location.locataire
            return {
                'id': locataire.id,
                'nom': locataire.get_full_name(),
                'email': locataire.email,
                'telephone': getattr(locataire, 'telephone', None),
            }
        return None


class MaisonDetailSerializer(serializers.ModelSerializer):
    """Serializer pour les détails d'une maison"""
    images = ImageMaisonSerializer(many=True, read_only=True)
    toutes_images = serializers.ListField(
        child=serializers.URLField(),
        read_only=True
    )
    
    class Meta:
        model = Maison
        fields = [
            'id', 'reference', 'titre', 'description', 'type_logement',
            'prix', 'caution', 'charges_incluses',
            'adresse', 'ville', 'commune', 'quartier', 'latitude', 'longitude',
            'nombre_chambres', 'nombre_salles_bain', 'nombre_toilettes', 'superficie',
            'equipements', 'commodites', 'statut', 'meublee', 'animaux_acceptes',
            'nombre_vues', 'images', 'toutes_images', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'reference', 'nombre_vues', 'created_at', 'updated_at']


class MaisonCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour créer/modifier une maison"""
    
    class Meta:
        model = Maison
        fields = [
            'titre', 'description', 'type_logement', 'prix', 'caution',
            'charges_incluses', 'adresse', 'ville', 'commune', 'quartier',
            'latitude', 'longitude', 'nombre_chambres', 'nombre_salles_bain',
            'nombre_toilettes', 'superficie', 'equipements', 'commodites',
            'statut', 'meublee', 'animaux_acceptes'
        ]
    
    def validate_prix(self, value):
        """Valide que le prix est positif"""
        if value <= 0:
            raise serializers.ValidationError("Le prix doit être supérieur à 0")
        return value
    
    def validate_caution(self, value):
        """Valide que la caution est positive"""
        if value < 0:
            raise serializers.ValidationError("La caution ne peut pas être négative")
        return value


class ImageMaisonCreateSerializer(serializers.ModelSerializer):
    """Serializer pour ajouter des images à une maison"""
    
    class Meta:
        model = ImageMaison
        fields = ['maison', 'image', 'legende', 'est_principale', 'ordre']
    
    def validate(self, attrs):
        """Valide les données"""
        maison = attrs.get('maison')
        
        # Vérifier que la maison existe
        if not Maison.objects.filter(id=maison.id).exists():
            raise serializers.ValidationError("Cette maison n'existe pas")
        
        return attrs
