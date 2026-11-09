"""
Commande pour créer un superuser automatiquement
"""
import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Crée un superuser si aucun n\'existe'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Email du superuser',
            default=os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@gestion-locative.com')
        )
        parser.add_argument(
            '--password',
            type=str,
            help='Mot de passe du superuser',
            default=os.environ.get('DJANGO_SUPERUSER_PASSWORD', '')
        )
        parser.add_argument(
            '--nom',
            type=str,
            help='Nom du superuser',
            default=os.environ.get('DJANGO_SUPERUSER_NOM', 'Admin')
        )
        parser.add_argument(
            '--prenoms',
            type=str,
            help='Prénoms du superuser',
            default=os.environ.get('DJANGO_SUPERUSER_PRENOMS', 'Super')
        )
        parser.add_argument(
            '--telephone',
            type=str,
            help='Téléphone du superuser',
            default=os.environ.get('DJANGO_SUPERUSER_TELEPHONE', '+225 00 00 00 00 00')
        )

    def handle(self, *args, **options):
        email = options['email']
        password = options['password']
        nom = options['nom']
        prenoms = options['prenoms']
        telephone = options['telephone']

        # Aucun mot de passe par défaut : on refuse de créer un admin devinable
        if not password or len(password) < 12:
            self.stdout.write(self.style.WARNING(
                'DJANGO_SUPERUSER_PASSWORD absent ou trop court (12 caractères min.) : '
                'superuser non créé.'
            ))
            return

        existant = User.objects.filter(email__iexact=email).first()
        if existant and existant.is_superuser:
            self.stdout.write(
                self.style.WARNING(f'Le superuser avec l\'email {existant.email} existe déjà.')
            )
            return
        if existant:
            # Compte déjà inscrit (ex. locataire) : on le promeut administrateur, une seule fois
            existant.is_superuser = True
            existant.is_staff = True
            existant.role = 'ADMIN'
            existant.set_password(password)
            existant.save()
            self.stdout.write(self.style.SUCCESS(f'Compte {existant.email} promu super admin.'))
            return

        user = User.objects.create_superuser(
            email=email,
            password=password,
            nom=nom,
            prenoms=prenoms,
            telephone=telephone,
            role='ADMIN'
        )

        self.stdout.write(
            self.style.SUCCESS(f'Superuser créé avec succès: {email}')
        )
