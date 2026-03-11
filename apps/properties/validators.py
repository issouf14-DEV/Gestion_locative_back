"""
Validateurs pour le module properties
"""
from django.core.exceptions import ValidationError


def validate_image_size(image):
    """
    Valide que la taille de l'image ne dépasse pas 5 MB
    """
    max_size_mb = 5
    if image.size > max_size_mb * 1024 * 1024:
        raise ValidationError(f"La taille de l'image ne doit pas dépasser {max_size_mb} MB")


def validate_image_format(image):
    """
    Valide que le format de l'image est autorisé
    """
    allowed_formats = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
    if image.content_type not in allowed_formats:
        raise ValidationError("Format d'image non autorisé. Utilisez JPG, PNG ou WEBP")
