"""
Serializers pour l'authentification
"""
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from apps.users.models import User
from apps.users.serializers import UserSerializer


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Serializer personnalisé pour l'obtention de tokens JWT
    """
    
    def validate(self, attrs):
        """Valide et retourne les tokens avec les données utilisateur"""
        data = super().validate(attrs)
        
        # Ajouter les informations utilisateur au response
        data['user'] = UserSerializer(self.user).data
        
        return data
    
    @classmethod
    def get_token(cls, user):
        """Ajoute des claims personnalisés au token"""
        token = super().get_token(user)
        
        # Ajouter des claims personnalisés
        token['email'] = user.email
        token['role'] = user.role
        token['nom'] = user.nom
        token['prenoms'] = user.prenoms
        
        return token


class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer pour l'inscription d'un nouvel utilisateur
    """
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
            'password', 'password_confirm', 'adresse'
        ]
    
    def validate(self, attrs):
        """Valide que les mots de passe correspondent"""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                "password": "Les mots de passe ne correspondent pas."
            })
        return attrs
    
    def validate_email(self, value):
        """Valide que l'email n'existe pas déjà"""
        if User.objects.filter(email=value.lower()).exists():
            raise serializers.ValidationError("Un utilisateur avec cet email existe déjà.")
        return value.lower()
    
    def validate_telephone(self, value):
        """Valide que le téléphone n'existe pas déjà"""
        if User.objects.filter(telephone=value).exists():
            raise serializers.ValidationError("Ce numéro de téléphone est déjà utilisé.")
        return value
    
    def create(self, validated_data):
        """Crée un nouvel utilisateur"""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        # Créer l'utilisateur avec le rôle LOCATAIRE par défaut
        user = User.objects.create_user(
            password=password,
            role='LOCATAIRE',
            **validated_data
        )
        
        return user


class LoginSerializer(serializers.Serializer):
    """
    Serializer pour la connexion
    """
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    
    def validate(self, attrs):
        """Valide les identifiants"""
        email = attrs.get('email', '').lower()
        password = attrs.get('password')
        
        if email and password:
            user = authenticate(
                request=self.context.get('request'),
                email=email,
                password=password
            )
            
            if not user:
                raise serializers.ValidationError(
                    "Email ou mot de passe incorrect."
                )
            
            if not user.is_active:
                raise serializers.ValidationError(
                    "Ce compte est désactivé."
                )
            
            attrs['user'] = user
            return attrs
        
        raise serializers.ValidationError(
            "Email et mot de passe sont obligatoires."
        )


class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Serializer pour demander la réinitialisation du mot de passe
    """
    email = serializers.EmailField(required=True)
    
    def validate_email(self, value):
        """Valide que l'email existe"""
        try:
            user = User.objects.get(email=value.lower())
            self.context['user'] = user
        except User.DoesNotExist:
            # Pour des raisons de sécurité, on ne révèle pas si l'email existe
            pass
        return value.lower()


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializer pour confirmer la réinitialisation du mot de passe
    """
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    
    def validate(self, attrs):
        """Valide que les nouveaux mots de passe correspondent"""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                "new_password": "Les mots de passe ne correspondent pas."
            })
        return attrs


class PasswordChangeSerializer(serializers.Serializer):
    """
    Serializer pour changer le mot de passe (utilisateur connecté)
    """
    old_password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    
    def validate(self, attrs):
        """Valide que les nouveaux mots de passe correspondent"""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                "new_password": "Les mots de passe ne correspondent pas."
            })
        return attrs
    
    def validate_old_password(self, value):
        """Valide que l'ancien mot de passe est correct"""
        user = self.context.get('user')
        if user and not user.check_password(value):
            raise serializers.ValidationError("Mot de passe actuel incorrect.")
        return value


class EmailVerificationSerializer(serializers.Serializer):
    """
    Serializer pour la vérification d'email
    """
    token = serializers.CharField(required=True)
