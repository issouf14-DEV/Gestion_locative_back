"""
Modèles pour la gestion des utilisateurs
"""
from __future__ import annotations
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import BaseModel
from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin, BaseModel):
    """
    Modèle utilisateur personnalisé
    """
    
    ROLE_CHOICES = [
        ('ADMIN', 'Administrateur'),
        ('LOCATAIRE', 'Locataire'),
    ]
    
    STATUT_CHOICES = [
        ('A_JOUR', 'À jour'),
        ('EN_RETARD', 'En retard'),
        ('SUSPENDU', 'Suspendu'),
    ]
    
    # Informations de base
    email = models.EmailField(
        _('Adresse email'),
        unique=True,
        error_messages={
            'unique': _("Un utilisateur avec cet email existe déjà."),
        }
    )
    telephone = models.CharField(
        _('Téléphone'),
        max_length=20,
        unique=True,
        error_messages={
            'unique': _("Ce numéro de téléphone est déjà utilisé."),
        }
    )
    nom = models.CharField(_('Nom'), max_length=100)
    prenoms = models.CharField(_('Prénoms'), max_length=100)
    
    # Rôle et statut
    role = models.CharField(
        _('Rôle'),
        max_length=20,
        choices=ROLE_CHOICES,
        default='LOCATAIRE'
    )
    statut = models.CharField(
        _('Statut'),
        max_length=20,
        choices=STATUT_CHOICES,
        default='A_JOUR'
    )
    
    # Informations supplémentaires
    photo = models.ImageField(
        _('Photo de profil'),
        upload_to='users/photos/',
        null=True,
        blank=True
    )
    adresse = models.TextField(_('Adresse'), blank=True, null=True)
    
    # Statuts Django
    is_staff = models.BooleanField(_('Membre du staff'), default=False)
    is_active = models.BooleanField(_('Actif'), default=True)
    email_verified = models.BooleanField(_('Email vérifié'), default=False)
    
    # Dates
    date_joined = models.DateTimeField(_('Date d\'inscription'), auto_now_add=True)
    last_login = models.DateTimeField(_('Dernière connexion'), null=True, blank=True)
    
    objects: 'UserManager' = UserManager()  # type: ignore[assignment]
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nom', 'prenoms', 'telephone']
    
    class Meta:
        verbose_name = _('Utilisateur')
        verbose_name_plural = _('Utilisateurs')
        ordering = ['-date_joined']
    
    def __str__(self):
        return f"{self.prenoms} {self.nom}"
    
    def get_full_name(self):
        """Retourne le nom complet"""
        return f"{self.prenoms} {self.nom}"
    
    def get_short_name(self):
        """Retourne le prénom"""
        return self.prenoms
    
    @property
    def is_admin(self):
        """Vérifie si l'utilisateur est admin"""
        return self.role == 'ADMIN'
    
    @property
    def is_locataire(self):
        """Vérifie si l'utilisateur est locataire"""
        return self.role == 'LOCATAIRE'
    
    @property
    def dette_totale(self):
        """Calcule la dette totale du locataire"""
        if self.role != 'LOCATAIRE':
            return 0
        
        from apps.billing.models import Facture
        factures_impayees = Facture.objects.filter(
            locataire=self,
            statut='EN_ATTENTE'
        )
        return sum(facture.montant for facture in factures_impayees)


class Profile(BaseModel):
    """
    Profil étendu de l'utilisateur (informations complémentaires)
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name=_('Utilisateur')
    )
    
    # Informations professionnelles
    profession = models.CharField(_('Profession'), max_length=100, blank=True)
    employeur = models.CharField(_('Employeur'), max_length=200, blank=True)
    
    # Contact d'urgence
    contact_urgence_nom = models.CharField(
        _('Nom du contact d\'urgence'),
        max_length=200,
        blank=True
    )
    contact_urgence_telephone = models.CharField(
        _('Téléphone du contact d\'urgence'),
        max_length=20,
        blank=True
    )
    contact_urgence_relation = models.CharField(
        _('Relation'),
        max_length=100,
        blank=True
    )
    
    # Préférences
    notifications_email = models.BooleanField(
        _('Notifications par email'),
        default=True
    )
    notifications_sms = models.BooleanField(
        _('Notifications par SMS'),
        default=False
    )
    
    # Documents
    piece_identite = models.FileField(
        _('Pièce d\'identité'),
        upload_to='users/documents/',
        null=True,
        blank=True
    )
    
    class Meta:
        verbose_name = _('Profil')
        verbose_name_plural = _('Profils')
    
    def __str__(self):
        return f"Profil de {self.user.get_full_name()}"
