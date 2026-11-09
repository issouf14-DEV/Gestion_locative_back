"""
Données de démonstration : un 2e super admin et 12 maisons d'Abidjan avec photos.

    python manage.py seed_demo              # crée (ne fait rien si déjà présent)
    python manage.py seed_demo --supprimer  # supprime tout ce qui a été créé

Le 2e admin est lu depuis DEMO_ADMIN_EMAIL et DEMO_ADMIN_PASSWORD (12 caractères min.).
Les maisons de démo ont une référence qui commence par « DEMO- ».
"""
import os
import urllib.request
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.properties.models import ImageMaison, Maison

PREFIXE = 'DEMO-'
UNSPLASH = 'https://images.unsplash.com/photo-{}?w=1200&q=75&fm=jpg'

# Photos intérieures réparties entre les maisons
INTERIEURS = [
    '1502672260266-1c1ef2d93688', '1522708323590-d24dbb6b0267', '1493809842364-78817add7ffb',
    '1484154218962-a197022b5858', '1505691938895-1758d7feb511', '1560448204-e02f11c3d0e2',
    '1600607687939-ce8a6c25118c', '1586023492125-27b2c045efd7', '1556909114-f6e7ad7d3136',
    '1540518614846-7eded433c457', '1554995207-c18c203602cb', '1600566753190-17f0baa2a6c3',
    '1600210492486-724fe5c67fb0', '1600047509807-ba8f99d2cdde', '1605276374104-dee2a0ed3cd6',
    '1583608205776-bfd35f0d9f83',
]

MAISONS = [
    # titre, type, prix, commune, quartier, chambres, sdb, superficie, meublée, photo façade
    ('Villa moderne avec piscine', 'VILLA', 850000, 'Cocody', 'Riviera 3', 5, 4, 420, True,
     '1564013799919-ab600027ffc6'),
    ('Duplex lumineux à Angré', 'DUPLEX', 450000, 'Cocody', 'Angré 8e tranche', 4, 3, 260, False,
     '1600596542815-ffad4c1539a9'),
    ('Appartement F3 Zone 4', 'F3', 300000, 'Marcory', 'Zone 4', 2, 2, 110, True,
     '1600585154340-be6161a56a0c'),
    ('Villa familiale Bingerville', 'VILLA', 550000, 'Bingerville', 'Cité Feh Kessé', 4, 3, 350, False,
     '1568605114967-8130f3a36994'),
    ('Maison F4 avec jardin', 'F4', 280000, 'Yopougon', 'Niangon Lokoa', 3, 2, 180, False,
     '1570129477492-45c003edd2be'),
    ('Villa de standing aux Deux Plateaux', 'VILLA', 1200000, 'Cocody', 'Deux Plateaux Vallon', 6, 5, 500, True,
     '1613490493576-7fde63acd811'),
    ('Appartement F2 au Plateau', 'F2', 250000, 'Plateau', 'Centre des affaires', 1, 1, 70, True,
     '1512917774080-9991f1c4c750'),
    ('Maison F3 calme à Koumassi', 'F3', 180000, 'Koumassi', 'Remblais', 2, 1, 95, False,
     '1580587771525-78b9dba3b914'),
    ('Appartement F2 à Treichville', 'F2', 200000, 'Treichville', 'Avenue 16', 1, 1, 65, False,
     '1600047509807-ba8f99d2cdde'),
    ('Maison F4 à Abobo', 'F4', 150000, 'Abobo', 'Abobo Baoulé', 3, 2, 140, False,
     '1605276374104-dee2a0ed3cd6'),
    ('Villa bord de mer à Port-Bouët', 'VILLA', 650000, 'Port-Bouët', 'Gonzagueville', 4, 3, 300, True,
     '1583608205776-bfd35f0d9f83'),
    ('Studio meublé à Adjamé', 'STUDIO', 100000, 'Adjamé', 'Williamsville', 1, 1, 35, True,
     '1600210492486-724fe5c67fb0'),
]

EQUIPEMENTS = ['climatisation', 'cuisine équipée', 'parking', 'eau chaude', 'gardiennage', 'groupe électrogène']
COMMODITES = ['école', 'supermarché', 'pharmacie', 'transport', 'hôpital']


def telecharger(photo_id):
    requete = urllib.request.Request(UNSPLASH.format(photo_id), headers={'User-Agent': 'gestion-locative-seed'})
    with urllib.request.urlopen(requete, timeout=30) as reponse:
        return reponse.read()


class Command(BaseCommand):
    help = "Crée (ou supprime avec --supprimer) un 2e super admin et des maisons de démonstration."

    def add_arguments(self, parser):
        parser.add_argument('--supprimer', action='store_true', help='Supprime les données de démo')

    def handle(self, *args, **options):
        if options['supprimer']:
            self.supprimer()
        else:
            self.creer_admin()
            self.creer_maisons()

    def creer_admin(self):
        email = os.environ.get('DEMO_ADMIN_EMAIL', '').strip()
        password = os.environ.get('DEMO_ADMIN_PASSWORD', '')
        if not email or len(password) < 12:
            self.stdout.write(self.style.WARNING('DEMO_ADMIN_EMAIL / DEMO_ADMIN_PASSWORD absents : 2e admin non créé.'))
            return
        User = get_user_model()
        if User.objects.filter(email=email).exists():
            self.stdout.write(f'2e admin déjà présent : {email}')
            return
        User.objects.create_superuser(
            email=email, password=password, nom='Demo', prenoms='Admin', telephone='+225 00 00 00 00 01',
        )
        self.stdout.write(self.style.SUCCESS(f'2e super admin créé : {email}'))

    def creer_maisons(self):
        if Maison.objects.filter(reference__startswith=PREFIXE).exists():
            self.stdout.write('Maisons de démo déjà présentes : rien à faire.')
            return
        for i, (titre, type_l, prix, commune, quartier, ch, sdb, surface, meublee, facade) in enumerate(MAISONS):
            with transaction.atomic():
                maison = Maison.objects.create(
                    reference=f'{PREFIXE}{i + 1:03d}',
                    titre=titre,
                    description=(
                        f"{titre} situé(e) à {quartier}, {commune}. Logement de {surface} m² avec "
                        f"{ch} chambre(s) et {sdb} salle(s) de bain, dans un quartier calme et sécurisé."
                    ),
                    type_logement=type_l,
                    prix=Decimal(prix),
                    caution=Decimal(prix * 2),
                    adresse=f'{quartier}, {commune}, Abidjan',
                    commune=commune,
                    quartier=quartier,
                    nombre_chambres=ch,
                    nombre_salles_bain=sdb,
                    nombre_toilettes=sdb,
                    superficie=Decimal(surface),
                    equipements=EQUIPEMENTS[: 3 + i % 4],
                    commodites=COMMODITES[: 2 + i % 4],
                    meublee=meublee,
                    statut='DISPONIBLE',
                )
                photos = [facade, INTERIEURS[(2 * i) % 16], INTERIEURS[(2 * i + 1) % 16]]
                for ordre, photo_id in enumerate(photos):
                    try:
                        contenu = telecharger(photo_id)
                    except Exception as erreur:  # une photo manquante ne bloque pas le déploiement
                        self.stdout.write(self.style.WARNING(f'Photo {photo_id} ignorée : {erreur}'))
                        continue
                    image = ImageMaison(maison=maison, est_principale=(ordre == 0), ordre=ordre,
                                        legende='Façade' if ordre == 0 else 'Intérieur')
                    image.image.save(f'demo-{i + 1:03d}-{ordre}.jpg', ContentFile(contenu), save=True)
            self.stdout.write(self.style.SUCCESS(f'Maison créée : {titre}'))

    def supprimer(self):
        maisons = Maison.objects.filter(reference__startswith=PREFIXE)
        for image in ImageMaison.objects.filter(maison__in=maisons):
            try:
                image.image.delete(save=False)  # supprime aussi le fichier sur Cloudinary
            except Exception:
                pass
        nombre = maisons.count()
        maisons.delete()
        self.stdout.write(self.style.SUCCESS(f'{nombre} maison(s) de démo supprimée(s).'))

        email = os.environ.get('DEMO_ADMIN_EMAIL', '').strip()
        if email:
            supprimes, _ = get_user_model().objects.filter(email=email).delete()
            self.stdout.write(self.style.SUCCESS(f'2e admin supprimé : {email}' if supprimes else 'Aucun 2e admin à supprimer.'))
