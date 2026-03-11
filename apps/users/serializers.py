"""
Serializers pour le module users
"""
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, Profile


class ProfileSerializer(serializers.ModelSerializer):
    """Serializer pour le profil utilisateur"""
    
    class Meta:
        model = Profile
        fields = [
            'profession', 'employeur', 
            'contact_urgence_nom', 'contact_urgence_telephone', 
            'contact_urgence_relation', 'notifications_email', 
            'notifications_sms', 'piece_identite'
        ]


class UserSerializer(serializers.ModelSerializer):
    """Serializer pour l'utilisateur"""
    profile = ProfileSerializer(read_only=True)
    dette_totale = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        read_only=True
    )
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'telephone', 'nom', 'prenoms',
            'role', 'statut', 'photo', 'adresse',
            'is_active', 'email_verified', 'date_joined',
            'last_login', 'profile', 'dette_totale'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login', 'dette_totale']


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer pour la création d'un utilisateur"""
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = User
        fields = [
            'email', 'telephone', 'nom', 'prenoms',
            'password', 'password_confirm', 'role', 'adresse'
        ]
    
    def validate(self, attrs):
        """Valide que les mots de passe correspondent"""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                "password": "Les mots de passe ne correspondent pas."
            })
        return attrs
    
    def create(self, validated_data):
        """Crée un nouvel utilisateur"""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        user = User.objects.create_user(
            password=password,
            **validated_data
        )
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour la mise à jour d'un utilisateur"""
    
    class Meta:
        model = User
        fields = [
            'nom', 'prenoms', 'telephone', 'photo',
            'adresse', 'statut'
        ]
    
    def update(self, instance, validated_data):
        """Met à jour l'utilisateur"""
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer pour changer le mot de passe"""
    old_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    
    def validate(self, attrs):
        """Valide que les nouveaux mots de passe correspondent"""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                "new_password": "Les nouveaux mots de passe ne correspondent pas."
            })
        return attrs
    
    def validate_old_password(self, value):
        """Valide que l'ancien mot de passe est correct"""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("L'ancien mot de passe est incorrect.")
        return value


class UserDetailSerializer(serializers.ModelSerializer):
    """Serializer détaillé pour un utilisateur"""
    profile = ProfileSerializer()
    dette_totale = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        read_only=True
    )
    
    # Statistiques pour les locataires
    nombre_factures_impayees = serializers.SerializerMethodField()
    location_actuelle = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'telephone', 'nom', 'prenoms',
            'role', 'statut', 'photo', 'adresse',
            'is_active', 'email_verified', 'date_joined',
            'last_login', 'profile', 'dette_totale',
            'nombre_factures_impayees', 'location_actuelle'
        ]
    
    def get_nombre_factures_impayees(self, obj):
        """Retourne le nombre de factures impayées"""
        if obj.role != 'LOCATAIRE':
            return 0
        from apps.billing.models import Facture
        return Facture.objects.filter(locataire=obj, statut='EN_ATTENTE').count()
    
    def get_location_actuelle(self, obj):
        """Retourne la location actuelle du locataire"""
        if obj.role != 'LOCATAIRE':
            return None
        from apps.rentals.models import Location
        try:
            location = Location.objects.get(locataire=obj, statut='ACTIVE')
            return {
                'id': location.id,
                'maison_titre': location.maison.titre,
                'date_debut': location.date_debut,
                'date_fin': location.date_fin,
                'loyer_mensuel': location.loyer_mensuel
            }
        except Location.DoesNotExist:
            return None
