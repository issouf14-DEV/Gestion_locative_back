"""
Script de test pour les calculs SODECI
"""
import os
import sys

# Ajouter le chemin du projet
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

import django
django.setup()

from decimal import Decimal
from apps.billing.calculators import FactureCalculator

print("=" * 60)
print("TEST DES FORMULES DE CALCUL SODECI")
print("=" * 60)

# Test 1: Cas simple
print("\n--- TEST 1: Cas simple ---")
result = FactureCalculator.simuler_repartition(
    consommations=[
        {'nom': 'Kouassi Jean', 'consommation': Decimal('15')},
        {'nom': 'Konan Marie', 'consommation': Decimal('25')},
        {'nom': 'Yao Pierre', 'consommation': Decimal('10')},
    ],
    montant_total=Decimal('50000')
)

print(f"Montant total facture: {result['montant_total']:,.0f} FCFA")
print(f"Consommation totale: {result['consommation_totale']} m3")
print(f"\nRepartition:")
for d in result['details']:
    print(f"  {d['nom']}: {d['consommation']} m3 ({d['pourcentage']:.2f}%) => {d['montant']:,.0f} FCFA")
print(f"\nSomme des montants: {result['somme_montants']:,.0f} FCFA")
print(f"Verification: {'OK' if result['verification_ok'] else 'ERREUR'}")

# Test 2: Cas avec arrondi difficile
print("\n--- TEST 2: Cas avec arrondi ---")
result2 = FactureCalculator.simuler_repartition(
    consommations=[
        {'nom': 'Locataire A', 'consommation': Decimal('17')},
        {'nom': 'Locataire B', 'consommation': Decimal('23')},
        {'nom': 'Locataire C', 'consommation': Decimal('13')},
    ],
    montant_total=Decimal('100000')
)

print(f"Montant total facture: {result2['montant_total']:,.0f} FCFA")
print(f"Consommation totale: {result2['consommation_totale']} m3")
print(f"\nRepartition:")
for d in result2['details']:
    print(f"  {d['nom']}: {d['consommation']} m3 ({d['pourcentage']:.2f}%) => {d['montant']:,.0f} FCFA")
print(f"\nSomme des montants: {result2['somme_montants']:,.0f} FCFA")
print(f"Verification: {'OK' if result2['verification_ok'] else 'ERREUR'}")

# Test 3: Verification formule
print("\n--- FORMULES UTILISEES ---")
print("""
SODECI/CIE - Repartition proportionnelle:
=========================================
1. Consommation_i = Index_nouveau - Index_ancien
2. Consommation_totale = Sum(Consommation_i)
3. Pourcentage_i = (Consommation_i / Consommation_totale) x 100
4. Montant_i = (Consommation_i / Consommation_totale) x Montant_facture

Note: Les arrondis sont geres pour que Sum(Montant_i) = Montant_facture
""")

print("=" * 60)
print("TESTS TERMINES")
print("=" * 60)
