"""
Filtres pour le module properties
"""
import django_filters
from .models import Maison


class MaisonFilter(django_filters.FilterSet):
    """
    Filtres avancés pour les maisons
    """
    prix_min = django_filters.NumberFilter(field_name='prix', lookup_expr='gte')
    prix_max = django_filters.NumberFilter(field_name='prix', lookup_expr='lte')
    
    ville = django_filters.CharFilter(lookup_expr='iexact')
    commune = django_filters.CharFilter(lookup_expr='icontains')
    quartier = django_filters.CharFilter(lookup_expr='icontains')
    
    nombre_chambres = django_filters.NumberFilter()
    nombre_chambres_min = django_filters.NumberFilter(
        field_name='nombre_chambres',
        lookup_expr='gte'
    )
    
    superficie_min = django_filters.NumberFilter(
        field_name='superficie',
        lookup_expr='gte'
    )
    superficie_max = django_filters.NumberFilter(
        field_name='superficie',
        lookup_expr='lte'
    )
    
    type_logement = django_filters.ChoiceFilter(choices=Maison.TYPE_CHOICES)
    statut = django_filters.ChoiceFilter(choices=Maison.STATUT_CHOICES)
    meublee = django_filters.BooleanFilter()
    animaux_acceptes = django_filters.BooleanFilter()
    charges_incluses = django_filters.BooleanFilter()
    
    class Meta:
        model = Maison
        fields = [
            'type_logement', 'statut', 'ville', 'commune',
            'quartier', 'meublee', 'animaux_acceptes',
            'charges_incluses'
        ]
