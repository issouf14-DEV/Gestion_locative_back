"""
Calculateur pour la répartition des factures SODECI/CIE
"""
from decimal import Decimal
from typing import Dict
from django.db import transaction
from django.utils import timezone
from .models import Facture, FactureCollective, IndexCompteur


class FactureCalculator:
    """
    Classe pour calculer la répartition des factures SODECI/CIE
    """
    
    @staticmethod
    def calculer_repartition(
        type_facture: str,
        montant_total: Decimal,
        mois: int,
        annee: int,
        date_echeance
    ) -> Dict:
        """
        Calcule la répartition d'une facture collective entre les locataires
        
        Args:
            type_facture: 'SODECI' ou 'CIE'
            montant_total: Montant total de la facture
            mois: Mois concerné (1-12)
            annee: Année concernée
            date_echeance: Date d'échéance pour paiement
        
        Returns:
            Dict avec les détails de la répartition
        """
        
        # 1. Récupérer tous les index du mois pour ce type
        index_mois = IndexCompteur.objects.filter(
            type_compteur=type_facture,
            mois=mois,
            annee=annee
        ).select_related('locataire')
        
        if not index_mois.exists():
            raise ValueError(f"Aucun index trouvé pour {type_facture} {mois}/{annee}")
        
        # 2. Préparer les données de chaque locataire
        locataires_data = []
        
        for index_actuel in index_mois:
            # Récupérer l'index du mois précédent
            mois_prec = mois - 1 if mois > 1 else 12
            annee_prec = annee if mois > 1 else annee - 1
            
            try:
                index_prec = IndexCompteur.objects.get(
                    locataire=index_actuel.locataire,
                    type_compteur=type_facture,
                    mois=mois_prec,
                    annee=annee_prec
                )
                index_ancien = index_prec.index_valeur
            except IndexCompteur.DoesNotExist:
                # Si pas d'index précédent, prendre 0
                index_ancien = Decimal('0')
            
            # Calculer la consommation
            consommation = index_actuel.index_valeur - index_ancien
            
            if consommation < 0:
                raise ValueError(
                    f"Consommation négative pour {index_actuel.locataire.get_full_name()}: "
                    f"{index_ancien} -> {index_actuel.index_valeur}"
                )
            
            locataires_data.append({
                'locataire': index_actuel.locataire,
                'index_ancien': index_ancien,
                'index_nouveau': index_actuel.index_valeur,
                'consommation': consommation
            })
        
        # 3. Calculer le total de consommation
        total_consommation = sum(d['consommation'] for d in locataires_data)
        
        if total_consommation == 0:
            raise ValueError("Consommation totale est zéro, impossible de répartir")
        
        # 4. Calculer pourcentage et montant pour chaque locataire
        factures_creees = []
        
        for data in locataires_data:
            pourcentage = (data['consommation'] / total_consommation) * 100
            montant = (pourcentage / 100) * montant_total
            
            # Arrondir
            pourcentage = round(pourcentage, 2)
            montant = round(montant, 0)
            
            data['pourcentage'] = pourcentage
            data['montant'] = montant
            factures_creees.append(data)
        
        # 5. Créer les factures individuelles dans une transaction
        with transaction.atomic():
            # Créer ou mettre à jour la facture collective
            facture_collective, _ = FactureCollective.objects.update_or_create(
                type_facture=type_facture,
                mois=mois,
                annee=annee,
                defaults={
                    'montant_total': montant_total,
                    'consommation_totale': total_consommation,
                    'repartie': True,
                    'date_repartition': timezone.now()
                }
            )
            
            # Créer les factures individuelles
            for data in factures_creees:
                Facture.objects.update_or_create(
                    locataire=data['locataire'],
                    type_facture=type_facture,
                    mois=mois,
                    annee=annee,
                    defaults={
                        'montant': data['montant'],
                        'index_ancien': data['index_ancien'],
                        'index_nouveau': data['index_nouveau'],
                        'consommation': data['consommation'],
                        'pourcentage': data['pourcentage'],
                        'date_echeance': date_echeance,
                        'statut': 'EN_ATTENTE'
                    }
                )
        
        return {
            'success': True,
            'facture_collective_id': facture_collective.id,
            'montant_total': float(montant_total),
            'consommation_totale': float(total_consommation),
            'nombre_locataires': len(factures_creees),
            'details': [
                {
                    'locataire_id': str(d['locataire'].id),
                    'locataire_nom': d['locataire'].get_full_name(),
                    'consommation': float(d['consommation']),
                    'pourcentage': float(d['pourcentage']),
                    'montant': float(d['montant'])
                }
                for d in factures_creees
            ]
        }
    
    @staticmethod
    def generer_factures_loyer(mois: int, annee: int, date_echeance):
        """
        Génère automatiquement les factures de loyer pour tous les locataires actifs
        """
        from apps.rentals.models import Location
        
        # Récupérer toutes les locations actives
        locations_actives = Location.objects.filter(statut='ACTIVE').select_related('locataire')
        
        factures_creees = []
        
        with transaction.atomic():
            for location in locations_actives:
                facture, _ = Facture.objects.update_or_create(
                    locataire=location.locataire,
                    type_facture='LOYER',
                    mois=mois,
                    annee=annee,
                    defaults={
                        'montant': location.loyer_mensuel,
                        'date_echeance': date_echeance,
                        'statut': 'EN_ATTENTE'
                    }
                )
                factures_creees.append(facture)
        
        return {
            'success': True,
            'nombre_factures': len(factures_creees),
            'montant_total': sum(f.montant for f in factures_creees)
        }
