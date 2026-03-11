"""
Modèles pour la gestion des propriétés (maisons)
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from apps.core.models import BaseModel


class Maison(BaseModel):
    """
    Modèle pour une maison/propriété
    """
    
    STATUT_CHOICES = [
        ('DISPONIBLE', 'Disponible'),
        ('LOUEE', 'Louée'),
        ('EN_MAINTENANCE', 'En maintenance'),
        ('INDISPONIBLE', 'Indisponible'),
    ]
    
    TYPE_CHOICES = [
        ('STUDIO', 'Studio'),
        ('F1', 'F1'),
        ('F2', 'F2'),
        ('F3', 'F3'),
        ('F4', 'F4'),
        ('F5', 'F5'),
        ('VILLA', 'Villa'),
        ('DUPLEX', 'Duplex'),
        ('APPARTEMENT', 'Appartement'),
    ]
    
    # Informations de base
    titre = models.CharField(_('Titre'), max_length=200)
    description = models.TextField(_('Description'))
    type_logement = models.CharField(
        _('Type de logement'),
        max_length=20,
        choices=TYPE_CHOICES,
        default='F2'
    )
    
    # Prix
    prix = models.DecimalField(
        _('Prix mensuel (FCFA)'),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    caution = models.DecimalField(
        _('Caution (FCFA)'),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Généralement équivalent à 1 ou 2 mois de loyer"
    )
    charges_incluses = models.BooleanField(
        _('Charges incluses'),
        default=False,
        help_text="Si True, SODECI/CIE inclus dans le prix"
    )
    
    # Localisation
    adresse = models.TextField(_('Adresse complète'))
    ville = models.CharField(_('Ville'), max_length=100, default='Abidjan')
    commune = models.CharField(_('Commune'), max_length=100)
    quartier = models.CharField(_('Quartier'), max_length=100)
    latitude = models.DecimalField(
        _('Latitude'),
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )
    longitude = models.DecimalField(
        _('Longitude'),
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )
    
    # Caractéristiques
    nombre_chambres = models.PositiveIntegerField(_('Nombre de chambres'), default=1)
    nombre_salles_bain = models.PositiveIntegerField(_('Nombre de salles de bain'), default=1)
    nombre_toilettes = models.PositiveIntegerField(_('Nombre de toilettes'), default=1)
    superficie = models.DecimalField(
        _('Superficie (m²)'),
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        null=True,
        blank=True
    )
    
    # Équipements (stocké en JSON)
    equipements = models.JSONField(
        _('Équipements'),
        default=list,
        blank=True,
        help_text="Liste des équipements: ['climatisation', 'cuisine équipée', ...]"
    )
    
    # Commodités à proximité
    commodites = models.JSONField(
        _('Commodités'),
        default=list,
        blank=True,
        help_text="['école', 'supermarché', 'transport', ...]"
    )
    
    # Statut et disponibilité
    statut = models.CharField(
        _('Statut'),
        max_length=20,
        choices=STATUT_CHOICES,
        default='DISPONIBLE'
    )
    meublee = models.BooleanField(_('Meublée'), default=False)
    animaux_acceptes = models.BooleanField(_('Animaux acceptés'), default=False)
    
    # Référence
    reference = models.CharField(
        _('Référence'),
        max_length=20,
        unique=True,
        editable=False
    )
    
    # Vues et statistiques
    nombre_vues = models.PositiveIntegerField(_('Nombre de vues'), default=0)
    
    class Meta:
        verbose_name = _('Maison')
        verbose_name_plural = _('Maisons')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['statut', 'prix']),
            models.Index(fields=['ville', 'commune']),
        ]
    
    def __str__(self):
        return f"{self.titre} - {self.reference}"
    
    def save(self, *args, **kwargs):
        """Génère une référence unique à la création"""
        if not self.reference:
            from apps.core.utils import generate_reference
            self.reference = generate_reference('MAIS')
        super().save(*args, **kwargs)
    
    @property
    def is_disponible(self):
        """Vérifie si la maison est disponible"""
        return self.statut == 'DISPONIBLE'
    
    @property
    def image_principale(self):
        """Retourne l'image principale"""
        image = self.images.filter(est_principale=True).first()
        return image.image.url if image else None
    
    @property
    def toutes_images(self):
        """Retourne toutes les images"""
        return [img.image.url for img in self.images.all()]


class ImageMaison(BaseModel):
    """
    Images d'une maison
    """
    maison = models.ForeignKey(
        Maison,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name=_('Maison')
    )
    image = models.ImageField(
        _('Image'),
        upload_to='properties/images/'
    )
    legende = models.CharField(
        _('Légende'),
        max_length=200,
        blank=True
    )
    est_principale = models.BooleanField(
        _('Image principale'),
        default=False
    )
    ordre = models.PositiveIntegerField(
        _('Ordre d\'affichage'),
        default=0
    )
    
    class Meta:
        verbose_name = _('Image de maison')
        verbose_name_plural = _('Images de maisons')
        ordering = ['-est_principale', 'ordre']
    
    def __str__(self):
        return f"Image de {self.maison.titre}"
    
    def save(self, *args, **kwargs):
        """Si c'est l'image principale, désactiver les autres"""
        if self.est_principale:
            ImageMaison.objects.filter(
                maison=self.maison,
                est_principale=True
            ).exclude(id=self.id).update(est_principale=False)
        super().save(*args, **kwargs)
