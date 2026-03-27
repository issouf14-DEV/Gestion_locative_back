"""
Modèles pour les paiements et validation manuelle
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from apps.core.models import BaseModel
from apps.users.models import User


class Paiement(BaseModel):
    """
    Modèle pour un paiement soumis par un locataire
    """
    
    STATUT_CHOICES = [
        ('EN_ATTENTE', 'En attente de validation'),
        ('VALIDE', 'Validé'),
        ('REJETE', 'Rejeté'),
    ]
    
    # Relations
    locataire = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='paiements',
        verbose_name=_('Locataire')
    )
    
    # Référence
    reference = models.CharField(
        _('Référence'),
        max_length=30,
        unique=True,
        editable=False
    )
    
    # Montant
    montant = models.DecimalField(
        _('Montant payé (FCFA)'),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    
    # Factures concernées (JSON: liste d'IDs de factures)
    factures_ids = models.JSONField(
        _('Factures concernées'),
        default=list,
        help_text="Liste des IDs de factures payées"
    )
    
    # Preuve de paiement
    preuve = models.ImageField(
        _('Preuve de paiement'),
        upload_to='payments/preuves/'
    )
    
    # Notes locataire
    notes_locataire = models.TextField(
        _('Notes du locataire'),
        blank=True
    )
    
    # Statut et validation
    statut = models.CharField(
        _('Statut'),
        max_length=20,
        choices=STATUT_CHOICES,
        default='EN_ATTENTE'
    )
    
    # Validation admin
    validateur = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='paiements_valides',
        verbose_name=_('Validateur')
    )
    date_validation = models.DateTimeField(
        _('Date de validation'),
        null=True,
        blank=True
    )
    commentaire_admin = models.TextField(
        _('Commentaire administrateur'),
        blank=True
    )
    
    class Meta:
        verbose_name = _('Paiement')
        verbose_name_plural = _('Paiements')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.reference} - {self.locataire.get_full_name()} - {self.montant} FCFA"
    
    def save(self, *args, **kwargs):
        if not self.reference:
            from apps.core.utils import generate_reference
            self.reference = generate_reference('PAY')
        super().save(*args, **kwargs)
