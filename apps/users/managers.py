"""
Manager personnalisé pour le modèle User
"""
from django.contrib.auth.models import BaseUserManager
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """
    Manager personnalisé pour le modèle User
    """
    
    def create_user(self, email, nom, prenoms, telephone, password=None, **extra_fields):
        """
        Crée et sauvegarde un utilisateur normal
        """
        if not email:
            raise ValueError(_('L\'adresse email est obligatoire'))
        if not telephone:
            raise ValueError(_('Le numéro de téléphone est obligatoire'))
        
        email = self.normalize_email(email)
        user = self.model(
            email=email,
            nom=nom,
            prenoms=prenoms,
            telephone=telephone,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, nom, prenoms, telephone, password=None, **extra_fields):
        """
        Crée et sauvegarde un superutilisateur
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', 'ADMIN')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Le superuser doit avoir is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Le superuser doit avoir is_superuser=True.'))
        
        return self.create_user(email, nom, prenoms, telephone, password, **extra_fields)
    
    def get_admins(self):
        """Retourne tous les administrateurs"""
        return self.filter(role='ADMIN', is_active=True)
    
    def get_locataires(self):
        """Retourne tous les locataires"""
        return self.filter(role='LOCATAIRE', is_active=True)
    
    def get_locataires_en_retard(self):
        """Retourne les locataires en retard de paiement"""
        return self.filter(role='LOCATAIRE', statut='EN_RETARD', is_active=True)
