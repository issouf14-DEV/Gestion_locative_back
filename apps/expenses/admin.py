from django.contrib import admin
from .models import Depense


@admin.register(Depense)
class DepenseAdmin(admin.ModelAdmin):
    list_display = ['categorie', 'description', 'montant', 'date_depense', 'maison']
    list_filter = ['categorie', 'date_depense']
    search_fields = ['description', 'maison__titre']
