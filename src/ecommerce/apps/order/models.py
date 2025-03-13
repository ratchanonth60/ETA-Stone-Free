from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.utils.translation import gettext_lazy as _
from oscar.apps.address.abstract_models import (
    AbstractBillingAddress,
    AbstractShippingAddress,
)
from oscar.apps.order.abstract_models import (
    AbstractCommunicationEvent,
    AbstractLine,
    AbstractLineAttribute,
    AbstractLinePrice,
    AbstractOrder,
    AbstractOrderDiscount,
    AbstractOrderNote,
    AbstractOrderStatusChange,
    AbstractPaymentEvent,
    AbstractPaymentEventType,
    AbstractShippingEvent,
    AbstractShippingEventType,
    AbstractSurcharge,
)
from oscar.core.compat import AUTH_USER_MODEL
from oscar.core.utils import get_default_currency
from oscar.models.fields import AutoSlugField
from phonenumber_field.modelfields import PhoneNumberField


class Order(AbstractOrder):
    number = models.CharField(
        _("Order number"), max_length=128, db_index=True, unique=True
    )

    # We track the site that each order is placed within
    site = models.ForeignKey(
        "sites.Site", verbose_name=_("Site"), null=True, on_delete=models.SET_NULL
    )

    basket = models.ForeignKey(
        "basket.Basket",
        verbose_name=_("Basket"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    # Orders can be placed without the user authenticating so we don't always
    # have a customer ID.
    user = models.ForeignKey(
        AUTH_USER_MODEL,
        related_name="orders",
        null=True,
        blank=True,
        verbose_name=_("User"),
        on_delete=models.SET_NULL,
    )

    # Billing address is not always required (eg paying by gift card)
    billing_address = models.ForeignKey(
        "order.BillingAddress",
        null=True,
        blank=True,
        verbose_name=_("Billing Address"),
        on_delete=models.SET_NULL,
    )

    # Total price looks like it could be calculated by adding up the
    # prices of the associated lines, but in some circumstances extra
    # order-level charges are added and so we need to store it separately
    currency = models.CharField(
        _("Currency"), max_length=12, default=get_default_currency
    )
    total_incl_tax = models.DecimalField(
        _("Order total (inc. tax)"), decimal_places=2, max_digits=12
    )
    total_excl_tax = models.DecimalField(
        _("Order total (excl. tax)"), decimal_places=2, max_digits=12
    )

    # Shipping charges
    shipping_incl_tax = models.DecimalField(
        _("Shipping charge (inc. tax)"), decimal_places=2, max_digits=12, default=0
    )
    shipping_excl_tax = models.DecimalField(
        _("Shipping charge (excl. tax)"), decimal_places=2, max_digits=12, default=0
    )

    # Not all lines are actually shipped (such as downloads), hence shipping
    # address is not mandatory.
    shipping_address = models.ForeignKey(
        "order.ShippingAddress",
        null=True,
        blank=True,
        verbose_name=_("Shipping Address"),
        on_delete=models.SET_NULL,
    )
    shipping_method = models.CharField(_("Shipping method"), max_length=128, blank=True)

    # Identifies shipping code
    shipping_code = models.CharField(blank=True, max_length=128, default="")

    # Use this field to indicate that an order is on hold / awaiting payment
    status = models.CharField(_("Status"), max_length=100, blank=True)
    guest_email = models.EmailField(_("Guest email address"), blank=True)

    # Index added to this field for reporting
    date_placed = models.DateTimeField(db_index=True)

    #: Order status pipeline.  This should be a dict where each (key, value) #:
    #: corresponds to a status and a list of possible statuses that can follow
    #: that one.
    pipeline = getattr(settings, "OSCAR_ORDER_STATUS_PIPELINE", {})

    #: Order status cascade pipeline.  This should be a dict where each (key,
    #: value) pair corresponds to an *order* status and the corresponding
    #: *line* status that needs to be set when the order is set to the new
    #: status
    cascade = getattr(settings, "OSCAR_ORDER_STATUS_CASCADE", {})


class OrderNote(AbstractOrderNote):  # noqa: F405
    order = models.ForeignKey(
        "order.Order",
        on_delete=models.CASCADE,
        related_name="notes",
        verbose_name=_("Order"),
    )

    # These are sometimes programatically generated so don't need a
    # user everytime
    user = models.ForeignKey(
        AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, verbose_name=_("User")
    )

    # We allow notes to be classified although this isn't always needed
    INFO, WARNING, ERROR, SYSTEM = "Info", "Warning", "Error", "System"
    note_type = models.CharField(_("Note Type"), max_length=128, blank=True)

    message = models.TextField(_("Message"))
    date_created = models.DateTimeField(_("Date Created"), auto_now_add=True)
    date_updated = models.DateTimeField(_("Date Updated"), auto_now=True)

    # Notes can only be edited for 5 minutes after being created
    editable_lifetime = 300


class OrderStatusChange(AbstractOrderStatusChange):
    order = models.ForeignKey(
        "order.Order",
        on_delete=models.CASCADE,
        related_name="status_changes",
        verbose_name=_("Order Status Changes"),
    )
    old_status = models.CharField(_("Old Status"), max_length=100, blank=True)
    new_status = models.CharField(_("New Status"), max_length=100, blank=True)
    date_created = models.DateTimeField(
        _("Date Created"), auto_now_add=True, db_index=True
    )


class CommunicationEvent(AbstractCommunicationEvent):
    order = models.ForeignKey(
        "order.Order",
        on_delete=models.CASCADE,
        related_name="communication_events",
        verbose_name=_("Order"),
    )
    event_type = models.ForeignKey(
        "communication.CommunicationEventType",
        on_delete=models.CASCADE,
        verbose_name=_("Event Type"),
    )
    date_created = models.DateTimeField(_("Date"), auto_now_add=True, db_index=True)


class ShippingAddress(AbstractShippingAddress):
    phone_number = PhoneNumberField(
        _("Phone number"),
        blank=True,
        help_text=_("In case we need to call you about your order"),
    )
    notes = models.TextField(
        blank=True,
        verbose_name=_("Instructions"),
        help_text=_("Tell us anything we should know when delivering your order."),
    )


class BillingAddress(AbstractBillingAddress):
    pass


class Line(AbstractLine):
    partner = models.ForeignKey(
        "partner.Partner",
        related_name="order_lines",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        verbose_name=_("Partner"),
    )
    partner_name = models.CharField(_("Partner name"), max_length=128, blank=True)
    partner_sku = models.CharField(_("Partner SKU"), max_length=128)

    # A line reference is the ID that a partner uses to represent this
    # particular line (it's not the same as a SKU).
    partner_line_reference = models.CharField(
        _("Partner reference"),
        max_length=128,
        blank=True,
        help_text=_(
            "This is the item number that the partner uses within their system"
        ),
    )
    partner_line_notes = models.TextField(_("Partner Notes"), blank=True)


class LinePrice(AbstractLinePrice):
    order = models.ForeignKey(
        "order.Order",
        on_delete=models.CASCADE,
        related_name="line_prices",
        verbose_name=_("Option"),
    )
    line = models.ForeignKey(
        "order.Line",
        on_delete=models.CASCADE,
        related_name="prices",
        verbose_name=_("Line"),
    )
    quantity = models.PositiveIntegerField(_("Quantity"), default=1)
    price_incl_tax = models.DecimalField(
        _("Price (inc. tax)"), decimal_places=2, max_digits=12
    )
    price_excl_tax = models.DecimalField(
        _("Price (excl. tax)"), decimal_places=2, max_digits=12
    )
    shipping_incl_tax = models.DecimalField(
        _("Shiping (inc. tax)"), decimal_places=2, max_digits=12, default=0
    )
    shipping_excl_tax = models.DecimalField(
        _("Shipping (excl. tax)"), decimal_places=2, max_digits=12, default=0
    )


class LineAttribute(AbstractLineAttribute):
    line = models.ForeignKey(
        "order.Line",
        on_delete=models.CASCADE,
        related_name="attributes",
        verbose_name=_("Line"),
    )
    option = models.ForeignKey(
        "catalogue.Option",
        null=True,
        on_delete=models.SET_NULL,
        related_name="line_attributes",
        verbose_name=_("Option"),
    )
    type = models.CharField(_("Type"), max_length=128)
    value = models.JSONField(_("Value"), encoder=DjangoJSONEncoder)


class ShippingEvent(AbstractShippingEvent):
    order = models.ForeignKey(
        "order.Order",
        on_delete=models.CASCADE,
        related_name="shipping_events",
        verbose_name=_("Order"),
    )
    lines = models.ManyToManyField(
        "order.Line",
        related_name="shipping_events",
        through="ShippingEventQuantity",
        verbose_name=_("Lines"),
    )
    event_type = models.ForeignKey(
        "order.ShippingEventType",
        on_delete=models.CASCADE,
        verbose_name=_("Event Type"),
    )
    notes = models.TextField(
        _("Event notes"),
        blank=True,
        help_text=_("This could be the dispatch reference, or a tracking number"),
    )
    date_created = models.DateTimeField(
        _("Date Created"), auto_now_add=True, db_index=True
    )


class ShippingEventType(AbstractShippingEventType):
    name = models.CharField(_("Name"), max_length=255, unique=True)
    # Code is used in forms
    code = AutoSlugField(_("Code"), max_length=128, unique=True, populate_from="name")


class PaymentEvent(AbstractPaymentEvent):
    order = models.ForeignKey(
        "order.Order",
        on_delete=models.CASCADE,
        related_name="payment_events",
        verbose_name=_("Order"),
    )
    amount = models.DecimalField(_("Amount"), decimal_places=2, max_digits=12)
    # The reference should refer to the transaction ID of the payment gateway
    # that was used for this event.
    reference = models.CharField(_("Reference"), max_length=128, blank=True)
    lines = models.ManyToManyField(
        "order.Line", through="PaymentEventQuantity", verbose_name=_("Lines")
    )
    event_type = models.ForeignKey(
        "order.PaymentEventType", on_delete=models.CASCADE, verbose_name=_("Event Type")
    )
    # Allow payment events to be linked to shipping events.  Often a shipping
    # event will trigger a payment event and so we can use this FK to capture
    # the relationship.
    shipping_event = models.ForeignKey(
        "order.ShippingEvent",
        null=True,
        on_delete=models.CASCADE,
        related_name="payment_events",
    )
    date_created = models.DateTimeField(
        _("Date created"), auto_now_add=True, db_index=True
    )


class PaymentEventType(AbstractPaymentEventType):
    name = models.CharField(_("Name"), max_length=128, unique=True)
    code = AutoSlugField(_("Code"), max_length=128, unique=True, populate_from="name")


class OrderDiscount(AbstractOrderDiscount):
    order = models.ForeignKey(
        "order.Order",
        on_delete=models.CASCADE,
        related_name="discounts",
        verbose_name=_("Order"),
    )

    # We need to distinguish between basket discounts, shipping discounts and
    # 'deferred' discounts.
    BASKET, SHIPPING, DEFERRED = "Basket", "Shipping", "Deferred"
    CATEGORY_CHOICES = (
        (BASKET, _(BASKET)),
        (SHIPPING, _(SHIPPING)),
        (DEFERRED, _(DEFERRED)),
    )
    category = models.CharField(
        _("Discount category"), default=BASKET, max_length=64, choices=CATEGORY_CHOICES
    )

    offer_id = models.PositiveIntegerField(_("Offer ID"), blank=True, null=True)
    offer_name = models.CharField(
        _("Offer name"), max_length=128, db_index=True, blank=True
    )
    voucher_id = models.PositiveIntegerField(_("Voucher ID"), blank=True, null=True)
    voucher_code = models.CharField(
        _("Code"), max_length=128, db_index=True, blank=True
    )
    frequency = models.PositiveIntegerField(_("Frequency"), null=True)
    amount = models.DecimalField(
        _("Amount"), decimal_places=2, max_digits=12, default=0
    )

    # Post-order offer applications can return a message to indicate what
    # action was taken after the order was placed.
    message = models.TextField(blank=True)


class Surcharge(AbstractSurcharge):
    order = models.ForeignKey(
        "order.Order",
        on_delete=models.CASCADE,
        related_name="surcharges",
        verbose_name=_("Surcharges"),
    )

    name = models.CharField(_("Surcharge"), max_length=128)

    code = models.CharField(_("Surcharge code"), max_length=128)

    incl_tax = models.DecimalField(
        _("Surcharge (inc. tax)"), decimal_places=2, max_digits=12, default=0
    )

    excl_tax = models.DecimalField(
        _("Surcharge (excl. tax)"), decimal_places=2, max_digits=12, default=0
    )
