from django.apps import apps
from django.utils.translation import gettext_lazy as _
from oscar.core.application import OscarConfig
from rest_framework.routers import DefaultRouter


class Api(OscarConfig):
    label = "api"
    name = "ecommerce.api"
    verbose_name = _("API")
    # default = True

    def ready(self):
        self.basket = apps.get_app_config("basket_api")
        self.category = apps.get_app_config("catalogue_api")
        self.users = apps.get_app_config("users_api")
        self.communication = apps.get_app_config("communication_api")

    def aggregate_routers(self, *routers):
        main_router = DefaultRouter()
        for router in routers:
            for prefix, viewset, basename in router.registry:
                main_router.register(prefix, viewset, basename)
        return main_router.urls

    def get_urls(self):
        return self.post_process_urls(
            self.aggregate_routers(
                self.basket.get_urls,
                self.users.get_urls,
                self.category.get_urls,
                self.communication.get_urls,
            )
        )
