"""
Modèles pour les dépenses
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from apps.core.models import BaseModel
from apps.properties.models import Maison


class Depense(BaseModel):
    """
    Modèle pour une dépense
    """
    
    CATEGORIE_CHOICES = [
        ('MAINTENANCE', 'Maintenance'),
        ('REPARATION', 'Réparation'),
        ('AMENAGEMENT', 'Aménagement'),
        ('TAXE', 'Taxe'),
        ('ASSURANCE', 'Assurance'),
        ('AUTRE', 'Autre'),
    ]
    
    maison = models.ForeignKey(
        Maison,
        on_delete=models.CASCADE,
        related_name='depenses',
        verbose_name=_('Maison'),
        null=True,
        blank=True
    )
    
    categorie = models.CharField(
        _('Catégorie'),
        max_length=20,
        choices=CATEGORIE_CHOICES
    )
    
    description = models.TextField(_('Description'))
    
    montant = models.DecimalField(
        _('Montant (FCFA)'),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    
    date_depense = models.DateField(_('Date de la dépense'))
    
    justificatif = models.FileField(
        _('Justificatif'),
        upload_to='expenses/justificatifs/',
        null=True,
        blank=True
    )
    
    class Meta:
        verbose_name = _('Dépense')
        verbose_name_plural = _('Dépenses')
        ordering = ['-date_depense']
    
    def __str__(self):
        return f"{self.get_categorie_display()} - {self.montant} FCFA"
