from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['titre', 'destinataire', 'type_notification', 'lu', 'created_at']
    list_filter = ['type_notification', 'lu', 'created_at']
    search_fields = ['titre', 'message', 'destinataire__nom']
