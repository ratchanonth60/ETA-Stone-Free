from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy
from oscar.apps.address.abstract_models import AbstractCountry, AbstractUserAddress
from oscar.core.compat import AUTH_USER_MODEL
from oscar.models.fields import UppercaseCharField

from ecommerce.core.defults import TITLE_CHOICES


class UserAddress(AbstractUserAddress):
    POSTCODE_REQUIRED = "postcode" in settings.OSCAR_REQUIRED_ADDRESS_FIELDS

    user = models.ForeignKey(
        AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="addresses",
        verbose_name=_("User"),
    )
    title = models.CharField(
        pgettext_lazy("Treatment Pronouns for the customer", "Title"),
        max_length=64,
        choices=TITLE_CHOICES,
        blank=True,
    )
    first_name = models.CharField(_("First name"), max_length=255, blank=True)
    last_name = models.CharField(_("Last name"), max_length=255, blank=True)

    # We use quite a few lines of an address as they are often quite long and
    # it's easier to just hide the unnecessary ones than add extra ones.
    line1 = models.CharField(_("First line of address"), max_length=255)
    line2 = models.CharField(_("Second line of address"), max_length=255, blank=True)
    line3 = models.CharField(_("Third line of address"), max_length=255, blank=True)
    line4 = models.CharField(_("City"), max_length=255, blank=True)
    state = models.CharField(_("State/County"), max_length=255, blank=True)
    postcode = UppercaseCharField(_("Post/Zip-code"), max_length=64, blank=True)
    country = models.ForeignKey(
        "address.Country", on_delete=models.CASCADE, verbose_name=_("Country")
    )

    # A field only used for searching addresses - this contains all the
    # `search_fields`.  This is effectively a poor man's Solr text field.
    search_text = models.TextField(
        _("Search text - used only for searching addresses"), editable=False
    )
    search_fields = [
        "first_name",
        "last_name",
        "line1",
        "line2",
        "line3",
        "line4",
        "state",
        "postcode",
        "country",
    ]

    # Fields, used for `summary` property definition and hash generation.
    base_fields = hash_fields = [
        "salutation",
        "line1",
        "line2",
        "line3",
        "line4",
        "state",
        "postcode",
        "country",
    ]
    #: Whether this address is the default for shipping
    is_default_for_shipping = models.BooleanField(
        _("Default shipping address?"), default=False
    )

    #: Whether this address should be the default for billing.
    is_default_for_billing = models.BooleanField(
        _("Default billing address?"), default=False
    )

    #: We keep track of the number of times an address has been used
    #: as a shipping address so we can show the most popular ones
    #: first at the checkout.
    num_orders_as_shipping_address = models.PositiveIntegerField(
        _("Number of Orders as Shipping Address"), default=0
    )

    #: Same as previous, but for billing address.
    num_orders_as_billing_address = models.PositiveIntegerField(
        _("Number of Orders as Billing Address"), default=0
    )

    #: A hash is kept to try and avoid duplicate addresses being added
    #: to the address book.
    hash = models.CharField(
        _("Address Hash"), max_length=255, db_index=True, editable=False
    )
    date_created = models.DateTimeField(_("Date Created"), auto_now_add=True)


class Country(AbstractCountry):
    iso_3166_1_a2 = models.CharField(
        _("ISO 3166-1 alpha-2"), max_length=2, primary_key=True
    )
    iso_3166_1_a3 = models.CharField(_("ISO 3166-1 alpha-3"), max_length=3, blank=True)
    iso_3166_1_numeric = models.CharField(
        _("ISO 3166-1 numeric"), blank=True, max_length=3
    )

    #: The commonly used name; e.g. 'United Kingdom'
    printable_name = models.CharField(_("Country name"), max_length=128, db_index=True)
    #: The full official name of a country
    #: e.g. 'United Kingdom of Great Britain and Northern Ireland'
    name = models.CharField(_("Official name"), max_length=128)

    display_order = models.PositiveSmallIntegerField(
        _("Display order"),
        default=0,
        db_index=True,
        help_text=_("Higher the number, higher the country in the list."),
    )

    is_shipping_country = models.BooleanField(
        _("Is shipping country"), default=True, db_index=True
    )
