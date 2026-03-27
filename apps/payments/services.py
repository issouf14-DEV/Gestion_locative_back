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


class EncaissementService:
    """
    Service pour l'encaissement direct des loyers et factures par l'admin
    Sans validation - paiement enregistré directement comme validé
    """
    
    @staticmethod
    def encaisser_loyer(
        locataire_id: str,
        mois: int,
        annee: int,
        montant: Decimal,
        mode_paiement: str = 'ESPECES',
        reference_paiement: str = '',
        notes: str = '',
        admin: Optional[User] = None
    ) -> Dict:
        """
        Encaisse le loyer d'un locataire (Admin)
        
        Args:
            locataire_id: ID du locataire
            mois: Mois du loyer
            annee: Année du loyer
            montant: Montant encaissé
            mode_paiement: ESPECES, VIREMENT, MOBILE_MONEY, CHEQUE
            reference_paiement: Référence du paiement externe
            notes: Notes supplémentaires
            admin: L'admin qui fait l'encaissement
        """
        from apps.users.models import User as UserModel
        
        locataire = UserModel.objects.get(id=locataire_id)
        
        # Trouver la facture de loyer correspondante
        facture = Facture.objects.filter(
            locataire=locataire,
            type_facture='LOYER',
            mois=mois,
            annee=annee,
            statut__in=['EN_ATTENTE', 'EN_RETARD']
        ).first()
        
        if not facture:
            raise ValueError(f"Aucune facture de loyer trouvée pour {locataire.get_full_name()} - {mois}/{annee}")
        
        with transaction.atomic():
            # Créer le paiement validé directement
            paiement = Paiement.objects.create(
                locataire=locataire,
                montant=montant,
                factures_ids=[str(facture.id)],
                notes_locataire=f"Encaissement direct - {mode_paiement}" + (f" - Réf: {reference_paiement}" if reference_paiement else ""),
                statut='VALIDE',
                validateur=admin,
                date_validation=timezone.now(),
                commentaire_admin=notes or f"Encaissement {mode_paiement}"
            )
            
            # Marquer la facture comme payée
            facture.statut = 'PAYEE'
            facture.save()
            
            # Mettre à jour le statut du locataire
            PaiementService._mettre_a_jour_statut_locataire(locataire)
            
            # Notifier le locataire
            Notification.objects.create(
                destinataire=locataire,
                type_notification='PAIEMENT',
                titre="Loyer encaissé",
                message=f"Votre loyer de {mois}/{annee} ({montant:,.0f} FCFA) a été enregistré. Merci!"
            )
        
        return {
            'success': True,
            'paiement_id': str(paiement.id),
            'reference': paiement.reference,
            'locataire': locataire.get_full_name(),
            'montant': float(montant),
            'mois': mois,
            'annee': annee,
            'mode_paiement': mode_paiement,
            'message': f"Loyer de {locataire.get_full_name()} encaissé avec succès"
        }
    
    @staticmethod
    def encaisser_facture(
        facture_id: str,
        montant: Decimal,
        mode_paiement: str = 'ESPECES',
        reference_paiement: str = '',
        notes: str = '',
        admin: Optional[User] = None
    ) -> Dict:
        """
        Encaisse une facture spécifique (loyer, SODECI, CIE, etc.)
        
        Args:
            facture_id: ID de la facture
            montant: Montant encaissé
            mode_paiement: Mode de paiement
            reference_paiement: Référence externe
            notes: Notes
            admin: Admin qui encaisse
        """
        facture = Facture.objects.select_related('locataire').get(id=facture_id)
        
        if facture.statut == 'PAYEE':
            raise ValueError("Cette facture est déjà payée")
        
        locataire = facture.locataire
        
        with transaction.atomic():
            # Créer le paiement
            paiement = Paiement.objects.create(
                locataire=locataire,
                montant=montant,
                factures_ids=[str(facture.id)],
                notes_locataire=f"Encaissement - {mode_paiement}" + (f" - Réf: {reference_paiement}" if reference_paiement else ""),
                statut='VALIDE',
                validateur=admin,
                date_validation=timezone.now(),
                commentaire_admin=notes or f"Encaissement {mode_paiement}"
            )
            
            # Marquer la facture comme payée
            facture.statut = 'PAYEE'
            facture.save()
            
            # Mettre à jour statut locataire
            PaiementService._mettre_a_jour_statut_locataire(locataire)
            
            # Notification
            type_display = getattr(facture, 'get_type_facture_display', lambda: facture.type_facture)()
            Notification.objects.create(
                destinataire=locataire,
                type_notification='PAIEMENT',
                titre=f"Paiement {type_display} enregistré",
                message=f"Votre paiement de {montant:,.0f} FCFA pour {type_display} ({facture.mois}/{facture.annee}) a été enregistré."
            )
        
        return {
            'success': True,
            'paiement_id': str(paiement.id),
            'reference': paiement.reference,
            'facture_reference': facture.reference,
            'type_facture': facture.type_facture,
            'locataire': locataire.get_full_name(),
            'montant': float(montant),
            'message': f"Paiement enregistré pour {locataire.get_full_name()}"
        }
    
    @staticmethod
    def encaisser_multiple(
        factures_ids: List[str],
        montant_total: Decimal,
        mode_paiement: str = 'ESPECES',
        reference_paiement: str = '',
        notes: str = '',
        admin: Optional[User] = None
    ) -> Dict:
        """
        Encaisse plusieurs factures en une seule opération
        
        Args:
            factures_ids: Liste des IDs de factures
            montant_total: Montant total encaissé
            mode_paiement: Mode de paiement
            reference_paiement: Référence
            notes: Notes
            admin: Admin
        """
        factures = Facture.objects.filter(
            id__in=factures_ids,
            statut__in=['EN_ATTENTE', 'EN_RETARD']
        ).select_related('locataire')
        
        if not factures.exists():
            raise ValueError("Aucune facture valide trouvée")
        
        # Vérifier que toutes les factures sont du même locataire
        locataires = set(f.locataire.id for f in factures)  # type: ignore
        if len(locataires) > 1:
            raise ValueError("Toutes les factures doivent appartenir au même locataire")
        
        locataire = factures.first().locataire  # type: ignore
        
        with transaction.atomic():
            # Créer le paiement
            paiement = Paiement.objects.create(
                locataire=locataire,
                montant=montant_total,
                factures_ids=[str(f.id) for f in factures],
                notes_locataire=f"Encaissement multiple - {mode_paiement}" + (f" - Réf: {reference_paiement}" if reference_paiement else ""),
                statut='VALIDE',
                validateur=admin,
                date_validation=timezone.now(),
                commentaire_admin=notes or f"Encaissement multiple {mode_paiement}"
            )
            
            # Marquer toutes les factures comme payées
            factures.update(statut='PAYEE')
            
            # Mettre à jour statut locataire
            PaiementService._mettre_a_jour_statut_locataire(locataire)
            
            # Notification
            Notification.objects.create(
                destinataire=locataire,
                type_notification='PAIEMENT',
                titre="Paiements enregistrés",
                message=f"Vos paiements ({montant_total:,.0f} FCFA) ont été enregistrés pour {factures.count()} facture(s)."
            )
        
        return {
            'success': True,
            'paiement_id': str(paiement.id),
            'reference': paiement.reference,
            'locataire': locataire.get_full_name(),
            'montant': float(montant_total),
            'nombre_factures': factures.count(),
            'message': f"{factures.count()} facture(s) payée(s) pour {locataire.get_full_name()}"
        }
    
    @staticmethod
    def get_factures_impayees_locataire(locataire_id: str) -> List[Dict]:
        """
        Liste les factures impayées d'un locataire
        """
        factures = Facture.objects.filter(
            locataire_id=locataire_id,
            statut__in=['EN_ATTENTE', 'EN_RETARD']
        ).order_by('-annee', '-mois')
        
        return [
            {
                'id': str(f.id),
                'reference': f.reference,
                'type': f.type_facture,
                'type_display': getattr(f, 'get_type_facture_display', lambda: f.type_facture)(),
                'mois': f.mois,
                'annee': f.annee,
                'montant': float(f.montant),
                'statut': f.statut,
                'date_echeance': f.date_echeance.isoformat() if f.date_echeance else None,
                'en_retard': f.statut == 'EN_RETARD'
            }
            for f in factures
        ]
    
    @staticmethod
    def get_resume_encaissements_mois(mois: int, annee: int) -> Dict:
        """
        Résumé des encaissements du mois
        """
        from django.db.models import Sum, Count
        
        paiements = Paiement.objects.filter(
            statut='VALIDE',
            date_validation__month=mois,
            date_validation__year=annee
        )
        
        stats = paiements.aggregate(
            total=Sum('montant'),
            nombre=Count('id')
        )
        
        return {
            'mois': mois,
            'annee': annee,
            'total_encaisse': float(stats['total'] or 0),
            'nombre_paiements': stats['nombre'] or 0
        }
