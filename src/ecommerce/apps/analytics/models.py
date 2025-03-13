from decimal import Decimal

from django.db import models
from django.utils.translation import gettext_lazy as _
from oscar.apps.analytics.abstract_models import (
    AbstractProductRecord,
    AbstractUserProductView,
    AbstractUserRecord,
    AbstractUserSearch,
)
from oscar.core.compat import AUTH_USER_MODEL


class ProductRecord(AbstractProductRecord):
    product = models.OneToOneField(
        "catalogue.Product",
        verbose_name=_("Product"),
        related_name="stats",
        on_delete=models.CASCADE,
    )

    # Data used for generating a score
    num_views = models.PositiveIntegerField(_("Views"), default=0)
    num_basket_additions = models.PositiveIntegerField(_("Basket Additions"), default=0)
    num_purchases = models.PositiveIntegerField(
        _("Purchases"), default=0, db_index=True
    )

    # Product score - used within search
    score = models.FloatField(_("Score"), default=0.00)


class UserRecord(AbstractUserRecord):
    user = models.OneToOneField(
        AUTH_USER_MODEL, verbose_name=_("User"), on_delete=models.CASCADE
    )

    # Browsing stats
    num_product_views = models.PositiveIntegerField(_("Product Views"), default=0)
    num_basket_additions = models.PositiveIntegerField(_("Basket Additions"), default=0)

    # Order stats
    num_orders = models.PositiveIntegerField(_("Orders"), default=0, db_index=True)
    num_order_lines = models.PositiveIntegerField(
        _("Order Lines"), default=0, db_index=True
    )
    num_order_items = models.PositiveIntegerField(
        _("Order Items"), default=0, db_index=True
    )
    total_spent = models.DecimalField(
        _("Total Spent"), decimal_places=2, max_digits=12, default=Decimal("0.00")
    )
    date_last_order = models.DateTimeField(_("Last Order Date"), blank=True, null=True)


class UserProductView(AbstractUserProductView):
    user = models.ForeignKey(
        AUTH_USER_MODEL, verbose_name=_("User"), on_delete=models.CASCADE
    )
    product = models.ForeignKey(
        "catalogue.Product", on_delete=models.CASCADE, verbose_name=_("Product")
    )
    date_created = models.DateTimeField(_("Date Created"), auto_now_add=True)


class UserSearch(AbstractUserSearch):
    user = models.ForeignKey(
        AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name=_("User")
    )
    query = models.CharField(_("Search term"), max_length=255, db_index=True)
    date_created = models.DateTimeField(_("Date Created"), auto_now_add=True)
