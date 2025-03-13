from django.utils.translation import gettext_lazy as _
from oscar.core.application import OscarConfig


class TenantConfig(OscarConfig):
    label = "Tenant"
    name = "ecommerce.core.tenants"
    verbose_name = _("Tenant")
