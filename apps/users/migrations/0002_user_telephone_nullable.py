from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='telephone',
            field=models.CharField(
                blank=True,
                default=None,
                error_messages={'unique': 'Ce numéro de téléphone est déjà utilisé.'},
                max_length=20,
                null=True,
                unique=True,
                verbose_name='Téléphone',
            ),
        ),
    ]
