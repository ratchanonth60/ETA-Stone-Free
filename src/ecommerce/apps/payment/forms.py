import re
from calendar import monthrange
from datetime import date

from django import forms
from django.conf import settings
from django.core import validators
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import gettext_lazy as _
from oscar.apps.address.forms import AbstractAddressForm
from oscar.forms.mixins import PhoneNumberMixin

from ecommerce.apps.address.models import Country
from ecommerce.apps.order.models import BillingAddress

from . import bankcards
from .models import Bankcard

# List of card names for all the card types supported in payment.bankcards
VALID_CARDS = {card_type[0] for card_type in bankcards.CARD_TYPES}


class BankcardNumberField(forms.CharField):
    def __init__(self, *args, **kwargs):
        _kwargs = {
            "max_length": 20,
            "widget": forms.TextInput(attrs={"autocomplete": "off"}),
            "label": _("Card number"),
        }
        if "types" in kwargs:
            self.accepted_cards = set(kwargs.pop("types"))
            if difference := self.accepted_cards - VALID_CARDS:
                raise ImproperlyConfigured(
                    f"The following accepted_cards are unknown: {difference}"
                )

        _kwargs |= kwargs
        super().__init__(*args, **_kwargs)

    def clean(self, value):
        """
        Check if given CC number is valid and one of the
        card types we accept
        """
        non_decimal = re.compile(r"\D+")
        value = non_decimal.sub("", (value or "").strip())

        if value and not bankcards.luhn(value):
            raise forms.ValidationError(_("Please enter a valid credit card number."))

        if hasattr(self, "accepted_cards"):
            card_type = bankcards.bankcard_type(value)
            if card_type not in self.accepted_cards:
                raise forms.ValidationError(_(f"{card_type} cards are not accepted."))

        return super().clean(value)


class BankcardMonthWidget(forms.MultiWidget):
    """
    Widget containing two select boxes for selecting the month and year
    """

    def decompress(self, value):
        return [value.month, value.year] if value else [None, None]

    def format_output(self, rendered_widgets):
        html = " ".join(rendered_widgets)
        return f'<span style="white-space: nowrap">{html}</span>'


class BankcardMonthField(forms.MultiValueField):
    """
    A modified version of the snippet: http://djangosnippets.org/snippets/907/
    """

    default_error_messages = {
        "invalid_month": _("Enter a valid month."),
        "invalid_year": _("Enter a valid year."),
    }
    NUM_YEARS = 5

    def __init__(self, *args, **kwargs):
        # Allow the number of years to be specified
        if "num_years" in kwargs:
            self.NUM_YEARS = kwargs.pop("num_years")

        errors = self.default_error_messages.copy()
        if "error_messages" in kwargs:
            errors.update(kwargs["error_messages"])

        fields = (
            forms.ChoiceField(
                choices=self.month_choices(),
                error_messages={"invalid": errors["invalid_month"]},
            ),
            forms.ChoiceField(
                choices=self.year_choices(),
                error_messages={"invalid": errors["invalid_year"]},
            ),
        )
        if "widget" not in kwargs:
            kwargs["widget"] = BankcardMonthWidget(
                widgets=[fields[0].widget, fields[1].widget]
            )
        super().__init__(fields, *args, **kwargs)

    def month_choices(self):
        return []

    def year_choices(self):
        return []


class BankcardExpiryMonthField(BankcardMonthField):
    NUM_YEARS = 15

    def __init__(self, *args, **kwargs):
        today = date.today()
        _kwargs = {
            "required": True,
            "label": _("Valid to"),
            "initial": ["%.2d" % today.month, today.year],
        } | kwargs
        super().__init__(*args, **_kwargs)

    def month_choices(self):
        return [("%.2d" % x, "%.2d" % x) for x in range(1, 13)]

    def year_choices(self):
        return [
            (x, x) for x in range(date.today().year, date.today().year + self.NUM_YEARS)
        ]

    def clean(self, value):
        expiry_date = super().clean(value)
        if expiry_date and date.today() > expiry_date:
            raise forms.ValidationError(
                _("The expiration date you entered is in the past.")
            )
        return expiry_date

    def compress(self, data_list):
        if data_list:
            if data_list[1] in validators.EMPTY_VALUES:
                error = self.error_messages["invalid_year"]
                raise forms.ValidationError(error)
            if data_list[0] in validators.EMPTY_VALUES:
                error = self.error_messages["invalid_month"]
                raise forms.ValidationError(error)
            year = int(data_list[1])
            month = int(data_list[0])
            # find last day of the month
            day = monthrange(year, month)[1]
            return date(year, month, day)
        return None


class BankcardStartingMonthField(BankcardMonthField):
    def __init__(self, *args, **kwargs):
        _kwargs = {
            "required": False,
            "label": _("Valid from"),
        } | kwargs
        super().__init__(*args, **_kwargs)

    def month_choices(self):
        months = [("%.2d" % x, "%.2d" % x) for x in range(1, 13)]
        months.insert(0, ("", "--"))
        return months

    def year_choices(self):
        today = date.today()
        years = [(x, x) for x in range(today.year - self.NUM_YEARS, today.year + 1)]
        years.insert(0, ("", "--"))
        return years

    def clean(self, value):
        starting_date = super().clean(value)
        if starting_date and date.today() < starting_date:
            raise forms.ValidationError(
                _("The starting date you entered is in the future.")
            )
        return starting_date

    def compress(self, data_list):
        if data_list:
            if data_list[1] in validators.EMPTY_VALUES:
                error = self.error_messages["invalid_year"]
                raise forms.ValidationError(error)
            if data_list[0] in validators.EMPTY_VALUES:
                error = self.error_messages["invalid_month"]
                raise forms.ValidationError(error)
            year = int(data_list[1])
            month = int(data_list[0])
            return date(year, month, 1)
        return None


class BankcardCCVField(forms.RegexField):
    def __init__(self, *args, **kwargs):
        _kwargs = {
            "required": True,
            "label": _("CCV number"),
            "widget": forms.TextInput(attrs={"size": "5"}),
            "error_messages": {"invalid": _("Please enter a 3 or 4 digit number")},
            "help_text": _(
                "This is the 3 or 4 digit security number "
                "on the back of your bankcard"
            ),
        } | kwargs
        super().__init__(r"^\d{3,4}$", *args, **_kwargs)

    def clean(self, value):
        if value is not None:
            value = value.strip()
        return super().clean(value)


# class BankcardForm(forms.ModelForm):
#     # By default, this number field will accept any number. The only validation
#     # is whether it passes the luhn check. If you wish to only accept certain
#     # types of card, you can pass a types kwarg to BankcardNumberField, e.g.
#     #
#     # BankcardNumberField(types=[bankcards.VISA, bankcards.VISA_ELECTRON,])

#     number = BankcardNumberField()
#     ccv = BankcardCCVField()
#     # start_month = BankcardStartingMonthField()
#     expiry_month = BankcardExpiryMonthField()

#     def __init__(self, *args, **kwargs):
#         self.user = kwargs.pop('user', None)  # Get the 'user' and remove it from kwargs
#         super(BankcardForm, self).__init__(*args, **kwargs)

#     class Meta:
#         model = Bankcard
#         fields = ("number", "expiry_month", "ccv")

#     def clean(self):
#         data = self.cleaned_data
#         number, ccv = data.get("number"), data.get("ccv")
#         if number and ccv:
#             if bankcards.is_amex(number) and len(ccv) != 4:
#                 raise forms.ValidationError(
#                     _("American Express cards use a 4 digit security code")
#                 )
#         return data

#     def save(self, *args, **kwargs):
#         bankcard = Bankcard(
#             number=self.cleaned_data["number"],
#             expiry_date=self.cleaned_data["expiry_month"],
#             # start_date=self.cleaned_data["start_month"],
#             ccv=self.cleaned_data["ccv"],
#         )
#         bankcard.user = self.user
#         bankcard.save_to_stripe()
#         return bankcard

#     @property
#     def bankcard(self):
#         """
#         Return an instance of the Bankcard model (unsaved)
#         """
#         return Bankcard(
#             number=self.cleaned_data["number"],
#             expiry_date=self.cleaned_data["expiry_month"],
#             # start_date=self.cleaned_data["start_month"],
#             ccv=self.cleaned_data["ccv"],
#         )

class BankcardForm(forms.ModelForm):
    stripeToken = forms.CharField(widget=forms.HiddenInput())  # Add stripeToken field
    stripe_customer_id = forms.CharField(widget=forms.HiddenInput(), required=False)  # Add this line
    stripe_card_id = forms.CharField(widget=forms.HiddenInput(), required=False)  # Add this line
    expiry_date = forms.DateField(widget=forms.HiddenInput(), required=False)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)  # Get the 'user' and remove it from kwargs
        super(BankcardForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Bankcard
        fields = ("stripe_card_id", "stripe_customer_id", "expiry_date")  # Only stripeToken field is required

    def save(self, *args, **kwargs):
        bankcard = super(BankcardForm, self).save(commit=False)
        bankcard.user = self.user
        bankcard.save()
        return bankcard


class BillingAddressForm(PhoneNumberMixin, AbstractAddressForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_country_queryset()

    def set_country_queryset(self):
        self.fields["country"].queryset = Country._default_manager.all()

    class Meta:
        model = BillingAddress
        fields = [
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


class PaymentMethodForm(forms.Form):
    payment_option = forms.ChoiceField(
        label=_("Select other payment method"),
        required=False,
        widget=forms.RadioSelect()
    )

    def __init__(self, *args, **kwargs):
        # Retrieve bank cards from the user and add them to the choices.
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['payment_option'].choices = self.get_payment_options(user)

    def get_payment_options(self, user):
        # Start with other payment methods.
        choices = list(settings.OSCAR_PAYMENT_METHODS)
        # If user has bank cards, add them to the choices.
        if user:
            bankcards = user.bankcards.all()
            choices.extend(
                (
                    card.id,
                    f"{card.card_type} {card.obfuscated_number} ({card.expiry_month})",
                )
                for card in bankcards
            )
        return choices
