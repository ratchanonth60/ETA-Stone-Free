from django.utils.translation import gettext_lazy as _
from oscar.core.application import OscarConfig


class ShippingConfig(OscarConfig):
    label = "shipping"
    name = "ecommerce.apps.shipping"
    verbose_name = _("Shipping")

    namespace = "shipping"
