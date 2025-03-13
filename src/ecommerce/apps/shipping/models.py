from decimal import Decimal as D

from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from oscar.apps.shipping.abstract_models import (AbstractOrderAndItemCharges,
                                                 AbstractWeightBand,
                                                 AbstractWeightBased)


# Create your models here.
class OrderAndItemCharges(AbstractOrderAndItemCharges):
    price_per_order = models.DecimalField(
        _("Price per order"), decimal_places=2, max_digits=12,
        default=D('0.00'))
    price_per_item = models.DecimalField(
        _("Price per item"), decimal_places=2, max_digits=12,
        default=D('0.00'))

    # If basket value is above this threshold, then shipping is free
    free_shipping_threshold = models.DecimalField(
        _("Free Shipping"), decimal_places=2, max_digits=12, blank=True,
        null=True)


class WeightBased(AbstractWeightBased):
    pass


class WeightBand(AbstractWeightBand):
    method = models.ForeignKey(
        'shipping.WeightBased',
        on_delete=models.CASCADE,
        related_name='bands',
        verbose_name=_("Method"))
    upper_limit = models.DecimalField(
        _("Upper Limit"), decimal_places=3, max_digits=12, db_index=True,
        validators=[MinValueValidator(D('0.00'))],
        help_text=_("Enter upper limit of this weight band in kg. The lower "
                    "limit will be determined by the other weight bands."))
    charge = models.DecimalField(
        _("Charge"), decimal_places=2, max_digits=12,
        validators=[MinValueValidator(D('0.00'))])
