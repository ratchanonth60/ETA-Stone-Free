from django.utils.translation import gettext_lazy as _
from oscar.core.application import OscarConfig


class VoucherConfig(OscarConfig):
    label = "voucher"
    name = "ecommerce.apps.voucher"
    verbose_name = _("Voucher")

    def ready(self):
        from oscar.apps.voucher import receivers  # noqa
