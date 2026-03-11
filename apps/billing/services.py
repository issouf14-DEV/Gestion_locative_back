"""
Services pour le module billing
"""
from decimal import Decimal
from datetime import timedelta
from typing import Dict, Any, Optional, List
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

from .models import Facture
from apps.users.models import User
from apps.notifications.models import Notification


class BillingService:
    """
    Service pour la gestion de la facturation
    """
    
    @staticmethod
    def calculer_dette_locataire(locataire_id: str) -> Dict:
        """
        Calcule la dette totale d'un locataire
        
        Returns:
            Dict avec le détail des dettes par type
        """
        factures_impayees = Facture.objects.filter(
            locataire_id=locataire_id,
            statut='EN_ATTENTE'
        )
        
        dette_loyer = Decimal('0')
        dette_sodeci = Decimal('0')
        dette_cie = Decimal('0')
        dette_autre = Decimal('0')
        
        for facture in factures_impayees:
            if facture.type_facture == 'LOYER':
                dette_loyer += facture.montant
            elif facture.type_facture == 'SODECI':
                dette_sodeci += facture.montant
            elif facture.type_facture == 'CIE':
                dette_cie += facture.montant
            else:
                dette_autre += facture.montant
        
        total = dette_loyer + dette_sodeci + dette_cie + dette_autre
        
        return {
            'dette_loyer': float(dette_loyer),
            'dette_sodeci': float(dette_sodeci),
            'dette_cie': float(dette_cie),
            'dette_autre': float(dette_autre),
            'dette_totale': float(total),
            'nombre_factures_impayees': factures_impayees.count()
        }
    
    @staticmethod
    def marquer_factures_en_retard() -> Dict:
        """
        Marque automatiquement les factures en retard
        Appelée par une tâche Celery quotidienne
        """
        today = timezone.now().date()
        
        factures_en_retard = Facture.objects.filter(
            statut='EN_ATTENTE',
            date_echeance__lt=today
        )
        
        count = factures_en_retard.update(statut='EN_RETARD')
        
        # Mettre à jour le statut des locataires concernés
        locataires_ids = factures_en_retard.values_list('locataire_id', flat=True).distinct()
        User.objects.filter(id__in=locataires_ids).update(statut='EN_RETARD')
        
        return {
            'nombre_factures_marquees': count,
            'nombre_locataires_affectes': len(locataires_ids)
        }
    
    @staticmethod
    def envoyer_rappels_factures() -> Dict:
        """
        Envoie des rappels pour les factures proches de l'échéance ou en retard
        """
        today = timezone.now().date()
        rappel_date = today + timedelta(days=3)  # 3 jours avant échéance
        
        # Factures proches de l'échéance
        factures_a_rappeler = Facture.objects.filter(
            statut='EN_ATTENTE',
            date_echeance__lte=rappel_date,
            date_echeance__gte=today
        ).select_related('locataire')
        
        # Factures en retard
        factures_en_retard = Facture.objects.filter(
            statut='EN_RETARD'
        ).select_related('locataire')
        
        rappels_envoyes = 0
        
        for facture in list(factures_a_rappeler) + list(factures_en_retard):
            BillingService._envoyer_rappel_facture(facture)
            rappels_envoyes += 1
        
        return {
            'rappels_envoyes': rappels_envoyes
        }
    
    @staticmethod
    def _envoyer_rappel_facture(facture: Facture):
        """Envoie un rappel pour une facture spécifique"""
        locataire = facture.locataire
        
        # Créer une notification dans l'application
        Notification.objects.create(
            destinataire=locataire,
            type_notification='RAPPEL',
            titre=f"Rappel - Facture {facture.reference}",
            message=f"Votre facture {facture.get_type_facture_display()} de {facture.montant} FCFA "  # type: ignore[attr-defined]
                   f"est due le {facture.date_echeance.strftime('%d/%m/%Y')}."
        )
        
        # Envoyer un email si les notifications email sont activées
        if hasattr(locataire, 'profile') and locataire.profile.notifications_email:  # type: ignore[union-attr]
            try:
                context = {
                    'locataire': locataire,
                    'facture': facture,
                }
                message = render_to_string('emails/reminder.html', context)
                
                send_mail(
                    subject=f"Rappel - Facture {facture.reference}",
                    message='',
                    html_message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[locataire.email],
                    fail_silently=True
                )
            except Exception:
                pass  # Ne pas bloquer en cas d'erreur email
    
    @staticmethod
    def get_historique_factures(locataire_id: str, mois: int | None = None, annee: int | None = None) -> Any:
        """
        Récupère l'historique des factures d'un locataire
        """
        queryset = Facture.objects.filter(locataire_id=locataire_id)
        
        if mois:
            queryset = queryset.filter(mois=mois)
        if annee:
            queryset = queryset.filter(annee=annee)
        
        return queryset.order_by('-annee', '-mois', '-date_emission')
    
    @staticmethod
    def get_resume_mensuel(mois: int, annee: int) -> Dict:
        """
        Obtient un résumé des factures pour un mois donné
        """
        factures = Facture.objects.filter(mois=mois, annee=annee)
        
        total_loyer = factures.filter(type_facture='LOYER').aggregate(
            total=models.Sum('montant')
        )['total'] or Decimal('0')
        
        total_sodeci = factures.filter(type_facture='SODECI').aggregate(
            total=models.Sum('montant')
        )['total'] or Decimal('0')
        
        total_cie = factures.filter(type_facture='CIE').aggregate(
            total=models.Sum('montant')
        )['total'] or Decimal('0')
        
        payees = factures.filter(statut='PAYEE').count()
        en_attente = factures.filter(statut='EN_ATTENTE').count()
        en_retard = factures.filter(statut='EN_RETARD').count()
        
        return {
            'mois': mois,
            'annee': annee,
            'total_loyer': float(total_loyer),
            'total_sodeci': float(total_sodeci),
            'total_cie': float(total_cie),
            'total_general': float(total_loyer + total_sodeci + total_cie),
            'factures_payees': payees,
            'factures_en_attente': en_attente,
            'factures_en_retard': en_retard,
            'total_factures': payees + en_attente + en_retard
        }


# Import nécessaire pour l'agrégation
from django.db import models
import logging

logger = logging.getLogger(__name__)


class FactureNotificationService:
    """
    Service pour envoyer les notifications de facture
    Supporte: Email, In-App (notifications), WhatsApp
    """
    
    @staticmethod
    def envoyer_facture_email(facture: Facture) -> Dict:
        """
        Envoie une facture par email au locataire
        """
        locataire = facture.locataire
        
        if not locataire.email:
            return {'success': False, 'message': 'Pas d\'email pour ce locataire'}
        
        # Construire le contenu
        subject = f"Facture {facture.type_facture} - {facture.mois}/{facture.annee}"
        
        type_display = getattr(facture, 'get_type_facture_display', lambda: facture.type_facture)()
        
        # Message texte simple
        message = f"""
Bonjour {locataire.prenoms} {locataire.nom},

Votre facture {type_display} pour {facture.mois}/{facture.annee} est disponible.

Montant à payer: {facture.montant:,.0f} FCFA
Date d'échéance: {facture.date_echeance.strftime('%d/%m/%Y')}
"""
        
        if facture.type_facture in ['SODECI', 'CIE']:
            message += f"""
Détails de consommation:
- Index ancien: {facture.index_ancien}
- Index nouveau: {facture.index_nouveau}
- Consommation: {facture.consommation} unités
- Votre part: {facture.pourcentage}%
"""
        
        message += """
Cordialement,
L'équipe de Gestion Locative
"""
        
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[locataire.email],
                fail_silently=False,
            )
            
            logger.info(f"Email facture envoyé à {locataire.email}")
            return {'success': True, 'message': f'Email envoyé à {locataire.email}'}
            
        except Exception as e:
            logger.error(f"Erreur envoi email: {str(e)}")
            return {'success': False, 'message': str(e)}
    
    @staticmethod
    def envoyer_facture_notification_app(facture: Facture) -> Dict:
        """
        Crée une notification in-app pour le locataire
        """
        type_display = getattr(facture, 'get_type_facture_display', lambda: facture.type_facture)()
        
        Notification.objects.create(
            destinataire=facture.locataire,
            type_notification='FACTURE',
            titre=f"Nouvelle facture {type_display}",
            message=f"Montant: {facture.montant:,.0f} FCFA - Échéance: {facture.date_echeance.strftime('%d/%m/%Y')}",
            lien=f"/factures/{facture.id}",
            donnees={
                'facture_id': str(facture.id),
                'type': facture.type_facture,
                'montant': float(facture.montant),
                'echeance': facture.date_echeance.isoformat()
            }
        )
        
        return {'success': True, 'message': 'Notification créée'}
    
    @staticmethod
    def envoyer_facture_whatsapp(facture: Facture) -> Dict:
        """
        Envoie une facture par WhatsApp
        
        FONCTIONNEMENT:
        - Génère un lien WhatsApp Web (wa.me) avec le message pré-rempli
        - L'admin clique sur le lien → WhatsApp Web s'ouvre → il envoie
        - 100% GRATUIT, pas d'inscription pour les locataires
        
        Retourne le lien WhatsApp pour que le frontend puisse l'ouvrir
        """
        locataire = facture.locataire
        
        if not locataire.telephone:
            return {'success': False, 'message': 'Pas de téléphone pour ce locataire'}
        
        # Formater le numéro (ajouter indicatif Côte d'Ivoire si nécessaire)
        phone = locataire.telephone.replace(' ', '').replace('-', '')
        if phone.startswith('0'):
            phone = '225' + phone[1:]  # Côte d'Ivoire
        elif not phone.startswith('+') and not phone.startswith('225'):
            phone = '225' + phone
        phone = phone.replace('+', '')  # wa.me n'utilise pas le +
        
        type_display = getattr(facture, 'get_type_facture_display', lambda: facture.type_facture)()
        
        # Message WhatsApp adapté selon le type de facture
        if facture.type_facture == 'LOYER':
            # Message pour le LOYER
            message = f"""Bonjour {locataire.prenoms},

J'espère que vous allez bien.

Je vous rappelle que le loyer du mois de {facture.mois}/{facture.annee} est dû.

Montant du loyer : {facture.montant:,.0f} FCFA
Date d'échéance : {facture.date_echeance.strftime('%d/%m/%Y')}

Merci de bien vouloir procéder au règlement dans les délais.

Cordialement,
La Gestion Locative"""
        
        elif facture.type_facture in ['SODECI', 'CIE']:
            # Message pour SODECI/CIE - quote-part de la facture collective
            service_nom = 'eau (SODECI)' if facture.type_facture == 'SODECI' else 'électricité (CIE)'
            message = f"""Bonjour {locataire.prenoms},

J'espère que vous allez bien.

La facture {type_display} du mois de {facture.mois}/{facture.annee} est arrivée. Voici votre quote-part à régler :

Montant de votre part : {facture.montant:,.0f} FCFA
Date d'échéance : {facture.date_echeance.strftime('%d/%m/%Y')}

Détail de votre consommation d'{service_nom} :
- Ancien index : {facture.index_ancien}
- Nouveau index : {facture.index_nouveau}
- Consommation : {facture.consommation} unités
- Votre part : {facture.pourcentage}%

Merci de bien vouloir procéder au règlement avant la date d'échéance.

Cordialement,
La Gestion Locative"""
        
        else:
            # Message générique pour autres types (charges, etc.)
            message = f"""Bonjour {locataire.prenoms},

J'espère que vous allez bien.

Veuillez trouver ci-dessous les détails de votre facture {type_display} :

Montant à payer : {facture.montant:,.0f} FCFA
Période : {facture.mois}/{facture.annee}
Date d'échéance : {facture.date_echeance.strftime('%d/%m/%Y')}

Merci de bien vouloir procéder au règlement avant la date d'échéance.

Cordialement,
La Gestion Locative"""
        
        # Encoder le message pour l'URL
        import urllib.parse
        encoded_message = urllib.parse.quote(message)
        
        # Générer le lien WhatsApp Web
        whatsapp_link = f"https://wa.me/{phone}?text={encoded_message}"
        
        logger.info(f"Lien WhatsApp généré pour {locataire.get_full_name()}: {phone}")
        
        return {
            'success': True,
            'message': f'Lien WhatsApp généré pour {locataire.get_full_name()}',
            'whatsapp_link': whatsapp_link,
            'phone': phone,
            'locataire': locataire.get_full_name()
        }
    
    @staticmethod
    def generer_liens_whatsapp_mois(mois: int, annee: int, type_facture: Optional[str] = None) -> Dict:
        """
        Génère les liens WhatsApp pour toutes les factures d'un mois
        L'admin peut ensuite ouvrir chaque lien pour envoyer
        """
        queryset = Facture.objects.filter(mois=mois, annee=annee, statut='EN_ATTENTE')
        
        if type_facture:
            queryset = queryset.filter(type_facture=type_facture)
        
        liens = []
        for facture in queryset.select_related('locataire'):
            result = FactureNotificationService.envoyer_facture_whatsapp(facture)
            if result.get('success'):
                liens.append({
                    'facture_id': str(facture.id),
                    'locataire': result['locataire'],
                    'phone': result['phone'],
                    'montant': float(facture.montant),
                    'whatsapp_link': result['whatsapp_link']
                })
        
        return {
            'success': True,
            'periode': f'{mois}/{annee}',
            'nombre_factures': len(liens),
            'liens': liens
        }
    
    @classmethod
    def envoyer_facture_tous_canaux(cls, facture: Facture, canaux: Optional[List[str]] = None) -> Dict:
        """
        Envoie une facture sur plusieurs canaux
        
        Args:
            facture: La facture à envoyer
            canaux: Liste de canaux ['email', 'app', 'whatsapp'] - email+app par défaut
        """
        if canaux is None:
            canaux = ['email', 'app']
        
        resultats = {}
        
        if 'email' in canaux:
            resultats['email'] = cls.envoyer_facture_email(facture)
        
        if 'app' in canaux:
            resultats['app'] = cls.envoyer_facture_notification_app(facture)
        
        if 'whatsapp' in canaux:
            resultats['whatsapp'] = cls.envoyer_facture_whatsapp(facture)
        
        return {
            'facture_id': str(facture.id),
            'locataire': facture.locataire.get_full_name(),
            'resultats': resultats
        }
    
    @classmethod
    def envoyer_toutes_factures_mois(cls, mois: int, annee: int, type_facture: Optional[str] = None, canaux: Optional[List[str]] = None) -> Dict:
        """
        Envoie toutes les factures d'un mois aux locataires
        """
        queryset = Facture.objects.filter(mois=mois, annee=annee, statut='EN_ATTENTE')
        
        if type_facture:
            queryset = queryset.filter(type_facture=type_facture)
        
        resultats = []
        for facture in queryset:
            result = cls.envoyer_facture_tous_canaux(facture, canaux)
            resultats.append(result)
        
        return {
            'success': True,
            'periode': f'{mois}/{annee}',
            'nombre_envois': len(resultats),
            'details': resultats
        }


class CompteurService:
    """
    Service pour gérer les compteurs et leur association aux locataires
    """
    
    @staticmethod
    def assigner_compteur_locataire(compteur_id: str, locataire_id: str) -> Dict:
        """
        Assigne un compteur à un locataire
        """
        from .models import Compteur
        
        try:
            compteur = Compteur.objects.get(id=compteur_id)
            locataire = User.objects.get(id=locataire_id)
            
            compteur.locataire_actuel = locataire
            compteur.statut = 'ACTIF'
            compteur.save()
            
            return {
                'success': True,
                'message': f'Compteur {compteur.numero} assigné à {locataire.get_full_name()}'
            }
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    @staticmethod
    def liberer_compteur(compteur_id: str) -> Dict:
        """
        Libère un compteur (quand le locataire part)
        """
        from .models import Compteur
        
        try:
            compteur = Compteur.objects.get(id=compteur_id)
            ancien_locataire = compteur.locataire_actuel
            
            compteur.locataire_actuel = None
            compteur.statut = 'INACTIF'
            compteur.save()
            
            return {
                'success': True,
                'message': f'Compteur {compteur.numero} libéré',
                'ancien_locataire': ancien_locataire.get_full_name() if ancien_locataire else None
            }
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    @staticmethod
    def lister_compteurs_locataire(locataire_id: str) -> list:
        """
        Liste les compteurs utilisés par un locataire
        """
        from .models import Compteur
        
        compteurs = Compteur.objects.filter(locataire_actuel_id=locataire_id, statut='ACTIF')
        
        return [
            {
                'id': str(c.id),
                'numero': c.numero,
                'type': c.type_compteur,
                'type_display': getattr(c, 'get_type_compteur_display', lambda: c.type_compteur)(),
                'dernier_index': float(c.dernier_index),
                'maison': c.maison.titre if c.maison else None
            }
            for c in compteurs
        ]
    
    @staticmethod
    def lister_compteurs_maison(maison_id: str) -> list:
        """
        Liste les compteurs d'une maison
        """
        from .models import Compteur
        
        compteurs = Compteur.objects.filter(maison_id=maison_id)
        
        return [
            {
                'id': str(c.id),
                'numero': c.numero,
                'type': c.type_compteur,
                'type_display': getattr(c, 'get_type_compteur_display', lambda: c.type_compteur)(),
                'statut': c.statut,
                'locataire': c.locataire_actuel.get_full_name() if c.locataire_actuel else None,
                'dernier_index': float(c.dernier_index)
            }
            for c in compteurs
        ]


class RappelLoyerService:
    """
    Service pour envoyer des rappels de loyer aux locataires
    Via WhatsApp et Email
    """
    
    @staticmethod
    def generer_message_loyer(locataire, montant: Decimal, mois: int, annee: int, date_echeance=None) -> str:
        """
        Génère un message courtois pour le rappel de loyer
        """
        # Nom du mois en français
        mois_noms = {
            1: 'janvier', 2: 'février', 3: 'mars', 4: 'avril',
            5: 'mai', 6: 'juin', 7: 'juillet', 8: 'août',
            9: 'septembre', 10: 'octobre', 11: 'novembre', 12: 'décembre'
        }
        mois_nom = mois_noms.get(mois, str(mois))
        
        # Date d'échéance par défaut : 5 du mois
        if date_echeance:
            echeance_str = date_echeance.strftime('%d/%m/%Y')
        else:
            echeance_str = f"05/{mois:02d}/{annee}"
        
        message = f"""Bonjour {locataire.prenoms},

J'espère que vous vous portez bien.

Je me permets de vous rappeler que le loyer du mois de {mois_nom} {annee} est dû.

Montant du loyer : {montant:,.0f} FCFA
Date d'échéance : {echeance_str}

Je vous remercie de bien vouloir procéder au règlement dans les meilleurs délais.

Pour toute question, n'hésitez pas à me contacter.

Cordialement,
La Gestion Locative"""
        
        return message
    
    @staticmethod
    def envoyer_rappel_whatsapp(
        locataire_id: str,
        montant: Decimal,
        mois: int,
        annee: int,
        date_echeance=None
    ) -> Dict:
        """
        Génère le lien WhatsApp pour envoyer un rappel de loyer
        L'admin clique sur le lien → WhatsApp s'ouvre avec le message prêt
        """
        import urllib.parse
        
        locataire = User.objects.get(id=locataire_id)
        
        if not locataire.telephone:
            return {'success': False, 'message': 'Pas de téléphone pour ce locataire'}
        
        # Formater le numéro
        phone = locataire.telephone.replace(' ', '').replace('-', '')
        if phone.startswith('0'):
            phone = '225' + phone[1:]
        elif not phone.startswith('+') and not phone.startswith('225'):
            phone = '225' + phone
        phone = phone.replace('+', '')
        
        # Générer le message
        message = RappelLoyerService.generer_message_loyer(
            locataire, montant, mois, annee, date_echeance
        )
        
        # Encoder pour URL
        encoded_message = urllib.parse.quote(message)
        whatsapp_link = f"https://wa.me/{phone}?text={encoded_message}"
        
        return {
            'success': True,
            'whatsapp_link': whatsapp_link,
            'phone': phone,
            'locataire': locataire.get_full_name(),
            'montant': float(montant),
            'mois': mois,
            'annee': annee,
            'message': f'Lien WhatsApp généré pour {locataire.get_full_name()}'
        }
    
    @staticmethod
    def envoyer_rappel_email(
        locataire_id: str,
        montant: Decimal,
        mois: int,
        annee: int,
        date_echeance=None
    ) -> Dict:
        """
        Envoie un rappel de loyer par email
        """
        locataire = User.objects.get(id=locataire_id)
        
        if not locataire.email:
            return {'success': False, 'message': 'Pas d\'email pour ce locataire'}
        
        # Générer le message
        message = RappelLoyerService.generer_message_loyer(
            locataire, montant, mois, annee, date_echeance
        )
        
        # Nom du mois
        mois_noms = {
            1: 'janvier', 2: 'février', 3: 'mars', 4: 'avril',
            5: 'mai', 6: 'juin', 7: 'juillet', 8: 'août',
            9: 'septembre', 10: 'octobre', 11: 'novembre', 12: 'décembre'
        }
        mois_nom = mois_noms.get(mois, str(mois))
        
        subject = f"Rappel de loyer - {mois_nom.capitalize()} {annee}"
        
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[locataire.email],
                fail_silently=False,
            )
            
            logger.info(f"Email rappel loyer envoyé à {locataire.email}")
            return {
                'success': True,
                'email': locataire.email,
                'locataire': locataire.get_full_name(),
                'message': f'Email envoyé à {locataire.email}'
            }
            
        except Exception as e:
            logger.error(f"Erreur envoi email: {str(e)}")
            return {'success': False, 'message': str(e)}
    
    @staticmethod
    def envoyer_rappel_tous_canaux(
        locataire_id: str,
        montant: Decimal,
        mois: int,
        annee: int,
        date_echeance=None,
        canaux: Optional[List[str]] = None
    ) -> Dict:
        """
        Envoie le rappel sur plusieurs canaux (email et/ou whatsapp)
        """
        if canaux is None:
            canaux = ['email', 'whatsapp']
        
        resultats = {}
        
        if 'email' in canaux:
            resultats['email'] = RappelLoyerService.envoyer_rappel_email(
                locataire_id, montant, mois, annee, date_echeance
            )
        
        if 'whatsapp' in canaux:
            resultats['whatsapp'] = RappelLoyerService.envoyer_rappel_whatsapp(
                locataire_id, montant, mois, annee, date_echeance
            )
        
        locataire = User.objects.get(id=locataire_id)
        
        return {
            'success': True,
            'locataire': locataire.get_full_name(),
            'montant': float(montant),
            'mois': mois,
            'annee': annee,
            'resultats': resultats
        }
    
    @staticmethod
    def envoyer_rappels_tous_locataires(
        mois: int,
        annee: int,
        canaux: Optional[List[str]] = None
    ) -> Dict:
        """
        Envoie des rappels de loyer à tous les locataires avec des factures impayées
        """
        from apps.rentals.models import Location
        
        # Récupérer tous les contrats actifs
        locations = Location.objects.filter(
            statut='ACTIVE'
        ).select_related('locataire')
        
        rappels = []
        
        for location in locations:
            # Vérifier si le loyer est impayé
            facture_impayee = Facture.objects.filter(
                locataire=location.locataire,
                type_facture='LOYER',
                mois=mois,
                annee=annee,
                statut__in=['EN_ATTENTE', 'EN_RETARD']
            ).first()
            
            if facture_impayee:
                result = RappelLoyerService.envoyer_rappel_tous_canaux(
                    locataire_id=str(location.locataire.id),
                    montant=location.loyer_mensuel,
                    mois=mois,
                    annee=annee,
                    canaux=canaux
                )
                rappels.append(result)
        
        return {
            'success': True,
            'mois': mois,
            'annee': annee,
            'nombre_rappels': len(rappels),
            'rappels': rappels
        }
    
    @staticmethod
    def generer_liens_whatsapp_loyers(mois: int, annee: int) -> Dict:
        """
        Génère les liens WhatsApp pour tous les loyers impayés du mois
        Retourne une liste de liens que l'admin peut ouvrir un par un
        """
        # Factures de loyer impayées
        factures = Facture.objects.filter(
            type_facture='LOYER',
            mois=mois,
            annee=annee,
            statut__in=['EN_ATTENTE', 'EN_RETARD']
        ).select_related('locataire')
        
        liens = []
        
        for facture in factures:
            result = RappelLoyerService.envoyer_rappel_whatsapp(
                locataire_id=str(facture.locataire.id),
                montant=facture.montant,
                mois=mois,
                annee=annee,
                date_echeance=facture.date_echeance
            )
            
            if result.get('success'):
                liens.append({
                    'locataire': result['locataire'],
                    'phone': result['phone'],
                    'montant': result['montant'],
                    'whatsapp_link': result['whatsapp_link']
                })
        
        return {
            'success': True,
            'mois': mois,
            'annee': annee,
            'nombre_locataires': len(liens),
            'liens': liens
        }