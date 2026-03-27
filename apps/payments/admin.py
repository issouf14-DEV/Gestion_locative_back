from django.contrib import admin
from .models import Paiement


@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    list_display = ['reference', 'locataire', 'montant', 'statut', 'created_at', 'date_validation']
    list_filter = ['statut', 'created_at']
    search_fields = ['reference', 'locataire__nom']
