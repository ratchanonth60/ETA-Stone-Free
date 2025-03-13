from django.utils.translation import gettext_lazy as _
from oscar.core.application import OscarConfig


class UserConfig(OscarConfig):
    label = "users"
    name = "ecommerce.apps.users"
    verbose_name = _("User")

    namespace = "users"
