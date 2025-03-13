# Generated by Django 4.2.6 on 2023-10-23 12:37

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('partner', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='partner',
            name='users',
            field=models.ManyToManyField(blank=True, related_name='partners', to=settings.AUTH_USER_MODEL, verbose_name='Users'),
        ),
        migrations.AlterUniqueTogether(
            name='stockrecord',
            unique_together={('partner', 'partner_sku')},
        ),
    ]
