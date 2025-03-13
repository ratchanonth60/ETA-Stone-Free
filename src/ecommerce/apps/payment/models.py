import datetime
from decimal import Decimal

import stripe
from django.db import models
from django.utils.translation import gettext_lazy as _
from oscar.apps.payment.abstract_models import (
    AbstractSource,
    AbstractSourceType,
    AbstractTransaction,
)
from oscar.core.compat import AUTH_USER_MODEL
from oscar.core.utils import get_default_currency
from oscar.templatetags.currency_filters import currency


class Transaction(AbstractTransaction):
    source = models.ForeignKey(
        "payment.Source",
        on_delete=models.CASCADE,
        related_name="transactions",
        verbose_name=_("Source"),
    )
    txn_type = models.CharField(_("Type"), max_length=128, blank=True)

    amount = models.DecimalField(_("Amount"), decimal_places=2, max_digits=12)
    reference = models.CharField(_("Reference"), max_length=128, blank=True)
    status = models.CharField(_("Status"), max_length=128, blank=True)
    date_created = models.DateTimeField(
        _("Date Created"), auto_now_add=True, db_index=True
    )


class Source(AbstractSource):
    order = models.ForeignKey(
        "order.Order",
        on_delete=models.CASCADE,
        related_name="sources",
        verbose_name=_("Order"),
    )
    source_type = models.ForeignKey(
        "payment.SourceType",
        on_delete=models.CASCADE,
        related_name="sources",
        verbose_name=_("Source Type"),
    )
    currency = models.CharField(
        _("Currency"), max_length=12, default=get_default_currency
    )

    # Track the various amounts associated with this source
    amount_allocated = models.DecimalField(
        _("Amount Allocated"), decimal_places=2, max_digits=12, default=Decimal("0.00")
    )
    amount_debited = models.DecimalField(
        _("Amount Debited"), decimal_places=2, max_digits=12, default=Decimal("0.00")
    )
    amount_refunded = models.DecimalField(
        _("Amount Refunded"), decimal_places=2, max_digits=12, default=Decimal("0.00")
    )

    # Reference number for this payment source.  This is often used to look up
    # a transaction model for a particular payment partner.
    reference = models.CharField(_("Reference"), max_length=255, blank=True)

    # A customer-friendly label for the source, eg XXXX-XXXX-XXXX-1234
    label = models.CharField(_("Label"), max_length=128, blank=True)

    def __str__(self):
        description = _("Allocation of %(amount)s from type %(type)s") % {
            "amount": currency(self.amount_allocated, self.currency),
            "type": self.source_type,
        }
        if self.reference:
            description += _(" (reference: %s)") % self.reference
        return description

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.deferred_txns:
            for txn in self.deferred_txns:
                self._create_transaction(*txn)

    def create_deferred_transaction(
        self, txn_type, amount, reference=None, status=None
    ):
        """
        Register the data for a transaction that can't be created yet due to FK
        constraints.  This happens at checkout where create an payment source
        and a transaction but can't save them until the order model exists.
        """
        if self.deferred_txns is None:
            self.deferred_txns = []
        self.deferred_txns.append((txn_type, amount, reference, status))

    def _create_transaction(self, txn_type, amount, reference="", status=""):
        self.transactions.create(
            txn_type=txn_type, amount=amount, reference=reference, status=status
        )

    # =======
    # Actions
    # =======

    def allocate(self, amount, reference="", status=""):
        """
        Convenience method for ring-fencing money against this source
        """
        self.amount_allocated += amount
        self.save()
        self._create_transaction(
            AbstractTransaction.AUTHORISE, amount, reference, status
        )

    allocate.alters_data = True

    def debit(self, amount=None, reference="", status=""):
        """
        Convenience method for recording debits against this source
        """
        if amount is None:
            amount = self.balance
        self.amount_debited += amount
        self.save()
        self._create_transaction(AbstractTransaction.DEBIT, amount, reference, status)

    debit.alters_data = True

    def refund(self, amount, reference="", status=""):
        """
        Convenience method for recording refunds against this source
        """
        self.amount_refunded += amount
        self.save()
        self._create_transaction(AbstractTransaction.REFUND, amount, reference, status)

    refund.alters_data = True

    # ==========
    # Properties
    # ==========

    @property
    def balance(self):
        """
        Return the balance of this source
        """
        return self.amount_allocated - self.amount_debited + self.amount_refunded

    @property
    def amount_available_for_refund(self):
        """
        Return the amount available to be refunded
        """
        return self.amount_debited - self.amount_refunded


class SourceType(AbstractSourceType):
    name = models.CharField(_("Name"), max_length=128, db_index=True)


class Bankcard(models.Model):
    user = models.ForeignKey(
        AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="bankcards",
        verbose_name=_("User"),
    )
    # Stripe specific fields
    stripe_card_id = models.CharField(
        _("Stripe Card ID"), max_length=255, blank=True, null=True
    )
    stripe_customer_id = models.CharField(
        _("Stripe Customer ID"), max_length=255, blank=True, null=True
    )

    card_type = models.CharField(_("Card Type"), max_length=128)
    last_4_digits = models.CharField(
        _("Last 4 digits"), max_length=4, blank=True, null=True
    )
    expiry_date = models.DateField(_("Expiry Date"), blank=True, null=True)

    class Meta:
        app_label = "payment"
        verbose_name = _("Bankcard")
        verbose_name_plural = _("Bankcards")

    def __str__(self):
        return _("%(card_type)s %(number)s (Expires: %(expiry)s)") % {
            "card_type": self.card_type,
            "number": self.obfuscated_number,
            "expiry": self.expiry_month(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Initialise the card-type
        # if self.id is None:
        #     self.card_type = bankcards.bankcard_type(self.number)
        #     if self.card_type is None:
        #         self.card_type = 'Unknown card type'

    @property
    def obfuscated_number(self):
        return f"XXXX-XXXX-XXXX-{self.last_4_digits}"

    @property
    def is_saved_to_stripe(self):
        return bool(self.stripe_card_id)

    def expiry_month(self, format="%m/%y"):
        return (
            self.expiry_date.strftime(format) if self.expiry_date is not None else "-"
        )

    def get_stripe_card(self):
        if self.stripe_customer_id and self.stripe_card_id:
            return stripe.Customer.retrieve_payment_method(
                self.stripe_customer_id, self.stripe_card_id
            )
        return None

    def update_card_details_from_stripe(self):
        if customer := self.get_stripe_card():
            self.card_type = customer.card.brand  # 'Visa', 'MasterCard', etc.
            self.last_4_digits = customer.card.last4
            self.expiry_date = datetime.date(
                customer.card.exp_year, customer.card.exp_month, 1
            )
            self.save()
