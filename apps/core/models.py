"""
Modèles de base réutilisables
"""
from django.db import models
import uuid


class BaseModel(models.Model):
    """
    Modèle de base abstrait avec champs communs
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="Identifiant unique"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Date de modification"
    )
    
    class Meta:
        abstract = True
        ordering = ['-created_at']
    
    def __str__(self):
        return str(self.id)
