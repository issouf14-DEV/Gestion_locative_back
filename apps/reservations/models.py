"""
Modèles pour les réservations
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import BaseModel
from apps.users.models import User
from apps.properties.models import Maison


class Reservation(BaseModel):
    """
    Modèle pour une réservation
    """
    
    STATUT_CHOICES = [
        ('EN_ATTENTE', 'En attente'),
        ('ACCEPTEE', 'Acceptée'),
        ('REFUSEE', 'Refusée'),
        ('ANNULEE', 'Annulée'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reservations',
        verbose_name=_('Utilisateur')
    )
    maison = models.ForeignKey(
        Maison,
        on_delete=models.CASCADE,
        related_name='reservations',
        verbose_name=_('Maison')
    )
    
    reference = models.CharField(
        _('Référence'),
        max_length=30,
        unique=True,
        editable=False
    )
    
    date_debut_souhaitee = models.DateField(_('Date de début souhaitée'))
    duree_mois = models.PositiveIntegerField(_('Durée (mois)'))
    message = models.TextField(_('Message'), blank=True)
    
    statut = models.CharField(
        _('Statut'),
        max_length=20,
        choices=STATUT_CHOICES,
        default='EN_ATTENTE'
    )
    
    reponse_admin = models.TextField(_('Réponse admin'), blank=True)
    date_reponse = models.DateTimeField(_('Date de réponse'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('Réservation')
        verbose_name_plural = _('Réservations')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.reference} - {self.user.get_full_name()} - {self.maison.titre}"
    
    def save(self, *args, **kwargs):
        if not self.reference:
            from apps.core.utils import generate_reference
            self.reference = generate_reference('RES')
        super().save(*args, **kwargs)
