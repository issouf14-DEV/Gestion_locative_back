"""
Fonctions utilitaires diverses
"""
import random
import string
from datetime import datetime, timedelta
from django.utils import timezone


def generate_random_code(length=8):
    """
    Génère un code aléatoire alphanumérique
    """
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))


def generate_reference(prefix='REF'):
    """
    Génère une référence unique avec préfixe
    """
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    random_part = generate_random_code(4)
    return f"{prefix}-{timestamp}-{random_part}"


def calculate_months_difference(start_date, end_date):
    """
    Calcule la différence en mois entre deux dates
    """
    return (end_date.year - start_date.year) * 12 + end_date.month - start_date.month


def add_months_to_date(date, months):
    """
    Ajoute un nombre de mois à une date
    """
    month = date.month - 1 + months
    year = date.year + month // 12
    month = month % 12 + 1
    day = min(date.day, [31, 
        29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28,
        31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month-1])
    return date.replace(year=year, month=month, day=day)


def format_currency(amount):
    """
    Formate un montant en devise (FCFA)
    """
    return f"{amount:,.0f} FCFA".replace(',', ' ')


def is_date_past(date):
    """
    Vérifie si une date est passée
    """
    return date < timezone.now().date() if isinstance(date, datetime) else date < timezone.now()
