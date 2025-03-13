from django.utils.translation import gettext_lazy as _
from oscar.core.application import OscarConfig
from oscar.core.loading import get_class
from rest_framework.routers import DefaultRouter


class CatalogueApi(OscarConfig):
    label = "catalogue_api"
    name = "ecommerce.api.catalogue"
    verbose_name = _("CatalogueAPI")
    # default = True
    namespace = "catalogue_api"

    def ready(self):
        self.product = get_class(
            "ecommerce.api.catalogue.views", "ProductViewSet", "ecommerce.apps"
        )
        self.category = get_class(
            "ecommerce.api.catalogue.views", "CategoryViewSet", "ecommerce.apps"
        )
        self.product_class = get_class(
            "ecommerce.api.catalogue.views", "ProductClassViewSet", "ecommerce.apps"
        )
        self.product_image = get_class(
            "ecommerce.api.catalogue.views", "ProductImageViewSet", "ecommerce.apps"
        )

    @property
    def get_urls(self):
        router = DefaultRouter()
        # product
        router.register(r"product", self.product)
        router.register(r"category", self.category)
        router.register(r"product_class", self.product_class)
        router.register(r"product_image", self.product_image)

        return router
