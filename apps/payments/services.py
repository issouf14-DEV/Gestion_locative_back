"""
Services pour le module payments - Validation manuelle des paiements
"""
from decimal import Decimal
from datetime import date
from typing import Dict, Any, Optional, List
from django.db import transaction
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

from .models import Paiement
from apps.billing.models import Facture
from apps.users.models import User
from apps.notifications.models import Notification


class PaiementService:
    """
    Service pour la gestion des paiements et validation manuelle
    """
    
    @staticmethod
    def soumettre_paiement(
        locataire: User,
        montant: Decimal,
        factures_ids: List[int],
        preuve_path: str,
        notes: str = ""
    ) -> Dict:
        """
        Soumet un nouveau paiement pour validation
        
        Args:
            locataire: L'utilisateur qui soumet le paiement
            montant: Montant payé
            factures_ids: Liste des IDs des factures concernées
            preuve_path: Chemin vers la preuve de paiement
            notes: Notes optionnelles du locataire
        
        Returns:
            Dict avec les détails du paiement créé
        """
        # Vérifier que les factures existent et appartiennent au locataire
        factures = Facture.objects.filter(
            id__in=factures_ids,
            locataire=locataire,
            statut__in=['EN_ATTENTE', 'EN_RETARD']
        )
        
        if factures.count() != len(factures_ids):
            raise ValueError("Certaines factures n'existent pas ou ne vous appartiennent pas")
        
        # Créer le paiement
        paiement = Paiement.objects.create(
            locataire=locataire,
            montant=montant,
            factures_ids=factures_ids,
            preuve=preuve_path,
            notes_locataire=notes,
            statut='EN_ATTENTE'
        )
        
        # Notifier les admins
        PaiementService._notifier_admins_nouveau_paiement(paiement)
        
        return {
            'success': True,
            'paiement_id': str(paiement.id),
            'reference': paiement.reference,
            'montant': float(paiement.montant),
            'statut': paiement.statut,
            'message': 'Votre paiement a été soumis et est en attente de validation'
        }
    
    @staticmethod
    def valider_paiement(
        paiement: Paiement,
        admin: User,
        commentaire: str = ""
    ) -> Dict:
        """
        Valide un paiement (Admin uniquement)
        
        Args:
            paiement: Le paiement à valider
            admin: L'administrateur qui valide
            commentaire: Commentaire optionnel
        
        Returns:
            Dict avec les détails de la validation
        """
        if paiement.statut != 'EN_ATTENTE':
            raise ValueError(f"Ce paiement ne peut pas être validé (statut: {paiement.statut})")
        
        with transaction.atomic():
            # Mettre à jour le paiement
            paiement.statut = 'VALIDE'
            paiement.validateur = admin
            paiement.date_validation = timezone.now()
            paiement.commentaire_admin = commentaire
            paiement.save()
            
            # Marquer les factures comme payées
            factures = Facture.objects.filter(id__in=paiement.factures_ids)
            factures.update(statut='PAYEE')
            
            # Mettre à jour le statut du locataire si plus de dettes
            PaiementService._mettre_a_jour_statut_locataire(paiement.locataire)
            
            # Notifier le locataire
            PaiementService._notifier_locataire_validation(paiement, validé=True)
        
        return {
            'success': True,
            'paiement_id': str(paiement.id),
            'reference': paiement.reference,
            'statut': 'VALIDE',
            'validateur': admin.get_full_name(),
            'date_validation': paiement.date_validation.isoformat() if paiement.date_validation else None  # type: ignore[union-attr]
        }
    
    @staticmethod
    def rejeter_paiement(
        paiement: Paiement,
        admin: User,
        raison: str
    ) -> Dict:
        """
        Rejette un paiement (Admin uniquement)
        
        Args:
            paiement: Le paiement à rejeter
            admin: L'administrateur qui rejette
            raison: Raison du rejet (obligatoire)
        
        Returns:
            Dict avec les détails du rejet
        """
        if paiement.statut != 'EN_ATTENTE':
            raise ValueError(f"Ce paiement ne peut pas être rejeté (statut: {paiement.statut})")
        
        if not raison:
            raise ValueError("Une raison de rejet est obligatoire")
        
        paiement.statut = 'REJETE'
        paiement.validateur = admin
        paiement.date_validation = timezone.now()
        paiement.commentaire_admin = raison
        paiement.save()
        
        # Notifier le locataire
        PaiementService._notifier_locataire_validation(paiement, validé=False)
        
        return {
            'success': True,
            'paiement_id': str(paiement.id),
            'reference': paiement.reference,
            'statut': 'REJETE',
            'raison': raison
        }
    
    @staticmethod
    def get_paiements_en_attente() -> Any:
        """
        Récupère tous les paiements en attente de validation
        """
        return Paiement.objects.filter(
            statut='EN_ATTENTE'
        ).select_related('locataire').order_by('-created_at')
    
    @staticmethod
    def get_historique_paiements(
        locataire_id: Optional[str] = None,
        statut: Optional[str] = None,
        date_debut: Optional[date] = None,
        date_fin: Optional[date] = None
    ) -> Any:
        """
        Récupère l'historique des paiements avec filtres optionnels
        """
        queryset = Paiement.objects.all()
        
        if locataire_id:
            queryset = queryset.filter(locataire_id=locataire_id)
        if statut:
            queryset = queryset.filter(statut=statut)
        if date_debut:
            queryset = queryset.filter(created_at__date__gte=date_debut)
        if date_fin:
            queryset = queryset.filter(created_at__date__lte=date_fin)
        
        return queryset.select_related('locataire', 'validateur').order_by('-created_at')
    
    @staticmethod
    def get_statistiques_paiements(mois: int | None = None, annee: int | None = None) -> Dict:
        """
        Obtient les statistiques de paiements
        """
        from django.db.models import Sum, Count
        
        queryset = Paiement.objects.all()
        
        if mois and annee:
            queryset = queryset.filter(
                created_at__month=mois,
                created_at__year=annee
            )
        elif annee:
            queryset = queryset.filter(created_at__year=annee)
        
        stats = queryset.aggregate(
            total_soumis=Count('id'),
            montant_total=Sum('montant')
        )
        
        valides = queryset.filter(statut='VALIDE').aggregate(
            count=Count('id'),
            montant=Sum('montant')
        )
        
        rejetes = queryset.filter(statut='REJETE').count()
        en_attente = queryset.filter(statut='EN_ATTENTE').count()
        
        return {
            'total_paiements': stats['total_soumis'] or 0,
            'montant_total_soumis': float(stats['montant_total'] or 0),
            'paiements_valides': valides['count'] or 0,
            'montant_valide': float(valides['montant'] or 0),
            'paiements_rejetes': rejetes,
            'paiements_en_attente': en_attente
        }
    
    @staticmethod
    def _notifier_admins_nouveau_paiement(paiement: Paiement):
        """Notifie les admins d'un nouveau paiement"""
        admins = User.objects.get_admins()  # type: ignore[attr-defined]
        
        for admin in admins:
            Notification.objects.create(
                destinataire=admin,
                type_notification='PAIEMENT',
                titre='Nouveau paiement à valider',
                message=f"Un paiement de {paiement.montant} FCFA soumis par "
                       f"{paiement.locataire.get_full_name()} est en attente de validation."
            )
        
        # Envoyer email aux admins
        try:
            for admin in admins:
                if hasattr(admin, 'profile') and admin.profile.notifications_email:  # type: ignore[union-attr]
                    context = {
                        'admin': admin,
                        'paiement': paiement,
                        'locataire': paiement.locataire,
                    }
                    message = render_to_string('emails/payment_validation.html', context)
                    
                    send_mail(
                        subject=f"Nouveau paiement à valider - {paiement.reference}",
                        message='',
                        html_message=message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[admin.email],
                        fail_silently=True
                    )
        except Exception:
            pass
    
    @staticmethod
    def _notifier_locataire_validation(paiement: Paiement, validé: bool):
        """Notifie le locataire du résultat de la validation"""
        if validé:
            titre = "Paiement validé"
            message = f"Votre paiement de {paiement.montant} FCFA ({paiement.reference}) a été validé."
        else:
            titre = "Paiement rejeté"
            message = f"Votre paiement de {paiement.montant} FCFA ({paiement.reference}) a été rejeté. " \
                     f"Raison: {paiement.commentaire_admin}"
        
        Notification.objects.create(
            destinataire=paiement.locataire,
            type_notification='PAIEMENT',
            titre=titre,
            message=message
        )
        
        # Envoyer email au locataire
        try:
            if hasattr(paiement.locataire, 'profile') and paiement.locataire.profile.notifications_email:  # type: ignore[union-attr]
                send_mail(
                    subject=titre,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[paiement.locataire.email],
                    fail_silently=True
                )
        except Exception:
            pass
    
    @staticmethod
    def _mettre_a_jour_statut_locataire(locataire: User):
        """Met à jour le statut du locataire selon ses dettes"""
        factures_impayees = Facture.objects.filter(
            locataire=locataire,
            statut__in=['EN_ATTENTE', 'EN_RETARD']
        ).count()
        
        if factures_impayees == 0:
            locataire.statut = 'A_JOUR'
            locataire.save(update_fields=['statut'])
