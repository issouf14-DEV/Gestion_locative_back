"""
Services pour le module notifications
"""
from typing import Dict, List
from django.core.mail import send_mail
from django.conf import settings

from .models import Notification
from apps.users.models import User


class NotificationService:
    """
    Service pour l'envoi et la gestion des notifications
    """
    
    @staticmethod
    def creer_notification(
        destinataire: User,
        titre: str,
        message: str,
        type_notification: str = 'INFO',
        lien: str = '',
        metadata: dict | None = None,
        envoyer_email: bool = True
    ) -> Notification:
        """
        Crée une nouvelle notification
        
        Args:
            destinataire: L'utilisateur destinataire
            titre: Titre de la notification
            message: Message
            type_notification: Type (INFO, SUCCESS, WARNING, ERROR, FACTURE, PAIEMENT, etc.)
            lien: Lien associé (optionnel)
            metadata: Données supplémentaires (optionnel)
            envoyer_email: Si True, envoie aussi un email
        
        Returns:
            La notification créée
        """
        notification = Notification.objects.create(
            destinataire=destinataire,
            titre=titre,
            message=message,
            type_notification=type_notification,
            lien=lien,
            metadata=metadata or {}
        )
        
        # Envoyer email si activé
        if envoyer_email and hasattr(destinataire, 'profile'):
            if destinataire.profile.notifications_email:  # type: ignore[union-attr]
                NotificationService._envoyer_email(destinataire, titre, message)
        
        return notification
    
    @staticmethod
    def envoyer_notification_multiple(
        destinataires_ids: List[int],
        titre: str,
        message: str,
        type_notification: str = 'INFO',
        lien: str = ''
    ) -> Dict:
        """
        Envoie une notification à plusieurs utilisateurs
        """
        destinataires = User.objects.filter(id__in=destinataires_ids, is_active=True)
        notifications_creees = []
        
        for user in destinataires:
            notif = NotificationService.creer_notification(
                destinataire=user,
                titre=titre,
                message=message,
                type_notification=type_notification,
                lien=lien
            )
            notifications_creees.append(notif)
        
        return {
            'envoyees': len(notifications_creees),
            'destinataires': [str(n.destinataire.id) for n in notifications_creees]
        }
    
    @staticmethod
    def envoyer_a_tous_locataires(
        titre: str,
        message: str,
        type_notification: str = 'INFO'
    ) -> Dict:
        """
        Envoie une notification à tous les locataires actifs
        """
        locataires = User.objects.get_locataires()  # type: ignore[attr-defined]
        count = 0
        
        for locataire in locataires:
            NotificationService.creer_notification(
                destinataire=locataire,
                titre=titre,
                message=message,
                type_notification=type_notification
            )
            count += 1
        
        return {'envoyees': count}
    
    @staticmethod
    def get_non_lues(user_id: str) -> int:
        """Compte les notifications non lues d'un utilisateur"""
        return Notification.objects.filter(
            destinataire_id=user_id,
            lu=False
        ).count()
    
    @staticmethod
    def marquer_toutes_lues(user_id: str) -> int:
        """Marque toutes les notifications d'un utilisateur comme lues"""
        from django.utils import timezone
        
        return Notification.objects.filter(
            destinataire_id=user_id,
            lu=False
        ).update(lu=True, date_lecture=timezone.now())
    
    @staticmethod
    def supprimer_anciennes_notifications(jours: int = 90) -> int:
        """
        Supprime les notifications plus anciennes que N jours
        Appelée par une tâche Celery périodique
        """
        from django.utils import timezone
        from datetime import timedelta
        
        date_limite = timezone.now() - timedelta(days=jours)
        count, _ = Notification.objects.filter(
            created_at__lt=date_limite,
            lu=True
        ).delete()
        
        return count
    
    @staticmethod
    def _envoyer_email(destinataire: User, titre: str, message: str):
        """Envoie un email de notification"""
        try:
            send_mail(
                subject=titre,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[destinataire.email],
                fail_silently=True
            )
        except Exception:
            pass  # Ne pas bloquer si l'email échoue


# Fonctions utilitaires pour les notifications courantes
def notifier_nouvelle_facture(locataire: User, facture):
    """Notifie un locataire d'une nouvelle facture"""
    NotificationService.creer_notification(
        destinataire=locataire,
        titre=f'Nouvelle facture - {facture.get_type_facture_display()}',
        message=f"Une nouvelle facture de {facture.montant} FCFA ({facture.get_type_facture_display()}) "
               f"a été générée. Échéance: {facture.date_echeance.strftime('%d/%m/%Y')}.",
        type_notification='FACTURE',
        metadata={'facture_id': str(facture.id), 'montant': float(facture.montant)}
    )


def notifier_paiement_valide(locataire: User, paiement):
    """Notifie un locataire que son paiement a été validé"""
    NotificationService.creer_notification(
        destinataire=locataire,
        titre='Paiement validé',
        message=f"Votre paiement de {paiement.montant} FCFA ({paiement.reference}) a été validé. Merci!",
        type_notification='PAIEMENT',
        metadata={'paiement_id': str(paiement.id)}
    )


def notifier_paiement_rejete(locataire: User, paiement, raison: str):
    """Notifie un locataire que son paiement a été rejeté"""
    NotificationService.creer_notification(
        destinataire=locataire,
        titre='Paiement rejeté',
        message=f"Votre paiement de {paiement.montant} FCFA ({paiement.reference}) a été rejeté. "
               f"Raison: {raison}",
        type_notification='WARNING',
        metadata={'paiement_id': str(paiement.id), 'raison': raison}
    )


def notifier_rappel_echeance(locataire: User, facture, jours_restants: int):
    """Envoie un rappel pour une facture proche de l'échéance"""
    NotificationService.creer_notification(
        destinataire=locataire,
        titre=f'Rappel - Facture à payer',
        message=f"Votre facture {facture.reference} de {facture.montant} FCFA "
               f"est due dans {jours_restants} jour(s).",
        type_notification='RAPPEL',
        metadata={'facture_id': str(facture.id), 'jours_restants': jours_restants}
    )
