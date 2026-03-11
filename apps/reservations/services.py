"""
Services pour le module reservations
"""
from typing import Dict
from django.db import transaction
from django.utils import timezone

from .models import Reservation
from apps.users.models import User
from apps.properties.models import Maison
from apps.notifications.services import NotificationService


class ReservationService:
    """
    Service pour la gestion des réservations
    """
    
    @staticmethod
    def creer_reservation(
        user: User,
        maison_id: int,
        date_debut_souhaitee,
        duree_mois: int,
        message: str = ""
    ) -> Dict:
        """
        Crée une nouvelle réservation
        
        Args:
            user: L'utilisateur qui fait la réservation
            maison_id: ID de la maison
            date_debut_souhaitee: Date de début souhaitée
            duree_mois: Durée en mois
            message: Message optionnel
        
        Returns:
            Dict avec les détails de la réservation
        """
        try:
            maison = Maison.objects.get(id=maison_id, disponible=True)
        except Maison.DoesNotExist:
            raise ValueError("Maison non trouvée ou non disponible")
        
        reservation = Reservation.objects.create(
            user=user,
            maison=maison,
            date_debut_souhaitee=date_debut_souhaitee,
            duree_mois=duree_mois,
            message=message
        )
        
        # Notifier les admins
        ReservationService._notifier_nouvelle_reservation(reservation)
        
        return {
            'success': True,
            'reservation_id': str(reservation.id),
            'reference': reservation.reference
        }
    
    @staticmethod
    def accepter_reservation(
        reservation_id: int,
        admin: User,
        reponse: str = ""
    ) -> Dict:
        """
        Accepte une réservation
        """
        try:
            reservation = Reservation.objects.get(id=reservation_id, statut='EN_ATTENTE')
        except Reservation.DoesNotExist:
            raise ValueError("Réservation non trouvée ou déjà traitée")
        
        with transaction.atomic():
            reservation.statut = 'ACCEPTEE'
            reservation.reponse_admin = reponse
            reservation.date_reponse = timezone.now()
            reservation.save()
            
            # Notifier le locataire
            NotificationService.creer_notification(
                destinataire=reservation.user,
                titre="Réservation acceptée",
                message=f"Votre réservation {reservation.reference} pour {reservation.maison.titre} a été acceptée.",
                type_notification='SUCCESS'
            )
        
        return {'success': True, 'statut': 'ACCEPTEE'}
    
    @staticmethod
    def refuser_reservation(
        reservation_id: int,
        admin: User,
        motif: str
    ) -> Dict:
        """
        Refuse une réservation
        """
        try:
            reservation = Reservation.objects.get(id=reservation_id, statut='EN_ATTENTE')
        except Reservation.DoesNotExist:
            raise ValueError("Réservation non trouvée ou déjà traitée")
        
        with transaction.atomic():
            reservation.statut = 'REFUSEE'
            reservation.reponse_admin = motif
            reservation.date_reponse = timezone.now()
            reservation.save()
            
            # Notifier le locataire
            NotificationService.creer_notification(
                destinataire=reservation.user,
                titre="Réservation refusée",
                message=f"Votre réservation {reservation.reference} a été refusée. Motif: {motif}",
                type_notification='WARNING'
            )
        
        return {'success': True, 'statut': 'REFUSEE'}
    
    @staticmethod
    def annuler_reservation(reservation_id: int, user: User) -> Dict:
        """
        Annule une réservation par l'utilisateur
        """
        try:
            reservation = Reservation.objects.get(
                id=reservation_id,
                user=user,
                statut='EN_ATTENTE'
            )
        except Reservation.DoesNotExist:
            raise ValueError("Réservation non trouvée ou ne peut pas être annulée")
        
        reservation.statut = 'ANNULEE'
        reservation.save()
        
        return {'success': True, 'statut': 'ANNULEE'}
    
    @staticmethod
    def _notifier_nouvelle_reservation(reservation: Reservation):
        """
        Notifie les administrateurs d'une nouvelle réservation
        """
        admins = User.objects.filter(role='ADMIN', is_active=True)
        
        for admin in admins:
            NotificationService.creer_notification(
                destinataire=admin,
                titre="Nouvelle réservation",
                message=f"Nouvelle réservation {reservation.reference} de {reservation.user.get_full_name()} pour {reservation.maison.titre}",
                type_notification='INFO',
                envoyer_email=True
            )
