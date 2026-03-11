"""
Configuration admin pour le module users
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, Profile


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Configuration admin pour User"""
    
    list_display = ['email', 'nom', 'prenoms', 'role', 'statut', 'is_active', 'date_joined']
    list_filter = ['role', 'statut', 'is_active', 'is_staff', 'date_joined']
    search_fields = ['email', 'nom', 'prenoms', 'telephone']
    ordering = ['-date_joined']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Informations personnelles'), {
            'fields': ('nom', 'prenoms', 'telephone', 'photo', 'adresse')
        }),
        (_('Permissions'), {
            'fields': ('role', 'statut', 'is_active', 'is_staff', 'is_superuser', 
                      'email_verified', 'groups', 'user_permissions')
        }),
        (_('Dates'), {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'nom', 'prenoms', 'telephone', 
                      'password1', 'password2', 'role'),
        }),
    )
    
    readonly_fields = ['date_joined', 'last_login']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('profile')


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """Configuration admin pour Profile"""
    
    list_display = ['user', 'profession', 'employeur', 'notifications_email']
    search_fields = ['user__email', 'user__nom', 'user__prenoms', 'profession']
    list_filter = ['notifications_email', 'notifications_sms']
    
    fieldsets = (
        (_('Utilisateur'), {'fields': ('user',)}),
        (_('Informations professionnelles'), {
            'fields': ('profession', 'employeur')
        }),
        (_('Contact d\'urgence'), {
            'fields': ('contact_urgence_nom', 'contact_urgence_telephone', 
                      'contact_urgence_relation')
        }),
        (_('Préférences'), {
            'fields': ('notifications_email', 'notifications_sms')
        }),
        (_('Documents'), {'fields': ('piece_identite',)}),
    )
