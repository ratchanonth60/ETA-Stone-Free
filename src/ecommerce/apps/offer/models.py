# Split the code into smaller files
# FILEPATH: /Users/ratchanonth/eta/src/ecommerce/apps/offer/operators.py
import operator
from decimal import ROUND_UP
from decimal import Decimal as D

from django.conf import settings
from django.core import exceptions
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext
from oscar.apps.offer.abstract_models import (
    AbstractBenefit,
    AbstractCondition,
    AbstractConditionalOffer,
    AbstractRange,
    AbstractRangeProduct,
    AbstractRangeProductFileUpload,
)
from oscar.apps.offer.managers import (
    ActiveOfferManager,
    BrowsableRangeManager,
    RangeManager,
)
from oscar.apps.offer.results import (
    SHIPPING_DISCOUNT,
    ZERO_DISCOUNT,
    BasketDiscount,
    PostOrderAction,
    ShippingDiscount,
)
from oscar.core.compat import AUTH_USER_MODEL
from oscar.core.loading import get_class
from oscar.models import fields

from ecommerce.apps.offer.utils import range_anchor, unit_price
from ecommerce.templatetags.currency_filters import currency

__all__ = [
    "BasketDiscount",
    "ShippingDiscount",
    "PostOrderAction",
    "SHIPPING_DISCOUNT",
    "ZERO_DISCOUNT",
    "CountConditionModify",
    "CoverageConditionModify",
    "ValueConditionModify",
    "PercentageDiscountBenefitModify",
    "AbsoluteDiscountBenefitModify",
    "FixedPriceBenefitModify",
    "FixedUnitDiscountBenefitModify",
    "ShippingBenefitModify",
    "MultibuyDiscountBenefitModify",
    "ShippingAbsoluteDiscountBenefitModify",
    "ShippingFixedPriceBenefitModify",
    "ShippingPercentageDiscountBenefitModify",
]


class ConditionalOffer(AbstractConditionalOffer):
    name = models.CharField(
        _("Name"),
        max_length=128,
        unique=True,
        help_text=_("This is displayed within the customer's basket"),
    )
    slug = fields.AutoSlugField(
        _("Slug"), max_length=128, unique=True, populate_from="name"
    )
    description = models.TextField(
        _("Description"),
        blank=True,
        help_text=_("This is displayed on the offer browsing page"),
    )

    # Offers come in a few different types:
    # (a) Offers that are available to all customers on the site. e.g. a
    #     3-for-2 offer.
    # (b) Offers that are linked to a voucher, and only become available once
    #     that voucher has been applied to the basket
    # (c) Offers that are linked to a user.  e.g. all students get 10% off.  The
    #     code to apply this offer needs to be coded
    # (d) Session offers - these are temporarily available to a user after some
    #     trigger event.  e.g. users coming from some affiliate site get 10%
    #     off.
    SITE, VOUCHER, USER, SESSION = ("Site", "Voucher", "User", "Session")
    TYPE_CHOICES = (
        (SITE, _("Site offer - available to all users")),
        (
            VOUCHER,
            _(
                "Voucher offer - only available after entering "
                "the appropriate voucher code"
            ),
        ),
        (USER, _("User offer - available to certain types of user")),
        (
            SESSION,
            _(
                "Session offer - temporary offer, available for "
                "a user for the duration of their session"
            ),
        ),
    )
    offer_type = models.CharField(
        _("Type"), choices=TYPE_CHOICES, default=SITE, max_length=128
    )

    exclusive = models.BooleanField(
        _("Exclusive offer"),
        help_text=_("Exclusive offers cannot be combined on the same items"),
        default=True,
    )
    combinations = models.ManyToManyField(
        "offer.ConditionalOffer",
        help_text=_(
            "Select other non-exclusive offers that this offer can be combined with on the same items"
        ),
        related_name="in_combination",
        limit_choices_to={"exclusive": False},
        blank=True,
    )

    # We track a status variable so it's easier to load offers that are
    # 'available' in some sense.
    OPEN, SUSPENDED, CONSUMED = "Open", "Suspended", "Consumed"
    status = models.CharField(_("Status"), max_length=64, default=OPEN)

    condition = models.ForeignKey(
        "offer.Condition",
        on_delete=models.CASCADE,
        related_name="offers",
        verbose_name=_("Condition"),
    )
    benefit = models.ForeignKey(
        "offer.Benefit",
        on_delete=models.CASCADE,
        related_name="offers",
        verbose_name=_("Benefit"),
    )

    # Some complicated situations require offers to be applied in a set order.
    priority = models.IntegerField(
        _("Priority"),
        default=0,
        db_index=True,
        help_text=_("The highest priority offers are applied first"),
    )

    # AVAILABILITY

    # Range of availability.  Note that if this is a voucher offer, then these
    # dates are ignored and only the dates from the voucher are used to
    # determine availability.
    start_datetime = models.DateTimeField(
        _("Start date"),
        blank=True,
        null=True,
        help_text=_(
            "Offers are active from the start date. "
            "Leave this empty if the offer has no start date."
        ),
    )
    end_datetime = models.DateTimeField(
        _("End date"),
        blank=True,
        null=True,
        help_text=_(
            "Offers are active until the end date. "
            "Leave this empty if the offer has no expiry date."
        ),
    )

    # Use this field to limit the number of times this offer can be applied in
    # total.  Note that a single order can apply an offer multiple times so
    # this is not necessarily the same as the number of orders that can use it.
    # Also see max_basket_applications.
    max_global_applications = models.PositiveIntegerField(
        _("Max global applications"),
        help_text=_(
            "The number of times this offer can be used before it is unavailable"
        ),
        blank=True,
        null=True,
    )

    # Use this field to limit the number of times this offer can be used by a
    # single user.  This only works for signed-in users - it doesn't really
    # make sense for sites that allow anonymous checkout.
    max_user_applications = models.PositiveIntegerField(
        _("Max user applications"),
        help_text=_("The number of times a single user can use this offer"),
        blank=True,
        null=True,
    )

    # Use this field to limit the number of times this offer can be applied to
    # a basket (and hence a single order). Often, an offer should only be
    # usable once per basket/order, so this field will commonly be set to 1.
    max_basket_applications = models.PositiveIntegerField(
        _("Max basket applications"),
        blank=True,
        null=True,
        help_text=_("The number of times this offer can be applied to a basket (and order)"),
    )

    # Use this field to limit the amount of discount an offer can lead to.
    # This can be helpful with budgeting.
    max_discount = models.DecimalField(
        _("Max discount"),
        decimal_places=2,
        max_digits=12,
        null=True,
        blank=True,
        help_text=_(
            "When an offer has given more discount to orders "
            "than this threshold, then the offer becomes "
            "unavailable"
        ),
    )

    # TRACKING
    # These fields are used to enforce the limits set by the
    # max_* fields above.

    total_discount = models.DecimalField(
        _("Total Discount"), decimal_places=2, max_digits=12, default=D("0.00")
    )
    num_applications = models.PositiveIntegerField(
        _("Number of applications"), default=0
    )
    num_orders = models.PositiveIntegerField(_("Number of Orders"), default=0)

    redirect_url = fields.ExtendedURLField(_("URL redirect (optional)"), blank=True)
    date_created = models.DateTimeField(_("Date Created"), auto_now_add=True)

    objects = models.Manager()
    active = ActiveOfferManager()

    # We need to track the voucher that this offer came from (if it is a
    # voucher offer)
    _voucher = None

    def is_condition_satisfied(self, basket):
        return self.condition.proxy().is_satisfied(self, basket)


class Benefit(AbstractBenefit):
    name = "Benefit"
    range = models.ForeignKey(
        "offer.Range",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        verbose_name=_("Range"),
    )

    # Benefit types
    PERCENTAGE, FIXED, MULTIBUY, FIXED_PRICE = (
        "Percentage",
        "Absolute",
        "Multibuy",
        "Fixed price",
    )
    SHIPPING_PERCENTAGE, SHIPPING_ABSOLUTE, SHIPPING_FIXED_PRICE = (
        "Shipping percentage",
        "Shipping absolute",
        "Shipping fixed price",
    )
    TYPE_CHOICES = (
        (PERCENTAGE, _("Discount is a percentage off of the product's value")),
        (FIXED, _("Discount is a fixed amount off of the product's value")),
        (MULTIBUY, _("Discount is to give the cheapest product for free")),
        (FIXED_PRICE, _("Get the products that meet the condition for a fixed price")),
        (SHIPPING_ABSOLUTE, _("Discount is a fixed amount of the shipping cost")),
        (SHIPPING_FIXED_PRICE, _("Get shipping for a fixed price")),
        (
            SHIPPING_PERCENTAGE,
            _("Discount is a percentage off of the shipping cost"),
        ),
    )
    type = models.CharField(_("Type"), max_length=128, choices=TYPE_CHOICES, blank=True)

    # The value to use with the designated type.  This can be either an integer
    # (eg for multibuy) or a decimal (eg an amount) which is slightly
    # confusing.
    value = fields.PositiveDecimalField(
        _("Value"), decimal_places=2, max_digits=12, null=True, blank=True
    )

    # If this is not set, then there is no upper limit on how many products
    # can be discounted by this benefit.
    max_affected_items = models.PositiveIntegerField(
        _("Max Affected Items"),
        blank=True,
        null=True,
        help_text=_(
            "Set this to prevent the discount consuming all items "
            "within the range that are in the basket."
        ),
    )

    # A custom benefit class can be used instead.  This means the
    # type/value/max_affected_items fields should all be None.
    proxy_class = fields.NullCharField(_("Custom class"), max_length=255, default=None)

    def __str__(self):
        return self.name

    @property
    def description(self):
        return self.name


class Condition(AbstractCondition):
    name = "Condition"
    COUNT, VALUE, COVERAGE = ("Count", "Value", "Coverage")
    TYPE_CHOICES = (
        (
            COUNT,
            _("Depends on number of items in basket that are in condition range"),
        ),
        (
            VALUE,
            _("Depends on value of items in basket that are in " "condition range"),
        ),
        (
            COVERAGE,
            _(
                "Needs to contain a set number of DISTINCT items "
                "from the condition range"
            ),
        ),
    )
    range = models.ForeignKey(
        "offer.Range",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        verbose_name=_("Range"),
    )
    type = models.CharField(_("Type"), max_length=128, choices=TYPE_CHOICES, blank=True)
    value = fields.PositiveDecimalField(
        _("Value"), decimal_places=2, max_digits=12, null=True, blank=True
    )

    proxy_class = fields.NullCharField(_("Custom class"), max_length=255, default=None)

    @property
    def proxy_map(self):
        return {
            self.COUNT: get_class("offer.conditions", "CountCondition"),
            self.VALUE: get_class("offer.conditions", "ValueCondition"),
            self.COVERAGE: get_class("offer.conditions", "CoverageCondition"),
        }

    def clean(self):
        # The form will validate whether this is ok or not.
        if not self.type:
            return
        method_name = f"clean_{self.type.lower()}"
        if hasattr(self, method_name):
            getattr(self, method_name)()

    def clean_count(self):
        self._extracted_from_clean_coverage(
            "Count conditions require a product range",
            "Count conditions require a value",
        )

    def clean_value(self):
        self._extracted_from_clean_coverage(
            "Value conditions require a product range",
            "Value conditions require a value",
        )

    def clean_coverage(self):
        self._extracted_from_clean_coverage(
            "Coverage conditions require a product range",
            "Coverage conditions require a value",
        )

    # TODO Rename this here and in `clean_count`, `clean_value` and `clean_coverage`
    def _extracted_from_clean_coverage(self, arg0, arg1):
        errors = []
        if not self.range:
            errors.append(_(arg0))
        if not self.value:
            errors.append(_(arg1))
        if errors:
            raise exceptions.ValidationError(errors)

    def consume_items(self, offer, basket, affected_lines):
        # This method is intentionally left empty as it is meant to be implemented in the subclass.
        pass

    def is_satisfied(self, offer, basket):
        """
        Determines whether a given basket meets this condition.  This is
        stubbed in this top-class object.  The subclassing proxies are
        responsible for implementing it correctly.
        """
        return False

    def is_partially_satisfied(self, offer, basket):
        """
        Determine if the basket partially meets the condition.  This is useful
        for up-selling messages to entice customers to buy something more in
        order to qualify for an offer.
        """
        return False

    def get_upsell_message(self, offer, basket):
        return None

    def can_apply_condition(self, line):
        """
        Determines whether the condition can be applied to a given basket line
        """
        if not line.stockrecord_id:
            return False
        product = line.product
        return self.range.contains_product(product) and product.is_discountable

    def get_applicable_lines(self, offer, basket, most_expensive_first=True):
        """
        Return line data for the lines that can be consumed by this condition
        """
        line_tuples = []
        for line in basket.all_lines():
            if not self.can_apply_condition(line):
                continue

            if price := unit_price(offer, line):
                line_tuples.append((price, line))
        key = operator.itemgetter(0)
        if most_expensive_first:
            return sorted(line_tuples, reverse=True, key=key)
        return sorted(line_tuples, key=key)


class Range(AbstractRange):
    name = models.CharField(_("Name"), max_length=128, unique=True)
    slug = fields.AutoSlugField(
        _("Slug"), max_length=128, unique=True, populate_from="name"
    )

    description = models.TextField(blank=True)

    # Whether this range is public
    is_public = models.BooleanField(
        _("Is public?"),
        default=False,
        help_text=_("Public ranges have a customer-facing page"),
    )

    includes_all_products = models.BooleanField(
        _("Includes all products?"), default=False
    )

    included_products = models.ManyToManyField(
        "catalogue.Product",
        related_name="includes",
        blank=True,
        verbose_name=_("Included Products"),
        through="offer.RangeProduct",
    )
    excluded_products = models.ManyToManyField(
        "catalogue.Product",
        related_name="excludes",
        blank=True,
        verbose_name=_("Excluded Products"),
    )
    classes = models.ManyToManyField(
        "catalogue.ProductClass",
        related_name="classes",
        blank=True,
        verbose_name=_("Product Types"),
    )
    included_categories = models.ManyToManyField(
        "catalogue.Category",
        related_name="includes",
        blank=True,
        verbose_name=_("Included Categories"),
    )

    # Allow a custom range instance to be specified
    proxy_class = fields.NullCharField(
        _("Custom class"), max_length=255, default=None, unique=True
    )

    date_created = models.DateTimeField(_("Date Created"), auto_now_add=True)

    objects = RangeManager()
    browsable = BrowsableRangeManager()


class RangeProduct(AbstractRangeProduct):
    range = models.ForeignKey("offer.Range", on_delete=models.CASCADE)
    product = models.ForeignKey("catalogue.Product", on_delete=models.CASCADE)
    display_order = models.IntegerField(default=0)


class RangeProductFileUpload(AbstractRangeProductFileUpload):
    range = models.ForeignKey(
        "offer.Range",
        on_delete=models.CASCADE,
        related_name="file_uploads",
        verbose_name=_("Range"),
    )
    filepath = models.CharField(_("File Path"), max_length=255)
    size = models.PositiveIntegerField(_("Size"))
    uploaded_by = models.ForeignKey(
        AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name=_("Uploaded By")
    )
    date_uploaded = models.DateTimeField(
        _("Date Uploaded"), auto_now_add=True, db_index=True
    )

    PENDING, FAILED, PROCESSED = "Pending", "Failed", "Processed"
    choices = (
        (PENDING, PENDING),
        (FAILED, FAILED),
        (PROCESSED, PROCESSED),
    )
    status = models.CharField(
        _("Status"), max_length=32, choices=choices, default=PENDING
    )
    error_message = models.CharField(_("Error Message"), max_length=255, blank=True)

    # Post-processing audit fields
    date_processed = models.DateTimeField(_("Date Processed"), null=True)
    num_new_skus = models.PositiveIntegerField(_("Number of New SKUs"), null=True)
    num_unknown_skus = models.PositiveIntegerField(
        _("Number of Unknown SKUs"), null=True
    )
    num_duplicate_skus = models.PositiveIntegerField(
        _("Number of Duplicate SKUs"), null=True
    )


class CountConditionModify(Condition):
    """
    An offer condition dependent on the NUMBER of matching items from the
    basket.
    """

    _description = _("Basket includes %(count)d item(s) from %(range)s")

    @property
    def name(self):
        return self._description % {
            "count": self.value,
            "range": str(self.range).lower(),
        }

    @property
    def description(self):
        return self._description % {
            "count": self.value,
            "range": range_anchor(self.range),
        }

    class Meta:
        app_label = "offer"
        proxy = True
        verbose_name = _("Count condition")
        verbose_name_plural = _("Count conditions")

    def is_satisfied(self, offer, basket):
        """
        Determines whether a given basket meets this condition
        """
        num_matches = 0
        for line in basket.all_lines():
            if self.can_apply_condition(line):
                num_matches += line.quantity_without_offer_discount(offer)
            if num_matches >= self.value:
                return True
        return False

    def _get_num_matches(self, basket, offer):
        if hasattr(self, "_num_matches"):
            return getattr(self, "_num_matches")
        num_matches = sum(
            line.quantity_available_for_offer(offer)
            for line in basket.all_lines()
            if self.can_apply_condition(line)
        )
        # pylint: disable=W0201
        self._num_matches = num_matches
        return num_matches

    def is_partially_satisfied(self, offer, basket):
        num_matches = self._get_num_matches(basket, offer)
        return 0 < num_matches < self.value

    def get_upsell_message(self, offer, basket):
        num_matches = self._get_num_matches(basket, offer)
        delta = self.value - num_matches
        if delta > 0:
            return ngettext(
                "Buy %(delta)d more product from %(range)s",
                "Buy %(delta)d more products from %(range)s",
                int(delta),
            ) % {"delta": delta, "range": self.range}
        return None

    def consume_items(self, offer, basket, affected_lines):
        """
        Marks items within the basket lines as consumed so they
        can't be reused in other offers.

        :basket: The basket
        :affected_lines: The lines that have been affected by the discount.
                         This should be list of tuples (line, discount, qty)
        """
        num_consumed = sum(quantity for line, __, quantity in affected_lines)
        to_consume = max(0, self.value - num_consumed)
        if to_consume == 0:
            return

        for __, line in self.get_applicable_lines(
            offer, basket, most_expensive_first=True
        ):
            num_consumed = line.consume(to_consume, offer=offer)
            to_consume -= num_consumed
            if to_consume == 0:
                break


class CoverageConditionModify(Condition):
    """
    An offer condition dependent on the number of DISTINCT matching items from
    the basket.
    """

    _description = _("Basket includes %(count)d distinct item(s) from %(range)s")

    @property
    def name(self):
        return self._description % {
            "count": self.value,
            "range": str(self.range).lower(),
        }

    @property
    def description(self):
        return self._description % {
            "count": self.value,
            "range": range_anchor(self.range),
        }

    class Meta:
        app_label = "offer"
        proxy = True
        verbose_name = _("Coverage Condition")
        verbose_name_plural = _("Coverage Conditions")

    def is_satisfied(self, offer, basket):
        """
        Determines whether a given basket meets this condition
        """
        covered_ids = []
        for line in basket.all_lines():
            if not line.is_available_for_offer_discount(offer):
                continue
            product = line.product
            if self.can_apply_condition(line) and product.id not in covered_ids:
                covered_ids.append(product.id)
            if len(covered_ids) >= self.value:
                return True
        return False

    def _get_num_covered_products(self, basket, offer):
        covered_ids = set()
        for line in basket.all_lines():
            product = line.product
            if (
                self.can_apply_condition(line)
                and line.quantity_available_for_offer(offer) > 0
            ):
                covered_ids.add(product.id)
        return len(covered_ids)

    def get_upsell_message(self, offer, basket):
        delta = self.value - self._get_num_covered_products(basket, offer)
        if delta > 0:
            return ngettext(
                "Buy %(delta)d more product from %(range)s",
                "Buy %(delta)d more products from %(range)s",
                int(delta),
            ) % {"delta": delta, "range": self.range}
        return None

    def is_partially_satisfied(self, offer, basket):
        return 0 < self._get_num_covered_products(basket, offer) < self.value

    def consume_items(self, offer, basket, affected_lines):
        """
        Marks items within the basket lines as consumed so they
        can't be reused in other offers.
        """
        consumed_products = [line.product for line, __, quantity in affected_lines]
        to_consume = max(0, self.value - len(consumed_products))
        if to_consume == 0:
            return

        for line in basket.all_lines():
            product = line.product
            if not self.can_apply_condition(line):
                continue
            if product in consumed_products:
                continue
            if not line.is_available_for_offer_discount(offer):
                continue
            # Only consume a quantity of 1 from each line
            line.consume(1, offer=offer)
            consumed_products.append(product)
            to_consume -= 1
            if to_consume == 0:
                break

    def get_value_of_satisfying_items(self, offer, basket):
        covered_ids = []
        value = D("0.00")
        for line in basket.all_lines():
            if self.can_apply_condition(line) and line.product.id not in covered_ids:
                covered_ids.append(line.product.id)
                value += unit_price(offer, line)
            if len(covered_ids) >= self.value:
                return value
        return value


class ValueConditionModify(Condition):
    """
    An offer condition dependent on the VALUE of matching items from the
    basket.
    """

    _description = _("Basket includes %(amount)s from %(range)s")

    @property
    def name(self):
        return self._description % {
            "amount": currency(self.value),
            "range": str(self.range).lower(),
        }

    @property
    def description(self):
        return self._description % {
            "amount": currency(self.value),
            "range": range_anchor(self.range),
        }

    class Meta:
        app_label = "offer"
        proxy = True
        verbose_name = _("Value condition")
        verbose_name_plural = _("Value conditions")

    def is_satisfied(self, offer, basket):
        """
        Determine whether a given basket meets this condition
        """
        value_of_matches = D("0.00")
        for line in basket.all_lines():
            if (
                self.can_apply_condition(line)
                and line.quantity_without_offer_discount(offer) > 0
            ):
                price = unit_price(offer, line)
                value_of_matches += price * int(
                    line.quantity_without_offer_discount(offer)
                )
            if value_of_matches >= self.value:
                return True
        return False

    def _get_value_of_matches(self, offer, basket):
        if hasattr(self, "_value_of_matches"):
            return getattr(self, "_value_of_matches")
        value_of_matches = D("0.00")
        for line in basket.all_lines():
            if self.can_apply_condition(line):
                price = unit_price(offer, line)
                value_of_matches += price * int(
                    line.quantity_available_for_offer(offer)
                )
        # pylint: disable=W0201
        self._value_of_matches = value_of_matches
        return value_of_matches

    def is_partially_satisfied(self, offer, basket):
        value_of_matches = self._get_value_of_matches(offer, basket)
        return D("0.00") < value_of_matches < self.value

    def get_upsell_message(self, offer, basket):
        value_of_matches = self._get_value_of_matches(offer, basket)
        delta = self.value - value_of_matches
        if delta > 0:
            return _("Spend %(value)s more from %(range)s") % {
                "value": currency(delta, basket.currency),
                "range": self.range,
            }
        return None

    def consume_items(self, offer, basket, affected_lines):
        """
        Marks items within the basket lines as consumed so they
        can't be reused in other offers.

        We allow lines to be passed in as sometimes we want them sorted
        in a specific order.
        """
        # Determine value of items already consumed as part of discount
        value_consumed = D("0.00")
        for line, __, qty in affected_lines:
            price = unit_price(offer, line)
            value_consumed += price * qty

        to_consume = max(0, self.value - value_consumed)
        if to_consume == 0:
            return

        for price, line in self.get_applicable_lines(
            offer, basket, most_expensive_first=True
        ):
            quantity_to_consume = min(
                line.quantity_without_offer_discount(offer),
                (to_consume / price).quantize(D(1), ROUND_UP),
            )
            line.consume(quantity_to_consume, offer=offer)
            to_consume -= price * quantity_to_consume
            if to_consume <= 0:
                break


def apply_discount(line, discount, quantity, offer=None, incl_tax=None):
    """
    Apply a given discount to the passed basket
    """
    # use OSCAR_OFFERS_INCL_TAX setting if incl_tax is left unspecified.
    incl_tax = incl_tax if incl_tax is not None else settings.OSCAR_OFFERS_INCL_TAX
    line.discount(discount, quantity, incl_tax=incl_tax, offer=offer)


class PercentageDiscountBenefitModify(Benefit):
    """
    An offer benefit that gives a percentage discount
    """

    _description = _("%(value)s%% discount on %(range)s")

    @property
    def name(self):
        return self._description % {"value": self.value, "range": self.range.name}

    @property
    def description(self):
        return self._description % {
            "value": self.value,
            "range": range_anchor(self.range),
        }

    class Meta:
        app_label = "offer"
        proxy = True
        verbose_name = _("Percentage discount benefit")
        verbose_name_plural = _("Percentage discount benefits")

    # pylint: disable=unused-argument
    def apply(
        self,
        basket,
        condition,
        offer,
        discount_percent=None,
        max_total_discount=None,
        **kwargs,
    ):
        if discount_percent is None:
            discount_percent = self.value

        discount_amount_available = max_total_discount

        line_tuples = self.get_applicable_lines(offer, basket)
        discount_percent = min(discount_percent, D("100.0"))
        discount = D("0.00")
        affected_items = 0
        max_affected_items = self._effective_max_affected_items()
        for price, line in line_tuples:
            affected_items += line.quantity_with_offer_discount(offer)
            if affected_items >= max_affected_items:
                break
            if discount_amount_available == 0:
                break

            quantity_affected = min(
                line.quantity_without_offer_discount(offer),
                max_affected_items - affected_items,
            )
            if quantity_affected <= 0:
                break

            line_discount = self.round(
                discount_percent / D("100.0") * price * int(quantity_affected),
                basket.currency,
            )

            if discount_amount_available is not None:
                line_discount = min(line_discount, discount_amount_available)
                discount_amount_available -= line_discount

            apply_discount(line, line_discount, quantity_affected, offer)

            affected_items += quantity_affected
            discount += line_discount

        return BasketDiscount(discount)


class AbsoluteDiscountBenefitModify(Benefit):
    """
    An offer benefit that gives an absolute discount
    """

    _description = _("%(value)s discount on %(range)s")

    @property
    def name(self):
        return self._description % {
            "value": currency(self.value),
            "range": self.range.name.lower(),
        }

    @property
    def description(self):
        return self._description % {
            "value": currency(self.value),
            "range": range_anchor(self.range),
        }

    class Meta:
        app_label = "offer"
        proxy = True
        verbose_name = _("Absolute discount benefit")
        verbose_name_plural = _("Absolute discount benefits")

    def apply(
        self,
        basket,
        condition,
        offer,
        discount_amount=None,
        max_total_discount=None,
        **kwargs,
    ):
        if discount_amount is None:
            discount_amount = self.value

        # Fetch basket lines that are in the range and available to be used in
        # an offer.
        line_tuples = self.get_applicable_lines(offer, basket)

        # Determine which lines can have the discount applied to them
        max_affected_items = self._effective_max_affected_items()
        num_affected_items = 0
        affected_items_total = D("0.00")
        lines_to_discount = []
        for price, line in line_tuples:
            if num_affected_items >= max_affected_items:
                break
            qty = min(
                line.quantity_without_offer_discount(offer),
                max_affected_items - num_affected_items,
            )
            lines_to_discount.append((line, price, qty))
            num_affected_items += qty
            affected_items_total += qty * price

        # Ensure we don't try to apply a discount larger than the total of the
        # matching items.
        discount = min(discount_amount, affected_items_total)
        if max_total_discount is not None:
            discount = min(discount, max_total_discount)

        if discount == 0:
            return ZERO_DISCOUNT

        # spreading the discount is a policy decision that may not apply

        # Apply discount equally amongst them
        applied_discount = D("0.00")
        last_line_idx = len(lines_to_discount) - 1
        for i, (line, price, qty) in enumerate(lines_to_discount):
            if i == last_line_idx:
                # If last line, then take the delta as the discount to ensure
                # the total discount is correct and doesn't mismatch due to
                # rounding.
                line_discount = discount - applied_discount
            else:
                # Calculate a weighted discount for the line
                line_discount = self.round(
                    ((price * qty) / affected_items_total) * discount, basket.currency
                )
            apply_discount(line, line_discount, qty, offer)
            applied_discount += line_discount

        return BasketDiscount(discount)


class FixedUnitDiscountBenefitModify(AbsoluteDiscountBenefitModify):
    """
    An offer benefit that gives an absolute discount on each applicable product.
    """

    class Meta:
        app_label = "offer"
        proxy = True
        verbose_name = _("Fixed unit discount benefit")
        verbose_name_plural = _("Fixed unit discount benefits")

    def get_lines_to_discount(self, offer, line_tuples):
        # Determine which lines can have the discount applied to them
        max_affected_items = self._effective_max_affected_items()
        num_affected_items = 0
        lines_to_discount = []
        for price, line in line_tuples:
            if num_affected_items >= max_affected_items:
                break
            qty = min(
                line.quantity_without_offer_discount(offer),
                max_affected_items - num_affected_items,
            )
            lines_to_discount.append((line, price, qty))
            num_affected_items += qty
        return lines_to_discount

    def apply(
        self,
        basket,
        condition,
        offer,
        discount_amount=None,
        max_total_discount=None,
        **kwargs,
    ):
        # Fetch basket lines that are in the range and available to be used in an offer.
        line_tuples = self.get_applicable_lines(offer, basket)
        lines_to_discount = self.get_lines_to_discount(offer, line_tuples)

        applied_discount = D("0.00")
        for line, price, qty in lines_to_discount:
            # If price is less than the fixed discount, then it will be free.
            line_discount = min(price * qty, self.value * qty)
            apply_discount(line, line_discount, qty, offer)
            applied_discount += line_discount

        return BasketDiscount(applied_discount)


class FixedPriceBenefitModify(Benefit):
    """
    An offer benefit that gives the items in the condition for a
    fixed price.  This is useful for "bundle" offers.

    Note that we ignore the benefit range here and only give a fixed price
    for the products in the condition range.  The condition cannot be a value
    condition.

    We also ignore the max_affected_items setting.
    """

    _description = _("The products that meet the condition are sold for %(amount)s")

    @property
    def name(self):
        return self._description % {"amount": currency(self.value)}

    class Meta:
        app_label = "offer"
        proxy = True
        verbose_name = _("Fixed price benefit")
        verbose_name_plural = _("Fixed price benefits")

    def apply(self, basket, condition, offer, **kwargs):
        if isinstance(condition, ValueConditionModify):
            return ZERO_DISCOUNT

        # Fetch basket lines that are in the range and available to be used in
        # an offer.
        line_tuples = self.get_applicable_lines(offer, basket, range=condition.range)
        if not line_tuples:
            return ZERO_DISCOUNT

        # Determine the lines to consume
        num_permitted = int(condition.value)
        num_affected = 0
        value_affected = D("0.00")
        covered_lines = []
        for price, line in line_tuples:
            if isinstance(condition, CoverageConditionModify):
                quantity_affected = 1
            else:
                quantity_affected = min(
                    line.quantity_without_offer_discount(offer),
                    num_permitted - num_affected,
                )
            num_affected += quantity_affected
            value_affected += quantity_affected * price
            covered_lines.append((price, line, quantity_affected))
            if num_affected >= num_permitted:
                break
        discount = max(value_affected - self.value, D("0.00"))
        if not discount:
            return ZERO_DISCOUNT

        # Apply discount to the affected lines
        discount_applied = D("0.00")
        last_line = covered_lines[-1][1]
        for price, line, quantity in covered_lines:
            if line == last_line:
                # If last line, we just take the difference to ensure that
                # rounding doesn't lead to an off-by-one error
                line_discount = discount - discount_applied
            else:
                line_discount = self.round(
                    discount * (price * quantity) / value_affected, basket.currency
                )
            apply_discount(line, line_discount, quantity, offer)
            discount_applied += line_discount

        return BasketDiscount(discount)


class MultibuyDiscountBenefitModify(Benefit):
    _description = _("Cheapest product from %(range)s is free")

    @property
    def name(self):
        return self._description % {"range": self.range.name.lower()}

    @property
    def description(self):
        return self._description % {"range": range_anchor(self.range)}

    class Meta:
        app_label = "offer"
        proxy = True
        verbose_name = _("Multibuy discount benefit")
        verbose_name_plural = _("Multibuy discount benefits")

    def apply(self, basket, condition, offer, **kwargs):
        line_tuples = self.get_applicable_lines(offer, basket)
        if not line_tuples:
            return ZERO_DISCOUNT

        # Cheapest line gives free product
        discount, line = line_tuples[0]
        if line.quantity_with_offer_discount(offer) == 0:
            apply_discount(line, discount, 1, offer)

            affected_lines = [(line, discount, 1)]
            condition.consume_items(offer, basket, affected_lines)

            return BasketDiscount(discount)
        else:
            return ZERO_DISCOUNT


# =================
# Shipping benefits
# =================


class ShippingBenefitModify(Benefit):
    def apply(self, basket, condition, offer, **kwargs):
        condition.consume_items(offer, basket, affected_lines=())
        return SHIPPING_DISCOUNT

    class Meta:
        app_label = "offer"
        proxy = True


class ShippingAbsoluteDiscountBenefitModify(ShippingBenefitModify):
    _description = _("%(amount)s off shipping cost")

    @property
    def name(self):
        return self._description % {"amount": currency(self.value)}

    class Meta:
        app_label = "offer"
        proxy = True
        verbose_name = _("Shipping absolute discount benefit")
        verbose_name_plural = _("Shipping absolute discount benefits")

    def shipping_discount(self, charge, currency=None):
        return min(charge, self.value)


class ShippingFixedPriceBenefitModify(ShippingBenefitModify):
    _description = _("Get shipping for %(amount)s")

    @property
    def name(self):
        return self._description % {"amount": currency(self.value)}

    class Meta:
        app_label = "offer"
        proxy = True
        verbose_name = _("Fixed price shipping benefit")
        verbose_name_plural = _("Fixed price shipping benefits")

    def shipping_discount(self, charge, currency=None):
        return D("0.00") if charge < self.value else charge - self.value


class ShippingPercentageDiscountBenefitModify(ShippingBenefitModify):
    _description = _("%(value)s%% off of shipping cost")

    @property
    def name(self):
        return self._description % {"value": self.value}

    class Meta:
        app_label = "offer"
        proxy = True
        verbose_name = _("Shipping percentage discount benefit")
        verbose_name_plural = _("Shipping percentage discount benefits")

    def shipping_discount(self, charge, currency=None):
        discount = charge * self.value / D("100.0")
        return discount.quantize(D("0.01"))
