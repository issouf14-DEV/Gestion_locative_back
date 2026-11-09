"""
Activité de démonstration : locataires, locations, factures, paiements,
compteurs, dépenses, réservations et notifications.

Tout est repérable pour pouvoir être supprimé :
- locataires de démo : email en @demo.gestion-locative.ci
- factures, paiements, compteurs : référence / numéro « DEMO-… »
- notifications : metadata {"demo": true}
- locations, dépenses, réservations : liées aux maisons « DEMO-… » (suppression en cascade)
"""
import io
import os
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.utils import timezone

from apps.billing.models import Compteur, Facture, IndexCompteur
from apps.expenses.models import Depense
from apps.notifications.models import Notification
from apps.payments.models import Paiement
from apps.properties.models import Maison
from apps.rentals.models import Location
from apps.reservations.models import Reservation

DOMAINE = '@demo.gestion-locative.ci'
User = get_user_model()

# prénoms, nom, référence de la maison louée, statut du locataire
LOCATAIRES = [
    ('Aya', 'Kouassi', 'DEMO-004', 'A_JOUR'),
    ('Seydou', 'Bamba', 'DEMO-005', 'EN_RETARD'),
    ('Mariam', 'Traoré', 'DEMO-007', 'A_JOUR'),
    ('Yao', 'Konan', 'DEMO-008', 'A_JOUR'),
    ('Fatou', 'Diabaté', 'DEMO-010', 'A_JOUR'),
]
MAISON_COMPTE_REEL = 'DEMO-003'  # Appartement F3 Zone 4


def _mois_recents(nombre=4):
    """Les `nombre` derniers mois, du plus ancien au mois courant."""
    aujourd_hui = date.today()
    mois, annee, resultat = aujourd_hui.month, aujourd_hui.year, []
    for _ in range(nombre):
        resultat.append((mois, annee))
        mois, annee = (12, annee - 1) if mois == 1 else (mois - 1, annee)
    return list(reversed(resultat))


def _recu_png(texte):
    """Petite image de reçu de paiement (Pillow)."""
    from PIL import Image, ImageDraw
    image = Image.new('RGB', (600, 340), 'white')
    dessin = ImageDraw.Draw(image)
    dessin.rectangle([10, 10, 590, 330], outline='#1e3a5f', width=4)
    dessin.text((40, 40), 'RECU DE PAIEMENT - MOBILE MONEY', fill='#1e3a5f')
    for i, ligne in enumerate(texte.split('\n')):
        dessin.text((40, 100 + i * 30), ligne, fill='black')
    tampon = io.BytesIO()
    image.save(tampon, format='PNG')
    return ContentFile(tampon.getvalue())


class Activite:
    def __init__(self, sortie):
        self.out = sortie
        self.n_facture = 0
        self.n_paiement = 0
        self.preuve = None
        self.admins = list(User.objects.filter(is_superuser=True))
        self.mois = _mois_recents()

    # ------------------------------------------------------------------ création
    def creer(self):
        if User.objects.filter(email__endswith=DOMAINE).exists():
            self.out('Activité de démo déjà présente : rien à faire.')
            return
        maisons = {m.reference: m for m in Maison.objects.filter(reference__startswith='DEMO-')}
        if not maisons:
            self.out('Aucune maison de démo : activité ignorée.')
            return
        mot_de_passe = os.environ.get('DEMO_ADMIN_PASSWORD') or None

        locataires = []
        for i, (prenoms, nom, ref, statut) in enumerate(LOCATAIRES):
            email = f"{prenoms.lower()}.{nom.lower().replace('é', 'e')}{DOMAINE}"
            user = User.objects.create_user(
                email=email, nom=nom, prenoms=prenoms, telephone=f'+225 07 00 00 00 {i + 10}',
                password=mot_de_passe, role='LOCATAIRE', statut=statut, email_verified=True,
            )
            locataires.append((user, maisons[ref]))
        compte_reel = self._compte_reel()
        if compte_reel:
            locataires.append((compte_reel, maisons[MAISON_COMPTE_REEL]))

        for numero, (user, maison) in enumerate(locataires):
            self._location(user, maison, numero)
        self._depenses(maisons)
        self._reservations(maisons, [u for u, _ in locataires])
        self._notifications_admins()
        self.out(f'Activité de démo créée : {len(locataires)} locataires, '
                 f'{self.n_facture} factures, {self.n_paiement} paiements.')

    def _compte_reel(self):
        email = os.environ.get('DEMO_LOCATAIRE_EMAIL', '').strip()
        if not email:
            return None
        user = User.objects.filter(email__iexact=email, role='LOCATAIRE').first()
        if not user or Location.objects.filter(locataire=user, statut='ACTIVE').exists():
            self.out(f'Compte {email} ignoré (introuvable, pas locataire ou déjà en location).')
            return None
        return user

    def _location(self, user, maison, numero):
        debut = date(self.mois[0][1], self.mois[0][0], 1)
        Location.objects.create(
            locataire=user, maison=maison, date_debut=debut, date_fin=debut + timedelta(days=365),
            duree_mois=12, loyer_mensuel=maison.prix, caution_versee=maison.caution, statut='ACTIVE',
            notes='Contrat de démonstration.',
        )
        maison.statut = 'LOUEE'
        maison.save(update_fields=['statut'])

        index = {'SODECI': Decimal(120 + 15 * numero), 'CIE': Decimal(2400 + 140 * numero)}
        compteurs = {
            t: Compteur.objects.create(
                numero=f'DEMO-{t[:3]}-{maison.reference[-3:]}', type_compteur=t, maison=maison,
                locataire_actuel=user, dernier_index=index[t],
            ) for t in ('SODECI', 'CIE')
        }
        en_retard = user.statut == 'EN_RETARD'
        for rang, (mois, annee) in enumerate(self.mois):
            courant = rang == len(self.mois) - 1
            echeance = date(annee, mois, 10)
            factures = [self._facture(user, 'LOYER', maison.prix, mois, annee, echeance)]
            for t, prix_unitaire, conso in (('SODECI', 450, 12 + (rang + numero) % 9),
                                            ('CIE', 95, 150 + 20 * ((rang + numero) % 6))):
                ancien, nouveau = index[t], index[t] + conso
                index[t] = nouveau
                IndexCompteur.objects.create(compteur=compteurs[t], locataire=user, type_compteur=t,
                                             index_valeur=nouveau, mois=mois, annee=annee)
                factures.append(self._facture(user, t, Decimal(conso * prix_unitaire), mois, annee,
                                              echeance, ancien, nouveau))
            if courant:
                if user.email.startswith('aya.'):
                    self._payer(user, factures[:1], echeance)
                if user.email.startswith('mariam.'):
                    self._paiement(user, factures, 'EN_ATTENTE', echeance)
            elif en_retard and rang == len(self.mois) - 2:
                Facture.objects.filter(id__in=[f.id for f in factures]).update(statut='EN_RETARD')
            else:
                self._payer(user, factures, echeance)
        for t, compteur in compteurs.items():
            compteur.dernier_index = index[t]
            compteur.date_dernier_releve = date.today()
            compteur.save(update_fields=['dernier_index', 'date_dernier_releve'])
        self._notifications_locataire(user, maison, en_retard)

    def _facture(self, user, type_f, montant, mois, annee, echeance, ancien=None, nouveau=None):
        self.n_facture += 1
        return Facture.objects.create(
            reference=f'DEMO-{type_f[:3]}-{self.n_facture:04d}', locataire=user, type_facture=type_f,
            montant=montant, index_ancien=ancien, index_nouveau=nouveau, mois=mois, annee=annee,
            date_echeance=echeance, statut='EN_ATTENTE',
        )

    def _payer(self, user, factures, echeance):
        paye_le = echeance - timedelta(days=3)
        Facture.objects.filter(id__in=[f.id for f in factures]).update(statut='PAYEE', date_paiement=paye_le)
        self._paiement(user, factures, 'VALIDE', echeance)

    def _paiement(self, user, factures, statut, echeance):
        self.n_paiement += 1
        total = sum(f.montant for f in factures)
        paiement = Paiement(
            reference=f'DEMO-PAY-{self.n_paiement:04d}', locataire=user, montant=total,
            factures_ids=[str(f.id) for f in factures], statut=statut,
            notes_locataire='Paiement par Orange Money.',
        )
        if statut == 'VALIDE' and self.admins:
            paiement.validateur = self.admins[0]
            paiement.date_validation = timezone.now()
            paiement.commentaire_admin = 'Paiement vérifié, merci.'
        if self.preuve:  # une seule image partagée par tous les paiements de démo
            paiement.preuve.name = self.preuve
            paiement.save()
        else:
            texte = f'Montant : {total:,.0f} FCFA\nOperateur : Orange Money\nReference : DEMO'
            paiement.preuve.save('demo-recu.png', _recu_png(texte), save=True)
            self.preuve = paiement.preuve.name

    def _depenses(self, maisons):
        lignes = [
            ('DEMO-004', 'REPARATION', 'Réparation de la pompe à eau', 85000, 70),
            ('DEMO-005', 'MAINTENANCE', 'Entretien des climatiseurs', 60000, 50),
            ('DEMO-007', 'AMENAGEMENT', 'Pose de nouveaux placards', 150000, 40),
            ('DEMO-008', 'TAXE', 'Impôt foncier', 120000, 30),
            ('DEMO-010', 'ASSURANCE', 'Assurance habitation annuelle', 95000, 25),
            ('DEMO-003', 'REPARATION', 'Remplacement du chauffe-eau', 110000, 15),
            ('DEMO-001', 'MAINTENANCE', 'Nettoyage de la piscine', 45000, 8),
            ('DEMO-006', 'AUTRE', 'Frais de gardiennage', 70000, 3),
        ]
        for ref, categorie, description, montant, jours in lignes:
            Depense.objects.create(maison=maisons[ref], categorie=categorie, description=description,
                                   montant=Decimal(montant), date_depense=date.today() - timedelta(days=jours))

    def _reservations(self, maisons, users):
        lignes = [
            ('DEMO-001', 0, 'EN_ATTENTE', 'Bonjour, je souhaite visiter la villa ce week-end.'),
            ('DEMO-002', 2, 'EN_ATTENTE', 'Le duplex est-il toujours disponible ?'),
            ('DEMO-009', 3, 'ACCEPTEE', 'Je suis intéressé pour 12 mois.'),
            ('DEMO-012', 4, 'REFUSEE', 'Possible de baisser le loyer ?'),
        ]
        for ref, idx, statut, message in lignes:
            Reservation.objects.create(
                user=users[idx % len(users)], maison=maisons[ref], date_debut_souhaitee=date.today() + timedelta(days=30),
                duree_mois=12, message=message, statut=statut,
                reponse_admin='' if statut == 'EN_ATTENTE' else ('Visite confirmée.' if statut == 'ACCEPTEE' else 'Le prix est ferme.'),
                date_reponse=None if statut == 'EN_ATTENTE' else timezone.now(),
            )

    def _notif(self, user, type_n, titre, message, lu=False):
        Notification.objects.create(destinataire=user, type_notification=type_n, titre=titre,
                                    message=message, lu=lu, metadata={'demo': True})

    def _notifications_locataire(self, user, maison, en_retard):
        self._notif(user, 'LOCATION', 'Bienvenue dans votre logement', f'Votre location « {maison.titre} » est active.', lu=True)
        self._notif(user, 'FACTURE', 'Nouvelles factures du mois', 'Vos factures de loyer, SODECI et CIE sont disponibles.')
        self._notif(user, 'PAIEMENT', 'Paiement validé', 'Votre dernier paiement a été validé par l’administrateur.', lu=True)
        if en_retard:
            self._notif(user, 'RAPPEL', 'Factures en retard', 'Vous avez des factures en retard. Merci de régulariser rapidement.')

    def _notifications_admins(self):
        for admin in self.admins:
            self._notif(admin, 'INFO', 'Nouvelles réservations', '2 demandes de réservation attendent votre réponse.')
            self._notif(admin, 'PAIEMENT', 'Paiement à valider', 'Mariam Traoré a envoyé une preuve de paiement.')
            self._notif(admin, 'WARNING', 'Locataire en retard', 'Seydou Bamba a des factures en retard.')
            self._notif(admin, 'SUCCESS', 'Loyers encaissés', 'Les loyers du mois dernier ont été encaissés.', lu=True)

    # --------------------------------------------------------------- suppression
    def supprimer(self):
        Notification.objects.filter(metadata__demo=True).delete()
        Facture.objects.filter(reference__startswith='DEMO-').delete()
        paiements = Paiement.objects.filter(reference__startswith='DEMO-')
        for nom in set(paiements.values_list('preuve', flat=True)):
            try:
                Paiement._meta.get_field('preuve').storage.delete(nom)
            except Exception:
                pass
        paiements.delete()
        reels = User.objects.filter(locations__maison__reference__startswith='DEMO-').exclude(email__endswith=DOMAINE)
        reels.update(statut='A_JOUR')
        n, _ = User.objects.filter(email__endswith=DOMAINE).delete()
        self.out(f'Activité de démo supprimée ({n} objets liés aux locataires de démo).')
