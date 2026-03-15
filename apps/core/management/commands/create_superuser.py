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
            default=os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'Admin@2024!')
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

        if User.objects.filter(email=email).exists():
            self.stdout.write(
                self.style.WARNING(f'Le superuser avec l\'email {email} existe déjà.')
            )
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
