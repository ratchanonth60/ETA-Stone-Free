import datetime

from django import forms
from django.http import QueryDict
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy
from oscar.apps.address.forms import AbstractAddressForm
from oscar.forms.mixins import PhoneNumberMixin

from ecommerce.apps.order.models import Order, OrderNote, ShippingAddress
from ecommerce.apps.payment.models import SourceType
from ecommerce.forms.widgets import DatePickerInput


class OrderStatsForm(forms.Form):
    date_from = forms.DateField(
        required=False,
        label=pgettext_lazy("start date", "From"),
        widget=DatePickerInput,
    )
    date_to = forms.DateField(
        required=False, label=pgettext_lazy("end date", "To"), widget=DatePickerInput
    )

    _filters = _description = None

    def _determine_filter_metadata(self):
        self._filters = {}
        self._description = _("All orders")
        if self.errors:
            return

        date_from = self.cleaned_data["date_from"]
        date_to = self.cleaned_data["date_to"]
        if date_from and date_to:
            # We want to include end date so we adjust the date we use with the
            # 'range' function.
            self._filters = {
                "date_placed__range": [date_from, date_to + datetime.timedelta(days=1)]
            }
            self._description = _(
                "Orders placed between %(date_from)s and %(date_to)s"
            ) % {"date_from": date_from, "date_to": date_to}
        elif date_from:
            self._filters = {"date_placed__gte": date_from}
            self._description = _("Orders placed since %s") % (date_from,)
        elif date_to:
            self._filters = {"date_placed__lte": date_to}
            self._description = _("Orders placed until %s") % (date_to,)
        else:
            self._filters = {}
            self._description = _("All orders")

    def get_filters(self):
        if self._filters is None:
            self._determine_filter_metadata()
        return self._filters

    def get_filter_description(self):
        if self._description is None:
            self._determine_filter_metadata()
        return self._description


class OrderSearchForm(forms.Form):
    order_number = forms.CharField(required=False, label=_("Order number"))
    name = forms.CharField(required=False, label=_("Customer name"))
    product_title = forms.CharField(required=False, label=_("Product name"))
    upc = forms.CharField(required=False, label=_("UPC"))
    partner_sku = forms.CharField(required=False, label=_("Partner SKU"))

    status_choices = (("", "---------"),) + tuple(
        [(v, v) for v in Order.all_statuses()]
    )
    status = forms.ChoiceField(
        choices=status_choices, label=_("Status"), required=False
    )

    date_from = forms.DateField(
        required=False, label=_("Date from"), widget=DatePickerInput
    )
    date_to = forms.DateField(
        required=False, label=_("Date to"), widget=DatePickerInput
    )

    voucher = forms.CharField(required=False, label=_("Voucher code"))

    payment_method = forms.ChoiceField(
        label=_("Payment method"), required=False, choices=()
    )

    format_choices = (
        ("html", _("HTML")),
        ("csv", _("CSV")),
    )
    response_format = forms.ChoiceField(
        widget=forms.RadioSelect,
        required=False,
        choices=format_choices,
        initial="html",
        label=_("Get results as"),
    )

    def __init__(self, *args, **kwargs):
        # Ensure that 'response_format' is always set
        if "data" in kwargs:
            data = kwargs["data"]
            del kwargs["data"]
        elif len(args) > 0:
            data = args[0]
            args = args[1:]
        else:
            data = None

        if data and data.get("response_format", None) not in self.format_choices:
            if isinstance(data, QueryDict):
                data = data.dict()
            data["response_format"] = "html"

        super().__init__(data, *args, **kwargs)
        self.fields["payment_method"].choices = self.payment_method_choices()

    def payment_method_choices(self):
        return (("", "---------"),) + tuple(
            (src.code, src.name) for src in SourceType.objects.all()
        )


class OrderNoteForm(forms.ModelForm):
    class Meta:
        model = OrderNote
        fields = ["message"]

    def __init__(self, order, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.order = order
        self.instance.user = user


class ShippingAddressForm(PhoneNumberMixin, AbstractAddressForm):
    class Meta:
        model = ShippingAddress
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
            "phone_number",
            "notes",
        ]


class OrderStatusForm(forms.Form):
    new_status = forms.ChoiceField(label=_("New order status"), choices=())

    def __init__(self, order, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Set the choices
        choices = [(x, x) for x in order.available_statuses()]
        self.fields["new_status"].choices = choices

    @property
    def has_choices(self):
        return len(self.fields["new_status"].choices) > 0
