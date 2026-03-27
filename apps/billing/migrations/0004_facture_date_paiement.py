from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0003_compteurs_notifications'),
    ]

    operations = [
        migrations.AddField(
            model_name='facture',
            name='date_paiement',
            field=models.DateField(blank=True, null=True, verbose_name='Date de paiement'),
        ),
    ]
