from django.core.validators import RegexValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from oscar.apps.communication.abstract_models import (
    AbstractCommunicationEventType,
    AbstractEmail,
    AbstractNotification,
)
from oscar.apps.communication.managers import CommunicationTypeManager
from oscar.core.compat import AUTH_USER_MODEL
from oscar.models.fields import AutoSlugField

from ecommerce.core.defults import CATEGORY_COMMUNICATION_CHOICES


class Email(AbstractEmail):
    user = models.ForeignKey(
        AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="emails",
        verbose_name=_("User"),
        null=True,
    )
    email = models.EmailField(_("Email Address"), null=True, blank=True)
    subject = models.TextField(_("Subject"), max_length=255)
    body_text = models.TextField(_("Body Text"))
    body_html = models.TextField(_("Body HTML"), blank=True)
    date_sent = models.DateTimeField(_("Date Sent"), auto_now_add=True)


class CommunicationEventType(AbstractCommunicationEventType):
    code = AutoSlugField(
        _("Code"),
        max_length=128,
        unique=True,
        populate_from="name",
        separator="_",
        uppercase=True,
        editable=True,
        validators=[
            RegexValidator(
                regex=r"^[A-Z_][0-9A-Z_]*$",
                message=_(
                    "Code can only contain the uppercase letters (A-Z), "
                    "digits, and underscores, and can't start with a digit."
                ),
            )
        ],
        help_text=_("Code used for looking up this event programmatically"),
    )

    #: Name is the friendly description of an event for use in the admin
    name = models.CharField(_("Name"), max_length=255, db_index=True)

    # We allow communication types to be categorised
    # For backwards-compatibility, the choice values are quite verbose
    CATEGORY_CHOICES = CATEGORY_COMMUNICATION_CHOICES

    category = models.CharField(
        _("Category"), max_length=255, default="Order related", choices=CATEGORY_CHOICES
    )

    # Template content for emails
    # NOTE: There's an intentional distinction between None and ''. None
    # instructs Oscar to look for a file-based template, '' is just an empty
    # template.
    email_subject_template = models.CharField(
        _("Email Subject Template"), max_length=255, blank=True, null=True
    )
    email_body_template = models.TextField(
        _("Email Body Template"), blank=True, null=True
    )
    email_body_html_template = models.TextField(
        _("Email Body HTML Template"),
        blank=True,
        null=True,
        help_text=_("HTML template"),
    )

    # Template content for SMS messages
    sms_template = models.CharField(
        _("SMS Template"),
        max_length=170,
        blank=True,
        null=True,
        help_text=_("SMS template"),
    )

    date_created = models.DateTimeField(_("Date Created"), auto_now_add=True)
    date_updated = models.DateTimeField(_("Date Updated"), auto_now=True)

    objects = CommunicationTypeManager()

    # File templates
    email_subject_template_file = "eta/communication/emails/commtype_%s_subject.txt"
    email_body_template_file = "eta/communication/emails/commtype_%s_body.txt"
    email_body_html_template_file = "eta/communication/emails/commtype_%s_body.html"
    sms_template_file = "eta/communication/sms/commtype_%s_body.txt"


class Notification(AbstractNotification):
    recipient = models.ForeignKey(
        AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )

    # Not all notifications will have a sender.
    sender = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)

    # HTML is allowed in this field as it can contain links
    subject = models.CharField(max_length=255)
    body = models.TextField()

    INBOX, ARCHIVE = "Inbox", "Archive"
    choices = ((INBOX, _("Inbox")), (ARCHIVE, _("Archive")))
    location = models.CharField(max_length=32, choices=choices, default=INBOX)

    date_sent = models.DateTimeField(auto_now_add=True)
    date_read = models.DateTimeField(blank=True, null=True)
