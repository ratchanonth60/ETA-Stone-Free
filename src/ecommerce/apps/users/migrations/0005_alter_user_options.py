# Generated by Django 4.2.20 on 2025-03-14 15:02

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_remove_user_created_at_remove_user_updated_at'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='user',
            options={'ordering': ['-id'], 'verbose_name': 'User', 'verbose_name_plural': 'Users'},
        ),
    ]
