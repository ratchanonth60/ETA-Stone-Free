from decimal import Decimal

from django.db import models
from django.utils.translation import gettext_lazy as _
from oscar.apps.voucher.abstract_models import (
    AbstractVoucher,
    AbstractVoucherApplication,
    AbstractVoucherSet,
)
from oscar.core.compat import AUTH_USER_MODEL


class VoucherSet(AbstractVoucherSet):
    name = models.CharField(verbose_name=_("Name"), max_length=100, unique=True)
    count = models.PositiveIntegerField(verbose_name=_("Number of vouchers"))
    code_length = models.IntegerField(verbose_name=_("Length of Code"), default=12)
    description = models.TextField(verbose_name=_("Description"))
    date_created = models.DateTimeField(auto_now_add=True, db_index=True)
    start_datetime = models.DateTimeField(_("Start datetime"))
    end_datetime = models.DateTimeField(_("End datetime"))


class Voucher(AbstractVoucher):
    """
    A voucher.  This is simply a link to a collection of offers.

    Note that there are three possible "usage" modes:
    (a) Single use
    (b) Multi-use
    (c) Once per customer

    Oscar enforces those modes by creating VoucherApplication
    instances when a voucher is used for an order.
    """

    name = models.CharField(
        _("Name"),
        max_length=128,
        unique=True,
        help_text=_(
            "This will be shown in the checkout"
            " and basket once the voucher is"
            " entered"
        ),
    )
    code = models.CharField(
        _("Code"),
        max_length=128,
        db_index=True,
        unique=True,
        help_text=_("Case insensitive / No" " spaces allowed"),
    )
    offers = models.ManyToManyField(
        "offer.ConditionalOffer",
        related_name="vouchers",
        verbose_name=_("Offers"),
        limit_choices_to={"offer_type": "Voucher"},
    )

    SINGLE_USE, MULTI_USE, ONCE_PER_CUSTOMER = (
        "Single use",
        "Multi-use",
        "Once per customer",
    )
    USAGE_CHOICES = (
        (SINGLE_USE, _("Can be used once by one customer")),
        (MULTI_USE, _("Can be used multiple times by multiple customers")),
        (ONCE_PER_CUSTOMER, _("Can only be used once per customer")),
    )
    usage = models.CharField(
        _("Usage"), max_length=128, choices=USAGE_CHOICES, default=MULTI_USE
    )

    start_datetime = models.DateTimeField(_("Start datetime"), db_index=True)
    end_datetime = models.DateTimeField(_("End datetime"), db_index=True)

    # Reporting information. Not used to enforce any consumption limits.
    num_basket_additions = models.PositiveIntegerField(
        _("Times added to basket"), default=0
    )
    num_orders = models.PositiveIntegerField(_("Times on orders"), default=0)
    total_discount = models.DecimalField(
        _("Total discount"), decimal_places=2, max_digits=12, default=Decimal("0.00")
    )

    voucher_set = models.ForeignKey(
        "voucher.VoucherSet",
        null=True,
        blank=True,
        related_name="vouchers",
        on_delete=models.CASCADE,
    )

    date_created = models.DateTimeField(auto_now_add=True, db_index=True)


class VoucherApplication(AbstractVoucherApplication):
    """
    For tracking how often a voucher has been used in an order.

    This is used to enforce the voucher usage mode in
    Voucher.is_available_to_user, and created in Voucher.record_usage.
    """

    voucher = models.ForeignKey(
        "voucher.Voucher",
        on_delete=models.CASCADE,
        related_name="applications",
        verbose_name=_("Voucher"),
    )

    # It is possible for an anonymous user to apply a voucher so we need to
    # allow the user to be nullable
    user = models.ForeignKey(
        AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        verbose_name=_("User"),
    )
    order = models.ForeignKey(
        "order.Order", on_delete=models.CASCADE, verbose_name=_("Order")
    )
    date_created = models.DateTimeField(auto_now_add=True, db_index=True)
