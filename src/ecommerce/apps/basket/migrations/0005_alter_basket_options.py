# Generated by Django 4.2.8 on 2024-03-07 08:31

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('basket', '0004_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='basket',
            options={'ordering': ['-id']},
        ),
    ]
