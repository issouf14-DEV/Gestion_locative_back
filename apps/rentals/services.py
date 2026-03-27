"""
Services pour le module rentals - Gestion des locations
"""
from decimal import Decimal
from datetime import date, timedelta
from typing import Dict, Optional, Any
from django.db import transaction

from .models import Location
from apps.users.models import User
from apps.properties.models import Maison
from apps.notifications.models import Notification


class LocationService:
    """
    Service pour la gestion des locations
    """
    
    @staticmethod
    def creer_location(
        locataire: User,
        maison: Maison,
        date_debut: date,
        duree_mois: int,
        loyer_mensuel: Decimal,
        caution_versee: Decimal,
        notes: str = ""
    ) -> Dict:
        """
        Crée une nouvelle location
        
        Returns:
            Dict avec les détails de la location créée
        """
        if maison.statut != 'DISPONIBLE':
            raise ValueError(f"Cette maison n'est pas disponible (statut: {maison.statut})")
        
        # Vérifier que le locataire n'a pas déjà une location active
        location_existante = Location.objects.filter(
            locataire=locataire,
            statut='ACTIVE'
        ).first()
        
        if location_existante:
            raise ValueError(
                f"Ce locataire a déjà une location active: "
                f"{location_existante.maison.titre} ({location_existante.numero_contrat})"
            )
        
        # Calculer la date de fin
        date_fin = LocationService._calculer_date_fin(date_debut, duree_mois)
        
        with transaction.atomic():
            # Créer la location
            location = Location.objects.create(
                locataire=locataire,
                maison=maison,
                date_debut=date_debut,
                date_fin=date_fin,
                duree_mois=duree_mois,
                loyer_mensuel=loyer_mensuel,
                caution_versee=caution_versee,
                notes=notes,
                statut='ACTIVE'
            )
            
            # Mettre à jour le statut de la maison
            maison.statut = 'LOUEE'
            maison.save(update_fields=['statut'])
            
            # Notifier le locataire
            Notification.objects.create(
                destinataire=locataire,
                type_notification='LOCATION',
                titre='Bienvenue dans votre nouveau logement',
                message=f"Votre contrat de location pour {maison.titre} a été créé. "
                       f"Début: {date_debut.strftime('%d/%m/%Y')}, Durée: {duree_mois} mois."
            )
        
        return {
            'success': True,
            'location_id': str(location.id),
            'numero_contrat': location.numero_contrat,
            'date_debut': date_debut.isoformat(),
            'date_fin': date_fin.isoformat(),
            'duree_mois': duree_mois,
            'loyer_mensuel': float(loyer_mensuel)
        }
    
    @staticmethod
    def renouveler_location(
        location: Location,
        duree_supplementaire_mois: int
    ) -> Dict:
        """
        Renouvelle une location existante
        """
        if location.statut != 'ACTIVE':
            raise ValueError("Seules les locations actives peuvent être renouvelées")
        
        ancienne_date_fin = location.date_fin
        nouvelle_date_fin = LocationService._calculer_date_fin(
            ancienne_date_fin, duree_supplementaire_mois
        )
        
        location.date_fin = nouvelle_date_fin
        location.duree_mois += duree_supplementaire_mois
        location.save()
        
        # Notifier le locataire
        Notification.objects.create(
            destinataire=location.locataire,
            type_notification='LOCATION',
            titre='Renouvellement de location',
            message=f"Votre contrat a été renouvelé de {duree_supplementaire_mois} mois. "
                   f"Nouvelle date de fin: {nouvelle_date_fin.strftime('%d/%m/%Y')}."
        )
        
        return {
            'success': True,
            'ancienne_date_fin': ancienne_date_fin.isoformat(),
            'nouvelle_date_fin': nouvelle_date_fin.isoformat(),
            'nouvelle_duree_totale': location.duree_mois
        }
    
    @staticmethod
    def resilier_location(
        location: Location,
        raison: str = ""
    ) -> Dict:
        """
        Résilie une location
        """
        if location.statut in ['TERMINEE', 'RESILIEE']:
            raise ValueError(f"Cette location est déjà terminée (statut: {location.statut})")
        
        with transaction.atomic():
            location.statut = 'RESILIEE'
            location.notes = f"{location.notes}\nRésiliation: {raison}" if location.notes else f"Résiliation: {raison}"
            location.save()
            
            # Libérer la maison
            location.maison.statut = 'DISPONIBLE'
            location.maison.save(update_fields=['statut'])
            
            # Notifier le locataire
            Notification.objects.create(
                destinataire=location.locataire,
                type_notification='LOCATION',
                titre='Résiliation de location',
                message=f"Votre contrat de location pour {location.maison.titre} a été résilié."
            )
        
        return {
            'success': True,
            'location_id': str(location.id),
            'statut': 'RESILIEE'
        }
    
    @staticmethod
    def get_location_active(locataire_id: str) -> Optional[Location]:
        """
        Récupère la location active d'un locataire
        """
        return Location.objects.filter(
            locataire_id=locataire_id,
            statut='ACTIVE'
        ).select_related('maison').first()
    
    @staticmethod
    def get_locations_expirant_bientot(jours: int = 30) -> Any:
        """
        Récupère les locations qui expirent dans les N prochains jours
        """
        date_limite = date.today() + timedelta(days=jours)
        
        return Location.objects.filter(
            statut='ACTIVE',
            date_fin__lte=date_limite
        ).select_related('locataire', 'maison')
    
    @staticmethod
    def envoyer_rappels_expiration():
        """
        Envoie des rappels pour les locations qui expirent bientôt
        Appelé par une tâche Celery
        """
        locations = LocationService.get_locations_expirant_bientot(jours=30)
        rappels_envoyes = 0
        
        for location in locations:
            jours_restants = (location.date_fin - date.today()).days
            
            Notification.objects.create(
                destinataire=location.locataire,
                type_notification='RAPPEL',
                titre='Expiration prochaine de votre location',
                message=f"Votre contrat de location pour {location.maison.titre} "
                       f"expire dans {jours_restants} jours ({location.date_fin.strftime('%d/%m/%Y')}). "
                       f"Contactez l'administration pour renouveler."
            )
            rappels_envoyes += 1
        
        return {'rappels_envoyes': rappels_envoyes}
    
    @staticmethod
    def get_statistiques_locations() -> Dict:
        """
        Obtient les statistiques des locations
        """
        from django.db.models import Sum, Count, Avg
        
        stats = Location.objects.aggregate(
            total=Count('id'),
            actives=Count('id', filter=models.Q(statut='ACTIVE')),
            terminees=Count('id', filter=models.Q(statut='TERMINEE')),
            resilies=Count('id', filter=models.Q(statut='RESILIEE')),
            loyer_mensuel_total=Sum('loyer_mensuel', filter=models.Q(statut='ACTIVE')),
            loyer_moyen=Avg('loyer_mensuel', filter=models.Q(statut='ACTIVE')),
            cautions_total=Sum('caution_versee', filter=models.Q(statut='ACTIVE'))
        )
        
        return {
            'total_locations': stats['total'] or 0,
            'locations_actives': stats['actives'] or 0,
            'locations_terminees': stats['terminees'] or 0,
            'locations_resilies': stats['resilies'] or 0,
            'loyer_mensuel_total': float(stats['loyer_mensuel_total'] or 0),
            'loyer_moyen': float(stats['loyer_moyen'] or 0),
            'cautions_total': float(stats['cautions_total'] or 0)
        }
    
    @staticmethod
    def calculer_duree_restante(location: Location) -> Dict:
        """
        Calcule la durée restante d'une location
        """
        if location.statut != 'ACTIVE':
            return {
                'jours_restants': 0,
                'mois_restants': 0,
                'pourcentage_ecoule': 100
            }
        
        today = date.today()
        jours_restants = (location.date_fin - today).days
        mois_restants = jours_restants // 30
        
        duree_totale = (location.date_fin - location.date_debut).days
        jours_ecoules = (today - location.date_debut).days
        pourcentage_ecoule = round((jours_ecoules / duree_totale) * 100, 1) if duree_totale > 0 else 0
        
        return {
            'jours_restants': max(0, jours_restants),
            'mois_restants': max(0, mois_restants),
            'pourcentage_ecoule': min(100, pourcentage_ecoule)
        }
    
    @staticmethod
    def _calculer_date_fin(date_debut: date, duree_mois: int) -> date:
        """Calcule la date de fin en ajoutant des mois"""
        from apps.core.utils import add_months_to_date
        return add_months_to_date(date_debut, duree_mois)


# Import nécessaire pour l'agrégation
from django.db import models
