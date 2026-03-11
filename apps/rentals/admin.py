from django.contrib import admin
from .models import Location


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ['numero_contrat', 'locataire', 'maison', 'date_debut', 'date_fin', 'statut']
    list_filter = ['statut', 'date_debut']
    search_fields = ['numero_contrat', 'locataire__nom', 'maison__titre']
