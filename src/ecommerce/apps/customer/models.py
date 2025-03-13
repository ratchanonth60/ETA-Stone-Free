from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.translation import gettext_lazy as _
from oscar.apps.customer.abstract_models import AbstractProductAlert

AUTH_USER_MODEL = getattr(settings, "AUTH_USER_MODEL", "user.User")


class ProductAlert(AbstractProductAlert):
    product = models.ForeignKey("catalogue.Product", on_delete=models.CASCADE)

    # A user is only required if the notification is created by a
    # registered user, anonymous users will only have an email address
    # attached to the notification
    user = models.ForeignKey(
        AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name="alerts",
        verbose_name=_("User"),
    )
    email = models.EmailField(_("Email"), db_index=True, blank=True)

    # This key are used to confirm and cancel alerts for anon users
    key = models.CharField(_("Key"), max_length=128, blank=True, db_index=True)

    # An alert can have two different statuses for authenticated
    # users ``ACTIVE`` and ``CANCELLED`` and anonymous users have an
    # additional status ``UNCONFIRMED``. For anonymous users a confirmation
    # and unsubscription key are generated when an instance is saved for
    # the first time and can be used to confirm and unsubscribe the
    # notifications.
    UNCONFIRMED, ACTIVE, CANCELLED, CLOSED = (
        "Unconfirmed",
        "Active",
        "Cancelled",
        "Closed",
    )
    STATUS_CHOICES = (
        (UNCONFIRMED, _("Not yet confirmed")),
        (ACTIVE, _("Active")),
        (CANCELLED, _("Cancelled")),
        (CLOSED, _("Closed")),
    )
    status = models.CharField(
        _("Status"), max_length=20, choices=STATUS_CHOICES, default=ACTIVE
    )

    date_created = models.DateTimeField(
        _("Date created"), auto_now_add=True, db_index=True
    )
    date_confirmed = models.DateTimeField(_("Date confirmed"), blank=True, null=True)
    date_cancelled = models.DateTimeField(_("Date cancelled"), blank=True, null=True)
    date_closed = models.DateTimeField(_("Date closed"), blank=True, null=True)

    @property
    def is_anonymous(self):
        return self.user is None

    @property
    def can_be_confirmed(self):
        return self.status == self.UNCONFIRMED

    @property
    def can_be_cancelled(self):
        return self.status in (self.ACTIVE, self.UNCONFIRMED)

    @property
    def is_cancelled(self):
        return self.status == self.CANCELLED

    @property
    def is_active(self):
        return self.status == self.ACTIVE

    def confirm(self):
        self.status = self.ACTIVE
        self.date_confirmed = timezone.now()
        self.save()
    confirm.alters_data = True

    def cancel(self):
        self.status = self.CANCELLED
        self.date_cancelled = timezone.now()
        self.save()
    cancel.alters_data = True

    def close(self):
        self.status = self.CLOSED
        self.date_closed = timezone.now()
        self.save()
    close.alters_data = True

    def get_email_address(self):
        return self.user.email if self.user else self.email

    def save(self, *args, **kwargs):
        if not self.id and not self.user:
            self.key = self.get_random_key()
            self.status = self.UNCONFIRMED
        # Ensure date fields get updated when saving from modelform (which just
        # calls save, and doesn't call the methods cancel(), confirm() etc).
        if self.status == self.CANCELLED and self.date_cancelled is None:
            self.date_cancelled = timezone.now()
        if not self.user and self.status == self.ACTIVE \
                and self.date_confirmed is None:
            self.date_confirmed = timezone.now()
        if self.status == self.CLOSED and self.date_closed is None:
            self.date_closed = timezone.now()

        return super().save(*args, **kwargs)

    def get_random_key(self):
        return get_random_string(length=40, allowed_chars='abcdefghijklmnopqrstuvwxyz0123456789')

    def get_confirm_url(self):
        return reverse('customer:alerts-confirm', kwargs={'key': self.key})

    def get_cancel_url(self):
        return reverse('customer:alerts-cancel-by-key', kwargs={'key': self.key})
