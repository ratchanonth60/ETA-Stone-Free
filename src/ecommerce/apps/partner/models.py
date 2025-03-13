from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy
from oscar.apps.address.abstract_models import AbstractPartnerAddress
from oscar.apps.partner.abstract_models import (AbstractPartner,
                                                AbstractStockAlert,
                                                AbstractStockRecord)
from oscar.core.compat import AUTH_USER_MODEL
from oscar.core.utils import get_default_currency
from oscar.models.fields import AutoSlugField
from ecommerce.core.defults import STATUS_CHOICES_STOCKALERT


class Partner(AbstractPartner):
    code = AutoSlugField(_("Code"), max_length=128, unique=True, db_index=True,
                         populate_from='name')
    name = models.CharField(
        pgettext_lazy("Partner's name", "Name"), max_length=128, blank=True, db_index=True)

    #: A partner can have users assigned to it. This is used
    #: for access modelling in the permission-based dashboard
    users = models.ManyToManyField(
        AUTH_USER_MODEL, related_name="partners",
        blank=True, verbose_name=_("Users"))


class PartnerAddress(AbstractPartnerAddress):
    partner = models.ForeignKey(
        'partner.Partner',
        on_delete=models.CASCADE,
        related_name='addresses',
        verbose_name=_('Partner'))


class StockRecord(AbstractStockRecord):
    product = models.ForeignKey(
        'catalogue.Product',
        on_delete=models.CASCADE,
        related_name="stockrecords",
        verbose_name=_("Product"))
    partner = models.ForeignKey(
        'partner.Partner',
        on_delete=models.CASCADE,
        verbose_name=_("Partner"),
        related_name='stockrecords')
    partner_sku = models.CharField(_("Partner SKU"), max_length=128)
    price_currency = models.CharField(
        _("Currency"), max_length=12, default=get_default_currency)
    price = models.DecimalField(
        _("Price"), decimal_places=2, max_digits=12,
        blank=True, null=True)
    num_in_stock = models.PositiveIntegerField(
        _("Number in stock"), blank=True, null=True)
    num_allocated = models.IntegerField(
        _("Number allocated"), blank=True, null=True)
    low_stock_threshold = models.PositiveIntegerField(
        _("Low Stock Threshold"), blank=True, null=True)
    date_created = models.DateTimeField(_("Date created"), auto_now_add=True)
    date_updated = models.DateTimeField(_("Date updated"), auto_now=True,
                                        db_index=True)


class StockAlert(AbstractStockAlert):
    status_choices = STATUS_CHOICES_STOCKALERT
    stockrecord = models.ForeignKey(
        'partner.StockRecord',
        on_delete=models.CASCADE,
        related_name='alerts',
        verbose_name=_("Stock Record"))
    status = models.CharField(_("Status"), max_length=128,
                              default="Open",
                              choices=status_choices)
    date_created = models.DateTimeField(_("Date Created"), auto_now_add=True, db_index=True)
    date_closed = models.DateTimeField(_("Date Closed"), blank=True, null=True)
