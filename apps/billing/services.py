"""
Services pour le module billing
"""
from decimal import Decimal
from datetime import timedelta
from typing import Dict, Any
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

from .models import Facture
from apps.users.models import User
from apps.notifications.models import Notification


class BillingService:
    """
    Service pour la gestion de la facturation
    """
    
    @staticmethod
    def calculer_dette_locataire(locataire_id: str) -> Dict:
        """
        Calcule la dette totale d'un locataire
        
        Returns:
            Dict avec le détail des dettes par type
        """
        factures_impayees = Facture.objects.filter(
            locataire_id=locataire_id,
            statut='EN_ATTENTE'
        )
        
        dette_loyer = Decimal('0')
        dette_sodeci = Decimal('0')
        dette_cie = Decimal('0')
        dette_autre = Decimal('0')
        
        for facture in factures_impayees:
            if facture.type_facture == 'LOYER':
                dette_loyer += facture.montant
            elif facture.type_facture == 'SODECI':
                dette_sodeci += facture.montant
            elif facture.type_facture == 'CIE':
                dette_cie += facture.montant
            else:
                dette_autre += facture.montant
        
        total = dette_loyer + dette_sodeci + dette_cie + dette_autre
        
        return {
            'dette_loyer': float(dette_loyer),
            'dette_sodeci': float(dette_sodeci),
            'dette_cie': float(dette_cie),
            'dette_autre': float(dette_autre),
            'dette_totale': float(total),
            'nombre_factures_impayees': factures_impayees.count()
        }
    
    @staticmethod
    def marquer_factures_en_retard() -> Dict:
        """
        Marque automatiquement les factures en retard
        Appelée par une tâche Celery quotidienne
        """
        today = timezone.now().date()
        
        factures_en_retard = Facture.objects.filter(
            statut='EN_ATTENTE',
            date_echeance__lt=today
        )
        
        count = factures_en_retard.update(statut='EN_RETARD')
        
        # Mettre à jour le statut des locataires concernés
        locataires_ids = factures_en_retard.values_list('locataire_id', flat=True).distinct()
        User.objects.filter(id__in=locataires_ids).update(statut='EN_RETARD')
        
        return {
            'nombre_factures_marquees': count,
            'nombre_locataires_affectes': len(locataires_ids)
        }
    
    @staticmethod
    def envoyer_rappels_factures() -> Dict:
        """
        Envoie des rappels pour les factures proches de l'échéance ou en retard
        """
        today = timezone.now().date()
        rappel_date = today + timedelta(days=3)  # 3 jours avant échéance
        
        # Factures proches de l'échéance
        factures_a_rappeler = Facture.objects.filter(
            statut='EN_ATTENTE',
            date_echeance__lte=rappel_date,
            date_echeance__gte=today
        ).select_related('locataire')
        
        # Factures en retard
        factures_en_retard = Facture.objects.filter(
            statut='EN_RETARD'
        ).select_related('locataire')
        
        rappels_envoyes = 0
        
        for facture in list(factures_a_rappeler) + list(factures_en_retard):
            BillingService._envoyer_rappel_facture(facture)
            rappels_envoyes += 1
        
        return {
            'rappels_envoyes': rappels_envoyes
        }
    
    @staticmethod
    def _envoyer_rappel_facture(facture: Facture):
        """Envoie un rappel pour une facture spécifique"""
        locataire = facture.locataire
        
        # Créer une notification dans l'application
        Notification.objects.create(
            destinataire=locataire,
            type_notification='RAPPEL',
            titre=f"Rappel - Facture {facture.reference}",
            message=f"Votre facture {facture.get_type_facture_display()} de {facture.montant} FCFA "  # type: ignore[attr-defined]
                   f"est due le {facture.date_echeance.strftime('%d/%m/%Y')}."
        )
        
        # Envoyer un email si les notifications email sont activées
        if hasattr(locataire, 'profile') and locataire.profile.notifications_email:  # type: ignore[union-attr]
            try:
                context = {
                    'locataire': locataire,
                    'facture': facture,
                }
                message = render_to_string('emails/reminder.html', context)
                
                send_mail(
                    subject=f"Rappel - Facture {facture.reference}",
                    message='',
                    html_message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[locataire.email],
                    fail_silently=True
                )
            except Exception:
                pass  # Ne pas bloquer en cas d'erreur email
    
    @staticmethod
    def get_historique_factures(locataire_id: str, mois: int | None = None, annee: int | None = None) -> Any:
        """
        Récupère l'historique des factures d'un locataire
        """
        queryset = Facture.objects.filter(locataire_id=locataire_id)
        
        if mois:
            queryset = queryset.filter(mois=mois)
        if annee:
            queryset = queryset.filter(annee=annee)
        
        return queryset.order_by('-annee', '-mois', '-date_emission')
    
    @staticmethod
    def get_resume_mensuel(mois: int, annee: int) -> Dict:
        """
        Obtient un résumé des factures pour un mois donné
        """
        factures = Facture.objects.filter(mois=mois, annee=annee)
        
        total_loyer = factures.filter(type_facture='LOYER').aggregate(
            total=models.Sum('montant')
        )['total'] or Decimal('0')
        
        total_sodeci = factures.filter(type_facture='SODECI').aggregate(
            total=models.Sum('montant')
        )['total'] or Decimal('0')
        
        total_cie = factures.filter(type_facture='CIE').aggregate(
            total=models.Sum('montant')
        )['total'] or Decimal('0')
        
        payees = factures.filter(statut='PAYEE').count()
        en_attente = factures.filter(statut='EN_ATTENTE').count()
        en_retard = factures.filter(statut='EN_RETARD').count()
        
        return {
            'mois': mois,
            'annee': annee,
            'total_loyer': float(total_loyer),
            'total_sodeci': float(total_sodeci),
            'total_cie': float(total_cie),
            'total_general': float(total_loyer + total_sodeci + total_cie),
            'factures_payees': payees,
            'factures_en_attente': en_attente,
            'factures_en_retard': en_retard,
            'total_factures': payees + en_attente + en_retard
        }


# Import nécessaire pour l'agrégation
from django.db import models
