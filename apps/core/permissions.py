"""
Permissions personnalisées
"""
from rest_framework import permissions


class IsAdminUser(permissions.BasePermission):
    """
    Permission pour vérifier si l'utilisateur est administrateur
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'ADMIN'
    
    def has_object_permission(self, request, view, obj):
        return request.user and request.user.is_authenticated and request.user.role == 'ADMIN'


class IsLocataireOrAdmin(permissions.BasePermission):
    """
    Permission pour vérifier si l'utilisateur est locataire ou admin
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permission pour vérifier si l'utilisateur est propriétaire de l'objet ou admin
    """
    def has_permission(self, request, view):
        # Autoriser l'accès au niveau vue, vérifier au niveau objet
        return request.user and request.user.is_authenticated
        
    def has_object_permission(self, request, view, obj):
        if request.user.role == 'ADMIN':
            return True
        
        # Si l'objet est un User et c'est l'utilisateur lui-même
        if hasattr(obj, 'pk') and obj.pk == request.user.pk:
            return True
        
        # Vérifier si l'objet a un attribut user
        if hasattr(obj, 'user') and obj.user_id == request.user.pk:
            return True
        
        # Vérifier si l'objet a un attribut locataire
        if hasattr(obj, 'locataire') and obj.locataire_id == request.user.pk:
            return True
        
        return False


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Les admins peuvent tout faire, les autres seulement lire
    """
    def has_permission(self, request, view):
        # Lecture autorisée pour tous
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Écriture uniquement pour les admins
        return request.user and request.user.is_authenticated and request.user.role == 'ADMIN'
