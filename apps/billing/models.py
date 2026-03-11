"""
Modèles pour la facturation (SODECI/CIE + Loyer)
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from apps.core.models import BaseModel
from apps.users.models import User
from decimal import Decimal


class Facture(BaseModel):
    """
    Modèle pour une facture (loyer, SODECI, CIE)
    """
    
    TYPE_CHOICES = [
        ('LOYER', 'Loyer'),
        ('SODECI', 'SODECI (Eau)'),
        ('CIE', 'CIE (Électricité)'),
        ('AUTRE', 'Autre'),
    ]
    
    STATUT_CHOICES = [
        ('EN_ATTENTE', 'En attente'),
        ('PAYEE', 'Payée'),
        ('ANNULEE', 'Annulée'),
        ('EN_RETARD', 'En retard'),
    ]
    
    # Relation
    locataire = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='factures',
        verbose_name=_('Locataire')
    )
    
    # Type et référence
    type_facture = models.CharField(
        _('Type'),
        max_length=20,
        choices=TYPE_CHOICES
    )
    reference = models.CharField(
        _('Référence'),
        max_length=30,
        unique=True,
        editable=False
    )
    
    # Montant
    montant = models.DecimalField(
        _('Montant (FCFA)'),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    
    # Pour SODECI/CIE
    index_ancien = models.DecimalField(
        _('Index ancien'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    index_nouveau = models.DecimalField(
        _('Index nouveau'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    consommation = models.DecimalField(
        _('Consommation (unités)'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    pourcentage = models.DecimalField(
        _('Pourcentage (%)'),
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Part de consommation du locataire"
    )
    
    # Période
    mois = models.PositiveIntegerField(_('Mois'), validators=[MinValueValidator(1)])
    annee = models.PositiveIntegerField(_('Année'))
    date_emission = models.DateField(_('Date d\'émission'), auto_now_add=True)
    date_echeance = models.DateField(_('Date d\'échéance'))
    
    # Statut
    statut = models.CharField(
        _('Statut'),
        max_length=20,
        choices=STATUT_CHOICES,
        default='EN_ATTENTE'
    )
    
    # Notes
    notes = models.TextField(_('Notes'), blank=True)
    
    class Meta:
        verbose_name = _('Facture')
        verbose_name_plural = _('Factures')
        ordering = ['-annee', '-mois', '-date_emission']
        unique_together = [['locataire', 'type_facture', 'mois', 'annee']]
        indexes = [
            models.Index(fields=['locataire', 'statut']),
            models.Index(fields=['mois', 'annee']),
        ]
    
    def __str__(self):
        return f"{self.reference} - {self.locataire.get_full_name()} - {self.get_type_facture_display()}"
    
    def save(self, *args, **kwargs):
        """Génère une référence unique"""
        if not self.reference:
            from apps.core.utils import generate_reference
            prefix = self.type_facture[:3]
            self.reference = generate_reference(prefix)
        
        # Calculer la consommation si index fournis
        if self.index_ancien is not None and self.index_nouveau is not None:
            self.consommation = self.index_nouveau - self.index_ancien
        
        super().save(*args, **kwargs)
    
    @property
    def is_en_retard(self):
        """Vérifie si la facture est en retard"""
        from django.utils import timezone
        return self.statut == 'EN_ATTENTE' and self.date_echeance < timezone.now().date()


class FactureCollective(BaseModel):
    """
    Facture collective SODECI/CIE pour tous les locataires
    """
    
    TYPE_CHOICES = [
        ('SODECI', 'SODECI (Eau)'),
        ('CIE', 'CIE (Électricité)'),
    ]
    
    type_facture = models.CharField(
        _('Type'),
        max_length=20,
        choices=TYPE_CHOICES
    )
    montant_total = models.DecimalField(
        _('Montant total (FCFA)'),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    mois = models.PositiveIntegerField(_('Mois'))
    annee = models.PositiveIntegerField(_('Année'))
    
    # Consommation totale
    consommation_totale = models.DecimalField(
        _('Consommation totale'),
        max_digits=12,
        decimal_places=2,
        default=0
    )
    
    # Métadonnées
    repartie = models.BooleanField(_('Répartie'), default=False)
    date_repartition = models.DateTimeField(_('Date de répartition'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('Facture collective')
        verbose_name_plural = _('Factures collectives')
        ordering = ['-annee', '-mois']
        unique_together = [['type_facture', 'mois', 'annee']]
    
    def __str__(self):
        return f"{self.get_type_facture_display()} - {self.mois}/{self.annee}"


class IndexCompteur(BaseModel):
    """
    Relevé d'index pour un locataire (pour SODECI/CIE)
    """
    
    TYPE_CHOICES = [
        ('SODECI', 'SODECI (Eau)'),
        ('CIE', 'CIE (Électricité)'),
    ]
    
    locataire = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='index_compteurs',
        verbose_name=_('Locataire')
    )
    type_compteur = models.CharField(
        _('Type'),
        max_length=20,
        choices=TYPE_CHOICES
    )
    
    index_valeur = models.DecimalField(
        _('Valeur de l\'index'),
        max_digits=10,
        decimal_places=2
    )
    
    mois = models.PositiveIntegerField(_('Mois'))
    annee = models.PositiveIntegerField(_('Année'))
    date_releve = models.DateField(_('Date du relevé'), auto_now_add=True)
    
    # Photo du compteur (optionnel)
    photo_compteur = models.ImageField(
        _('Photo du compteur'),
        upload_to='billing/compteurs/',
        null=True,
        blank=True
    )
    
    class Meta:
        verbose_name = _('Index compteur')
        verbose_name_plural = _('Index compteurs')
        ordering = ['-annee', '-mois']
        unique_together = [['locataire', 'type_compteur', 'mois', 'annee']]
    
    def __str__(self):
        return f"{self.locataire.get_full_name()} - {self.get_type_compteur_display()} - {self.mois}/{self.annee}"
