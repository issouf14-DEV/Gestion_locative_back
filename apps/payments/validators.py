"""
Validateurs pour le module payments
"""
from decimal import Decimal
from django.core.exceptions import ValidationError


def validate_montant_paiement(montant: Decimal):
    """
    Valide que le montant du paiement est valide
    """
    if montant <= 0:
        raise ValidationError("Le montant du paiement doit être supérieur à 0")
    
    if montant > Decimal('100000000'):  # 100 millions FCFA max
        raise ValidationError("Le montant du paiement est trop élevé")


def validate_preuve_paiement_size(image):
    """
    Valide que la taille de la preuve de paiement ne dépasse pas 10 MB
    """
    max_size_mb = 10
    if image.size > max_size_mb * 1024 * 1024:
        raise ValidationError(f"La taille de l'image ne doit pas dépasser {max_size_mb} MB")


def validate_preuve_paiement_format(image):
    """
    Valide que le format de la preuve de paiement est autorisé
    """
    allowed_formats = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp', 'application/pdf']
    if hasattr(image, 'content_type') and image.content_type not in allowed_formats:
        raise ValidationError("Format de fichier non autorisé. Utilisez JPG, PNG, WEBP ou PDF")


def validate_factures_ids(factures_ids: list):
    """
    Valide que la liste des factures n'est pas vide
    """
    if not factures_ids:
        raise ValidationError("Vous devez sélectionner au moins une facture à payer")
    
    if len(factures_ids) > 50:
        raise ValidationError("Vous ne pouvez pas payer plus de 50 factures à la fois")


def validate_reference_paiement(reference: str):
    """
    Valide le format de la référence de paiement
    """
    if not reference:
        raise ValidationError("La référence de paiement est requise")
    
    if len(reference) < 6:
        raise ValidationError("La référence de paiement doit contenir au moins 6 caractères")
