from django.contrib import admin
from .models import Reservation


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ['reference', 'user', 'maison', 'date_debut_souhaitee', 'statut', 'created_at']
    list_filter = ['statut', 'created_at']
    search_fields = ['reference', 'user__nom', 'maison__titre']
