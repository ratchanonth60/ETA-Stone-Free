from django.utils.translation import gettext_lazy as _
from oscar.core.application import OscarConfig
from oscar.core.loading import get_class
from rest_framework.routers import DefaultRouter


class UsersApi(OscarConfig):
    label = "users_api"
    name = "ecommerce.api.users"
    verbose_name = _("UsersApi")
    # default = True
    namespace = "users_api"

    def ready(self):
        self.users = get_class(
            "ecommerce.api.users.views", "UsersViewSet", "ecommerce.apps"
        )

    @property
    def get_urls(self):
        router = DefaultRouter()
        # product
        router.register(r"user", self.users)

        return router
