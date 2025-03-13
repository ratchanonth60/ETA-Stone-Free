# Generated by Django 4.2.6 on 2023-10-23 12:37

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('offer', '0001_initial'),
        ('catalogue', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='rangeproductfileupload',
            name='uploaded_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Uploaded By'),
        ),
        migrations.AddField(
            model_name='rangeproduct',
            name='product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='catalogue.product'),
        ),
        migrations.AddField(
            model_name='rangeproduct',
            name='range',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='offer.range'),
        ),
        migrations.AddField(
            model_name='range',
            name='classes',
            field=models.ManyToManyField(blank=True, related_name='classes', to='catalogue.productclass', verbose_name='Product Types'),
        ),
        migrations.AddField(
            model_name='range',
            name='excluded_products',
            field=models.ManyToManyField(blank=True, related_name='excludes', to='catalogue.product', verbose_name='Excluded Products'),
        ),
        migrations.AddField(
            model_name='range',
            name='included_categories',
            field=models.ManyToManyField(blank=True, related_name='includes', to='catalogue.category', verbose_name='Included Categories'),
        ),
        migrations.AddField(
            model_name='range',
            name='included_products',
            field=models.ManyToManyField(blank=True, related_name='includes', through='offer.RangeProduct', to='catalogue.product', verbose_name='Included Products'),
        ),
        migrations.AddField(
            model_name='conditionaloffer',
            name='benefit',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='offers', to='offer.benefit', verbose_name='Benefit'),
        ),
        migrations.AddField(
            model_name='conditionaloffer',
            name='combinations',
            field=models.ManyToManyField(blank=True, help_text='Select other non-exclusive offers that this offer can be combined with on the same items', limit_choices_to={'exclusive': False}, related_name='in_combination', to='offer.conditionaloffer'),
        ),
        migrations.AddField(
            model_name='conditionaloffer',
            name='condition',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='offers', to='offer.condition', verbose_name='Condition'),
        ),
        migrations.AddField(
            model_name='condition',
            name='range',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='offer.range', verbose_name='Range'),
        ),
        migrations.AddField(
            model_name='benefit',
            name='range',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='offer.range', verbose_name='Range'),
        ),
        migrations.CreateModel(
            name='AbsoluteDiscountBenefitModify',
            fields=[
            ],
            options={
                'verbose_name': 'Absolute discount benefit',
                'verbose_name_plural': 'Absolute discount benefits',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('offer.benefit',),
        ),
        migrations.CreateModel(
            name='CountConditionModify',
            fields=[
            ],
            options={
                'verbose_name': 'Count condition',
                'verbose_name_plural': 'Count conditions',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('offer.condition',),
        ),
        migrations.CreateModel(
            name='CoverageConditionModify',
            fields=[
            ],
            options={
                'verbose_name': 'Coverage Condition',
                'verbose_name_plural': 'Coverage Conditions',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('offer.condition',),
        ),
        migrations.CreateModel(
            name='FixedPriceBenefitModify',
            fields=[
            ],
            options={
                'verbose_name': 'Fixed price benefit',
                'verbose_name_plural': 'Fixed price benefits',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('offer.benefit',),
        ),
        migrations.CreateModel(
            name='MultibuyDiscountBenefitModify',
            fields=[
            ],
            options={
                'verbose_name': 'Multibuy discount benefit',
                'verbose_name_plural': 'Multibuy discount benefits',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('offer.benefit',),
        ),
        migrations.CreateModel(
            name='PercentageDiscountBenefitModify',
            fields=[
            ],
            options={
                'verbose_name': 'Percentage discount benefit',
                'verbose_name_plural': 'Percentage discount benefits',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('offer.benefit',),
        ),
        migrations.CreateModel(
            name='ShippingBenefitModify',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('offer.benefit',),
        ),
        migrations.CreateModel(
            name='ValueConditionModify',
            fields=[
            ],
            options={
                'verbose_name': 'Value condition',
                'verbose_name_plural': 'Value conditions',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('offer.condition',),
        ),
        migrations.AlterUniqueTogether(
            name='rangeproduct',
            unique_together={('range', 'product')},
        ),
        migrations.CreateModel(
            name='FixedUnitDiscountBenefitModify',
            fields=[
            ],
            options={
                'verbose_name': 'Fixed unit discount benefit',
                'verbose_name_plural': 'Fixed unit discount benefits',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('offer.absolutediscountbenefitmodify',),
        ),
        migrations.CreateModel(
            name='ShippingAbsoluteDiscountBenefitModify',
            fields=[
            ],
            options={
                'verbose_name': 'Shipping absolute discount benefit',
                'verbose_name_plural': 'Shipping absolute discount benefits',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('offer.shippingbenefitmodify',),
        ),
        migrations.CreateModel(
            name='ShippingFixedPriceBenefitModify',
            fields=[
            ],
            options={
                'verbose_name': 'Fixed price shipping benefit',
                'verbose_name_plural': 'Fixed price shipping benefits',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('offer.shippingbenefitmodify',),
        ),
        migrations.CreateModel(
            name='ShippingPercentageDiscountBenefitModify',
            fields=[
            ],
            options={
                'verbose_name': 'Shipping percentage discount benefit',
                'verbose_name_plural': 'Shipping percentage discount benefits',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('offer.shippingbenefitmodify',),
        ),
    ]
