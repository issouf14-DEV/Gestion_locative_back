"""
Calculateur pour la répartition des factures SODECI/CIE

FORMULES SODECI/CIE:
====================
1. Consommation individuelle = Index_nouveau - Index_ancien
2. Consommation totale = Σ Consommation de tous les locataires
3. Pourcentage = (Consommation_i / Consommation_totale) × 100
4. Montant à payer = (Consommation_i / Consommation_totale) × Montant_facture

Exemple:
--------
Facture SODECI totale: 50,000 FCFA
Locataire A: 15 m³, Locataire B: 25 m³, Locataire C: 10 m³
Total: 50 m³

Locataire A paie: (15/50) × 50,000 = 15,000 FCFA (30%)
Locataire B paie: (25/50) × 50,000 = 25,000 FCFA (50%)
Locataire C paie: (10/50) × 50,000 = 10,000 FCFA (20%)
"""
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List
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
        # Formule: Consommation_totale = Σ (Index_nouveau_i - Index_ancien_i)
        total_consommation = sum(d['consommation'] for d in locataires_data)
        
        if total_consommation == 0:
            raise ValueError("Consommation totale est zéro, impossible de répartir")
        
        # 4. Calculer pourcentage et montant pour chaque locataire
        # Formules SODECI:
        #   Pourcentage_i = (Consommation_i / Consommation_totale) × 100
        #   Montant_i = (Consommation_i / Consommation_totale) × Montant_total
        factures_creees = []
        somme_montants = Decimal('0')
        
        for data in locataires_data:
            # Pourcentage de consommation
            pourcentage = (data['consommation'] / total_consommation) * Decimal('100')
            
            # Montant exact (non arrondi)
            montant_exact = (data['consommation'] / total_consommation) * montant_total
            
            # Arrondir au franc CFA
            montant = montant_exact.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
            pourcentage = pourcentage.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            
            somme_montants += montant
            
            data['pourcentage'] = pourcentage
            data['montant'] = montant
            factures_creees.append(data)
        
        # 5. Ajuster le dernier montant pour que la somme = montant_total (gestion des arrondis)
        difference = montant_total - somme_montants
        if difference != 0 and factures_creees:
            # Attribuer la différence au plus gros consommateur
            max_idx = max(range(len(factures_creees)), key=lambda i: factures_creees[i]['consommation'])
            factures_creees[max_idx]['montant'] += difference
        
        # 6. Créer les factures individuelles dans une transaction
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

    @staticmethod
    def simuler_repartition(
        consommations: List[Dict],
        montant_total: Decimal
    ) -> Dict:
        """
        Simule une répartition de facture SANS créer de données
        Utile pour prévisualisation avant validation
        
        Args:
            consommations: Liste de dict avec {'nom': str, 'consommation': Decimal}
            montant_total: Montant total de la facture SODECI/CIE
        
        Returns:
            Dict avec la simulation de répartition
        
        Exemple:
            result = FactureCalculator.simuler_repartition(
                consommations=[
                    {'nom': 'Kouassi Jean', 'consommation': Decimal('15')},
                    {'nom': 'Konan Marie', 'consommation': Decimal('25')},
                    {'nom': 'Yao Pierre', 'consommation': Decimal('10')},
                ],
                montant_total=Decimal('50000')
            )
        """
        if not consommations:
            raise ValueError("La liste des consommations est vide")
        
        # Calculer le total
        total = sum(Decimal(str(c['consommation'])) for c in consommations)
        
        if total == 0:
            raise ValueError("La consommation totale est zéro")
        
        # Calculer les montants
        resultats = []
        somme = Decimal('0')
        
        for c in consommations:
            conso = Decimal(str(c['consommation']))
            pourcentage = (conso / total) * Decimal('100')
            montant = (conso / total) * montant_total
            montant_arrondi = montant.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
            somme += montant_arrondi
            
            resultats.append({
                'nom': c['nom'],
                'consommation': float(conso),
                'pourcentage': float(pourcentage.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
                'montant': float(montant_arrondi)
            })
        
        # Ajuster pour que somme = montant_total
        diff = montant_total - somme
        if diff != 0 and resultats:
            max_idx = max(range(len(resultats)), key=lambda i: resultats[i]['consommation'])
            resultats[max_idx]['montant'] += float(diff)
        
        # Vérification
        somme_finale = sum(r['montant'] for r in resultats)
        
        return {
            'montant_total': float(montant_total),
            'consommation_totale': float(total),
            'nombre_locataires': len(resultats),
            'somme_montants': somme_finale,
            'verification_ok': abs(somme_finale - float(montant_total)) < 0.01,
            'details': resultats
        }

    @staticmethod
    def verifier_facture_collective(facture_collective_id: str) -> Dict:
        """
        Vérifie la cohérence d'une facture collective
        S'assure que la somme des montants individuels = montant total
        """
        try:
            fc = FactureCollective.objects.get(id=facture_collective_id)
        except FactureCollective.DoesNotExist:
            return {'success': False, 'message': 'Facture collective non trouvée'}
        
        # Récupérer les factures individuelles
        factures = Facture.objects.filter(
            type_facture=fc.type_facture,
            mois=fc.mois,
            annee=fc.annee
        )
        
        somme_montants = sum(f.montant for f in factures)
        somme_consommations = sum(f.consommation or Decimal('0') for f in factures)
        
        ecart_montant = abs(fc.montant_total - somme_montants)
        ecart_conso = abs(fc.consommation_totale - somme_consommations)
        
        return {
            'success': True,
            'facture_collective': str(fc.id),
            'type': fc.type_facture,
            'periode': f'{fc.mois}/{fc.annee}',
            'montant_total_declare': float(fc.montant_total),
            'somme_factures_individuelles': float(somme_montants),
            'ecart_montant': float(ecart_montant),
            'consommation_totale_declaree': float(fc.consommation_totale),
            'somme_consommations': float(somme_consommations),
            'ecart_consommation': float(ecart_conso),
            'coherent': ecart_montant < Decimal('1') and ecart_conso < Decimal('0.01'),
            'nombre_factures': factures.count()
        }
