"""
Vues pour l'authentification
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings

from .serializers import (
    CustomTokenObtainPairSerializer,
    RegisterSerializer,
    LoginSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    PasswordChangeSerializer,
)
from .tokens import account_activation_token, password_reset_token
from apps.users.serializers import UserSerializer
from apps.core.throttling import LoginRateThrottle, PasswordResetRateThrottle, RegisterRateThrottle

User = get_user_model()


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Vue personnalisée pour l'obtention de tokens JWT
    """
    serializer_class = CustomTokenObtainPairSerializer


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([RegisterRateThrottle])
def register(request):
    """
    Inscription d'un nouvel utilisateur
    """
    serializer = RegisterSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.save()
        
        # Générer les tokens JWT
        refresh = RefreshToken.for_user(user)  # type: ignore[arg-type]
        
        # Envoyer email de vérification (optionnel)
        # send_verification_email(user, request)
        
        return Response({
            'success': True,
            'message': 'Inscription réussie',
            'data': {
                'user': UserSerializer(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            }
        }, status=status.HTTP_201_CREATED)
    
    return Response({
        'success': False,
        'message': 'Erreur d\'inscription',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([LoginRateThrottle])
def login(request):
    """
    Connexion d'un utilisateur
    """
    serializer = LoginSerializer(data=request.data, context={'request': request})
    
    if serializer.is_valid():
        user = serializer.validated_data['user']  # type: ignore[index]
        
        # Générer les tokens JWT
        refresh = RefreshToken.for_user(user)  # type: ignore[arg-type]
        
        # Mettre à jour last_login
        from django.utils import timezone
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])
        
        return Response({
            'success': True,
            'message': 'Connexion réussie',
            'data': {
                'user': UserSerializer(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            }
        }, status=status.HTTP_200_OK)
    
    return Response({
        'success': False,
        'message': 'Erreur de connexion',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """
    Déconnexion d'un utilisateur (blacklist du refresh token)
    """
    try:
        refresh_token = request.data.get('refresh_token')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        
        return Response({
            'success': True,
            'message': 'Déconnexion réussie'
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'success': False,
            'message': 'Erreur lors de la déconnexion',
            'errors': {'detail': str(e)}
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([PasswordResetRateThrottle])
def password_reset_request(request):
    """
    Demande de réinitialisation de mot de passe
    """
    serializer = PasswordResetRequestSerializer(data=request.data)
    
    if serializer.is_valid():
        email = serializer.validated_data['email']  # type: ignore[index]
        
        try:
            user = User.objects.get(email=email)
            
            # Générer le token
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = password_reset_token.make_token(user)
            
            # Construire le lien de réinitialisation
            # À adapter selon votre frontend
            reset_link = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}/"
            
            # Envoyer l'email
            subject = "Réinitialisation de votre mot de passe"
            message = f"""
            Bonjour {user.get_full_name()},
            
            Vous avez demandé la réinitialisation de votre mot de passe.
            Cliquez sur le lien ci-dessous pour réinitialiser votre mot de passe :
            
            {reset_link}
            
            Ce lien est valable pendant 24 heures.
            
            Si vous n'avez pas fait cette demande, ignorez ce message.
            
            Cordialement,
            L'équipe Gestion Locative
            """
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
        except User.DoesNotExist:
            # Pour des raisons de sécurité, on ne révèle pas si l'email existe
            pass
        
        return Response({
            'success': True,
            'message': 'Si cet email existe, un lien de réinitialisation a été envoyé.'
        }, status=status.HTTP_200_OK)
    
    return Response({
        'success': False,
        'message': 'Email invalide',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_confirm(request):
    """
    Confirmation de la réinitialisation du mot de passe
    """
    serializer = PasswordResetConfirmSerializer(data=request.data)
    
    if serializer.is_valid():
        try:
            uid = request.data.get('uid')
            token = serializer.validated_data['token']  # type: ignore[index]
            new_password = serializer.validated_data['new_password']  # type: ignore[index]
            
            # Décoder l'uid
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
            
            # Vérifier le token
            if password_reset_token.check_token(user, token):
                user.set_password(new_password)
                user.save()
                
                return Response({
                    'success': True,
                    'message': 'Mot de passe réinitialisé avec succès'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'message': 'Token invalide ou expiré'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        except (User.DoesNotExist, ValueError, TypeError):
            return Response({
                'success': False,
                'message': 'Lien invalide'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    return Response({
        'success': False,
        'message': 'Données invalides',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def password_change(request):
    """
    Changement de mot de passe pour utilisateur connecté
    """
    serializer = PasswordChangeSerializer(
        data=request.data,
        context={'user': request.user}
    )
    
    if serializer.is_valid():
        # Changer le mot de passe
        request.user.set_password(serializer.validated_data['new_password'])  # type: ignore[index]
        request.user.save()
        
        return Response({
            'success': True,
            'message': 'Mot de passe modifié avec succès'
        }, status=status.HTTP_200_OK)
    
    return Response({
        'success': False,
        'message': 'Erreur de validation',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([AllowAny])
def verify_email(request, uid, token):
    """
    Vérification de l'email utilisateur
    """
    try:
        user_id = force_str(urlsafe_base64_decode(uid))
        user = User.objects.get(pk=user_id)
        
        if account_activation_token.check_token(user, token):
            user.email_verified = True  # type: ignore[attr-defined]
            user.save()
            
            return Response({
                'success': True,
                'message': 'Email vérifié avec succès'
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'message': 'Token invalide ou expiré'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    except (User.DoesNotExist, ValueError, TypeError):
        return Response({
            'success': False,
            'message': 'Lien de vérification invalide'
        }, status=status.HTTP_400_BAD_REQUEST)


def send_verification_email(user, request):
    """
    Envoie un email de vérification à l'utilisateur
    """
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = account_activation_token.make_token(user)
    
    # Construire le lien de vérification
    verification_link = f"{settings.FRONTEND_URL}/verify-email/{uid}/{token}/"
    
    subject = "Vérifiez votre adresse email"
    message = f"""
    Bonjour {user.get_full_name()},
    
    Merci de vous être inscrit sur notre plateforme.
    Veuillez cliquer sur le lien ci-dessous pour vérifier votre adresse email :
    
    {verification_link}
    
    Cordialement,
    L'équipe Gestion Locative
    """
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )


# ==============================================================================
# AUTHENTIFICATION SOCIALE (Google, Facebook)
# ==============================================================================

@api_view(['POST'])
@permission_classes([AllowAny])
def google_login(request):
    """
    Connexion via Google OAuth2
    
    Le frontend envoie le token d'accès Google après l'authentification OAuth
    """
    import requests
    
    access_token = request.data.get('access_token')
    
    if not access_token:
        return Response({
            'success': False,
            'message': 'Token d\'accès Google requis'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Valider le token avec Google
        google_response = requests.get(
            'https://www.googleapis.com/oauth2/v3/userinfo',
            headers={'Authorization': f'Bearer {access_token}'}
        )
        
        if google_response.status_code != 200:
            return Response({
                'success': False,
                'message': 'Token Google invalide'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        google_data = google_response.json()
        email = google_data.get('email')
        
        if not email:
            return Response({
                'success': False,
                'message': 'Email non fourni par Google'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Chercher ou créer l'utilisateur
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'nom': google_data.get('family_name', ''),
                'prenoms': google_data.get('given_name', ''),
                'email_verified': google_data.get('email_verified', False),
                'role': 'LOCATAIRE',
            }
        )
        
        if created:
            # Définir un mot de passe inutilisable pour les comptes sociaux
            user.set_unusable_password()
            user.save()
        
        # Générer les tokens JWT
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'success': True,
            'message': 'Connexion Google réussie',
            'data': {
                'user': UserSerializer(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                },
                'is_new_user': created
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Erreur lors de la connexion Google: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
