from django.utils.translation import gettext_lazy as _
from oscar.core.application import OscarConfig


class PartnerConfig(OscarConfig):
    label = "partner"
    name = "ecommerce.apps.partner"
    verbose_name = _("Partner")

    def ready(self):
        from oscar.apps.partner import receivers  # noqa
