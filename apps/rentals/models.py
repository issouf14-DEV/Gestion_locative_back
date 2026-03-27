"""
Modèles pour les locations (contrats)
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from apps.core.models import BaseModel
from apps.users.models import User
from apps.properties.models import Maison


class Location(BaseModel):
    """
    Modèle pour un contrat de location
    """
    
    STATUT_CHOICES = [
        ('ACTIVE', 'Active'),
        ('TERMINEE', 'Terminée'),
        ('RESILIEE', 'Résiliée'),
        ('SUSPENDUE', 'Suspendue'),
    ]
    
    # Relations
    locataire = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='locations',
        verbose_name=_('Locataire')
    )
    maison = models.ForeignKey(
        Maison,
        on_delete=models.CASCADE,
        related_name='locations',
        verbose_name=_('Maison')
    )
    
    # Références
    numero_contrat = models.CharField(
        _('Numéro de contrat'),
        max_length=30,
        unique=True,
        editable=False
    )
    
    # Dates
    date_debut = models.DateField(_('Date de début'))
    date_fin = models.DateField(_('Date de fin'))
    duree_mois = models.PositiveIntegerField(_('Durée (mois)'))
    
    # Montants
    loyer_mensuel = models.DecimalField(
        _('Loyer mensuel (FCFA)'),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    caution_versee = models.DecimalField(
        _('Caution versée (FCFA)'),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    
    # Statut
    statut = models.CharField(
        _('Statut'),
        max_length=20,
        choices=STATUT_CHOICES,
        default='ACTIVE'
    )
    
    # Documents
    contrat_pdf = models.FileField(
        _('Contrat PDF'),
        upload_to='rentals/contrats/',
        null=True,
        blank=True
    )
    
    # Notes
    notes = models.TextField(_('Notes'), blank=True)
    
    class Meta:
        verbose_name = _('Location')
        verbose_name_plural = _('Locations')
        ordering = ['-date_debut']
    
    def __str__(self):
        return f"{self.numero_contrat} - {self.locataire.get_full_name()} - {self.maison.titre}"
    
    def save(self, *args, **kwargs):
        if not self.numero_contrat:
            from apps.core.utils import generate_reference
            self.numero_contrat = generate_reference('LOC')
        super().save(*args, **kwargs)
