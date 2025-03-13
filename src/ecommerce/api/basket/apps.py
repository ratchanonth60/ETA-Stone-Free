from django.utils.translation import gettext_lazy as _
from oscar.core.application import OscarConfig
from oscar.core.loading import get_class
from rest_framework.routers import DefaultRouter


class BasketApi(OscarConfig):
    label = "basket_api"
    name = "ecommerce.api.basket"
    verbose_name = _("BasketApi")
    # default = True
    namespace = "basket_api"

    def ready(self):
        self.basket = get_class(
            "ecommerce.api.basket.views", "BasketViewSet", "ecommerce.apps"
        )
        self.line = get_class(
            "ecommerce.api.basket.views", "LineViewSet", "ecommerce.apps"
        )

    @property
    def get_urls(self):
        router = DefaultRouter()
        # product
        router.register(r"basket", self.basket)
        router.register(r"line", self.line)

        return router
