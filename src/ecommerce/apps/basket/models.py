from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.utils.translation import gettext_lazy as _
from oscar.apps.basket.abstract_models import (
    AbstractBasket,
    AbstractLine,
    AbstractLineAttribute,
)
from oscar.core.compat import AUTH_USER_MODEL
from oscar.core.utils import get_default_currency
from oscar.models.fields.slugfield import SlugField

from ecommerce.core.defults import OPEN, SAVED, STATUS_CHOICES_BASKET


class Basket(AbstractBasket):
    owner = models.ForeignKey(
        AUTH_USER_MODEL,
        null=True,
        related_name="baskets",
        on_delete=models.CASCADE,
        verbose_name=_("Owner"),
    )

    STATUS_CHOICES = STATUS_CHOICES_BASKET
    status = models.CharField(
        _("Status"), max_length=128, default=OPEN, choices=STATUS_CHOICES
    )

    # A basket can have many vouchers attached to it.  However, it is common
    # for sites to only allow one voucher per basket - this will need to be
    # enforced in the project's codebase.
    vouchers = models.ManyToManyField(
        "voucher.Voucher", verbose_name=_("Vouchers"), blank=True
    )

    date_created = models.DateTimeField(_("Date created"), auto_now_add=True)
    date_merged = models.DateTimeField(_("Date merged"), null=True, blank=True)
    date_submitted = models.DateTimeField(_("Date submitted"), null=True, blank=True)

    # Only if a basket is in one of these statuses can it be edited
    editable_statuses = (OPEN, SAVED)

    class Meta(AbstractBasket.Meta):
        ordering = ["-id"]


class Line(AbstractLine):
    basket = models.ForeignKey(
        "basket.Basket",
        on_delete=models.CASCADE,
        related_name="lines",
        verbose_name=_("Basket"),
    )

    # This is to determine which products belong to the same line
    # We can't just use product.id as you can have customised products
    # which should be treated as separate lines.  Set as a
    # SlugField as it is included in the path for certain views.
    line_reference = SlugField(_("Line Reference"), max_length=128, db_index=True)

    product = models.ForeignKey(
        "catalogue.Product",
        on_delete=models.CASCADE,
        related_name="basket_lines",
        verbose_name=_("Product"),
    )

    # We store the stockrecord that should be used to fulfil this line.
    stockrecord = models.ForeignKey(
        "partner.StockRecord", on_delete=models.CASCADE, related_name="basket_lines"
    )

    quantity = models.PositiveIntegerField(_("Quantity"), default=1)

    # We store the unit price incl tax of the product when it is first added to
    # the basket.  This allows us to tell if a product has changed price since
    # a person first added it to their basket.
    price_currency = models.CharField(
        _("Currency"), max_length=12, default=get_default_currency
    )
    price_excl_tax = models.DecimalField(
        _("Price excl. Tax"), decimal_places=2, max_digits=12, null=True
    )
    price_incl_tax = models.DecimalField(
        _("Price incl. Tax"), decimal_places=2, max_digits=12, null=True
    )

    # Track date of first addition
    date_created = models.DateTimeField(
        _("Date Created"), auto_now_add=True, db_index=True
    )
    date_updated = models.DateTimeField(_("Date Updated"), auto_now=True, db_index=True)


class LineAttribute(AbstractLineAttribute):
    line = models.ForeignKey(
        "basket.Line",
        on_delete=models.CASCADE,
        related_name="attributes",
        verbose_name=_("Line"),
    )
    option = models.ForeignKey(
        "catalogue.Option", on_delete=models.CASCADE, verbose_name=_("Option")
    )
    value = models.JSONField(_("Value"), encoder=DjangoJSONEncoder)
