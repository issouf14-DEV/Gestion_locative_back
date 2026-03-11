"""
Services pour le dashboard
"""
from django.utils import timezone
from django.db.models import Sum, Count
from apps.properties.models import Maison
from apps.users.models import User
from apps.billing.models import Facture
from apps.expenses.models import Depense
from apps.rentals.models import Location


class DashboardService:
    """
    Service pour calculer les statistiques du dashboard
    """
    
    @staticmethod
    def get_admin_stats():
        """
        Calcule les statistiques pour le dashboard administrateur
        """
        now = timezone.now()
        mois_courant = now.month
        annee_courante = now.year
        
        # Statistiques maisons
        total_maisons = Maison.objects.count()
        maisons_disponibles = Maison.objects.filter(statut='DISPONIBLE').count()
        maisons_louees = Maison.objects.filter(statut='LOUEE').count()
        
        # Statistiques locataires
        total_locataires = User.objects.get_locataires().count()
        locataires_a_jour = User.objects.filter(role='LOCATAIRE', statut='A_JOUR').count()
        locataires_en_retard = User.objects.filter(role='LOCATAIRE', statut='EN_RETARD').count()
        
        # Revenus du mois
        factures_payees_mois = Facture.objects.filter(
            mois=mois_courant,
            annee=annee_courante,
            statut='PAYEE'
        )
        revenus_mois_courant = factures_payees_mois.aggregate(
            total=Sum('montant')
        )['total'] or 0
        
        # Dépenses du mois
        depenses_mois = Depense.objects.filter(
            date_depense__month=mois_courant,
            date_depense__year=annee_courante
        )
        depenses_mois_courant = depenses_mois.aggregate(
            total=Sum('montant')
        )['total'] or 0
        
        # Factures impayées
        factures_impayees = Facture.objects.filter(statut='EN_ATTENTE')
        montant_factures_impayees = factures_impayees.aggregate(
            total=Sum('montant')
        )['total'] or 0
        
        return {
            'total_maisons': total_maisons,
            'maisons_disponibles': maisons_disponibles,
            'maisons_louees': maisons_louees,
            'total_locataires': total_locataires,
            'locataires_a_jour': locataires_a_jour,
            'locataires_en_retard': locataires_en_retard,
            'revenus_mois_courant': revenus_mois_courant,
            'depenses_mois_courant': depenses_mois_courant,
            'factures_impayees': factures_impayees.count(),
            'montant_factures_impayees': montant_factures_impayees,
        }
    
    @staticmethod
    def get_locataire_stats(user):
        """
        Calcule les statistiques pour le dashboard d'un locataire
        """
        # Location actuelle
        try:
            location = Location.objects.get(locataire=user, statut='ACTIVE')
            location_info = {
                'maison_titre': location.maison.titre,
                'loyer_mensuel': float(location.loyer_mensuel),
                'date_debut': location.date_debut,
                'date_fin': location.date_fin,
            }
        except Location.DoesNotExist:
            location_info = None
        
        # Factures impayées
        factures_impayees = Facture.objects.filter(
            locataire=user,
            statut='EN_ATTENTE'
        )
        dette_totale = factures_impayees.aggregate(
            total=Sum('montant')
        )['total'] or 0
        
        # Historique paiements
        paiements_effectues = Facture.objects.filter(
            locataire=user,
            statut='PAYEE'
        ).count()
        
        return {
            'statut': user.statut,
            'dette_totale': float(dette_totale),
            'nombre_factures_impayees': factures_impayees.count(),
            'paiements_effectues': paiements_effectues,
            'location_actuelle': location_info,
        }
