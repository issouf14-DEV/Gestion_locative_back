"""
Configuration admin pour le module billing
"""
from django.contrib import admin
from .models import Facture, IndexCompteur, FactureCollective


@admin.register(Facture)
class FactureAdmin(admin.ModelAdmin):
    list_display = ['reference', 'locataire', 'type_facture', 'montant', 'mois', 'annee', 'statut']
    list_filter = ['type_facture', 'statut', 'mois', 'annee']
    search_fields = ['reference', 'locataire__nom', 'locataire__prenoms']


@admin.register(IndexCompteur)
class IndexCompteurAdmin(admin.ModelAdmin):
    list_display = ['locataire', 'type_compteur', 'index_valeur', 'mois', 'annee']
    list_filter = ['type_compteur', 'mois', 'annee']


@admin.register(FactureCollective)
class FactureCollectiveAdmin(admin.ModelAdmin):
    list_display = ['type_facture', 'montant_total', 'mois', 'annee', 'repartie']
    list_filter = ['type_facture', 'repartie', 'mois', 'annee']
