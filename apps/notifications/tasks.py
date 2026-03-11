"""
Tâches Celery pour le module notifications
"""
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings


@shared_task(bind=True, max_retries=3)
def envoyer_email_async(self, destinataire_email: str, sujet: str, message: str):
    """
    Envoie un email de manière asynchrone
    
    Args:
        destinataire_email: Email du destinataire
        sujet: Sujet de l'email
        message: Corps du message
    """
    try:
        send_mail(
            subject=sujet,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[destinataire_email],
            fail_silently=False,
        )
        return {'success': True, 'email': destinataire_email}
    except Exception as exc:
        self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3)
def envoyer_notification_email_async(self, notification_id: int):
    """
    Envoie l'email associé à une notification de manière asynchrone
    
    Args:
        notification_id: ID de la notification
    """
    from .models import Notification
    
    try:
        notification = Notification.objects.select_related('destinataire').get(id=notification_id)
        
        if hasattr(notification.destinataire, 'email'):
            send_mail(
                subject=notification.titre,
                message=notification.message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[notification.destinataire.email],
                fail_silently=False,
            )
        
        return {'success': True, 'notification_id': notification_id}
    except Notification.DoesNotExist:
        return {'success': False, 'error': 'Notification non trouvée'}
    except Exception as exc:
        self.retry(exc=exc, countdown=60)


@shared_task
def envoyer_rappel_factures():
    """
    Tâche planifiée pour envoyer des rappels de factures en attente
    """
    from apps.billing.models import Facture
    from django.utils import timezone
    from datetime import timedelta
    from .services import NotificationService
    
    # Factures dont l'échéance est dans 3 jours
    date_limite = timezone.now().date() + timedelta(days=3)
    
    factures = Facture.objects.filter(
        statut='EN_ATTENTE',
        date_echeance=date_limite
    ).select_related('locataire')
    
    for facture in factures:
        NotificationService.creer_notification(
            destinataire=facture.locataire,
            titre="Rappel: Facture à payer",
            message=f"Votre facture {facture.type_facture} de {facture.montant} FCFA arrive à échéance le {facture.date_echeance}.",
            type_notification='RAPPEL',
            envoyer_email=True
        )
    
    return {'factures_rappelees': factures.count()}


@shared_task
def marquer_notifications_expirees():
    """
    Marque les anciennes notifications comme lues automatiquement
    """
    from .models import Notification
    from django.utils import timezone
    from datetime import timedelta
    
    # Notifications non lues depuis plus de 30 jours
    date_limite = timezone.now() - timedelta(days=30)
    
    updated = Notification.objects.filter(
        lu=False,
        created_at__lt=date_limite
    ).update(lu=True)
    
    return {'notifications_marquees': updated}
