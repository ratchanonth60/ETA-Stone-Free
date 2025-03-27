# Generated by Django 4.2.20 on 2025-03-14 15:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalogue', '0004_attributeoption_code_attributeoptiongroup_code_and_more'),
        ('offer', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='range',
            name='excluded_categories',
            field=models.ManyToManyField(blank=True, help_text='Products with these categories are excluded from the range when Includes all products is checked', related_name='excludes', to='catalogue.category', verbose_name='Excluded Categories'),
        ),
    ]
