"""
Gestion des tokens personnalisés pour la réinitialisation de mot de passe et la vérification d'email
"""
from typing import TYPE_CHECKING
from django.contrib.auth.tokens import PasswordResetTokenGenerator
import six

if TYPE_CHECKING:
    from apps.users.models import User


class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
    """
    Générateur de token pour la vérification d'email
    """
    def _make_hash_value(self, user: "User", timestamp) -> str:
        return (
            six.text_type(user.pk) + six.text_type(timestamp) +
            six.text_type(user.email_verified)  # type: ignore[union-attr]
        )


account_activation_token = AccountActivationTokenGenerator()
password_reset_token = PasswordResetTokenGenerator()
