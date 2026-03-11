"""
Modèles pour les notifications
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import BaseModel
from apps.users.models import User


class Notification(BaseModel):
    """
    Modèle pour une notification
    """
    
    TYPE_CHOICES = [
        ('INFO', 'Information'),
        ('SUCCESS', 'Succès'),
        ('WARNING', 'Avertissement'),
        ('ERROR', 'Erreur'),
        ('FACTURE', 'Facture'),
        ('PAIEMENT', 'Paiement'),
        ('LOCATION', 'Location'),
        ('RAPPEL', 'Rappel'),
    ]
    
    destinataire = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name=_('Destinataire')
    )
    
    type_notification = models.CharField(
        _('Type'),
        max_length=20,
        choices=TYPE_CHOICES,
        default='INFO'
    )
    
    titre = models.CharField(_('Titre'), max_length=200)
    message = models.TextField(_('Message'))
    
    lu = models.BooleanField(_('Lu'), default=False)
    date_lecture = models.DateTimeField(_('Date de lecture'), null=True, blank=True)
    
    # Lien associé (optionnel)
    lien = models.CharField(_('Lien'), max_length=500, blank=True)
    
    # Données supplémentaires (JSON)
    metadata = models.JSONField(_('Métadonnées'), default=dict, blank=True)
    
    class Meta:
        verbose_name = _('Notification')
        verbose_name_plural = _('Notifications')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['destinataire', 'lu']),
        ]
    
    def __str__(self):
        return f"{self.titre} - {self.destinataire.get_full_name()}"
    
    def marquer_comme_lu(self):
        """Marque la notification comme lue"""
        from django.utils import timezone
        self.lu = True
        self.date_lecture = timezone.now()
        self.save(update_fields=['lu', 'date_lecture'])
