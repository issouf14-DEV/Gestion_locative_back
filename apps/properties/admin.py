"""
Configuration admin pour le module properties
"""
from django.contrib import admin
from .models import Maison, ImageMaison


class ImageMaisonInline(admin.TabularInline):
    """Inline pour les images de maison"""
    model = ImageMaison
    extra = 1
    fields = ['image', 'legende', 'est_principale', 'ordre']


@admin.register(Maison)
class MaisonAdmin(admin.ModelAdmin):
    """Configuration admin pour Maison"""
    
    list_display = [
        'reference', 'titre', 'type_logement', 'prix',
        'ville', 'commune', 'statut', 'nombre_vues', 'created_at'
    ]
    list_filter = [
        'statut', 'type_logement', 'ville', 'commune',
        'meublee', 'charges_incluses', 'created_at'
    ]
    search_fields = ['titre', 'reference', 'description', 'adresse', 'quartier']
    readonly_fields = ['reference', 'nombre_vues', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('reference', 'titre', 'description', 'type_logement', 'statut')
        }),
        ('Prix et charges', {
            'fields': ('prix', 'caution', 'charges_incluses')
        }),
        ('Localisation', {
            'fields': ('adresse', 'ville', 'commune', 'quartier', 'latitude', 'longitude')
        }),
        ('Caractéristiques', {
            'fields': (
                'nombre_chambres', 'nombre_salles_bain', 'nombre_toilettes',
                'superficie', 'meublee', 'animaux_acceptes'
            )
        }),
        ('Équipements et commodités', {
            'fields': ('equipements', 'commodites'),
            'classes': ('collapse',)
        }),
        ('Statistiques', {
            'fields': ('nombre_vues', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [ImageMaisonInline]
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('images')


@admin.register(ImageMaison)
class ImageMaisonAdmin(admin.ModelAdmin):
    """Configuration admin pour ImageMaison"""
    
    list_display = ['maison', 'legende', 'est_principale', 'ordre', 'created_at']
    list_filter = ['est_principale', 'created_at']
    search_fields = ['maison__titre', 'legende']
    ordering = ['-est_principale', 'ordre']
