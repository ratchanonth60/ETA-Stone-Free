from django.utils.translation import gettext_lazy as _
from oscar.core.application import OscarConfig


class AnalyticsConfig(OscarConfig):
    label = "analytics"
    name = "ecommerce.apps.analytics"
    verbose_name = _("Analytics")

    def ready(self):
        from oscar.apps.analytics import receivers  # noqa
