from django.apps import apps
from django.urls import include, path, re_path
from django.utils.translation import gettext_lazy as _
from oscar.core.application import OscarConfig
from oscar.core.loading import get_class


class CatalogueOnlyConfig(OscarConfig):
    label = "catalogue"
    name = "ecommerce.apps.catalogue"
    verbose_name = _("Catalogue")
    # default = True
    namespace = "catalogue"

    def ready(self):
        from oscar.apps.catalogue import receivers  # noqa

        super().ready()

        self.detail_view = get_class(
            "catalogue.views", "ProductDetailView", "ecommerce.apps"
        )
        self.catalogue_view = get_class(
            "catalogue.views", "CatalogueView", "ecommerce.apps"
        )
        self.category_view = get_class(
            "catalogue.views", "ProductCategoryView", "ecommerce.apps"
        )
        self.range_view = get_class("offer.views", "RangeDetailView", "ecommerce.apps")

    def get_urls(self):
        urls = super().get_urls()
        urls += [
            path("", self.catalogue_view.as_view(), name="index"),
            re_path(
                r"^(?P<product_slug>[\w-]*)_(?P<pk>\d+)/$",
                self.detail_view.as_view(),
                name="detail",
            ),
            re_path(
                r"^category/(?P<category_slug>[\w-]+(/[\w-]+)*)_(?P<pk>\d+)/$",
                self.category_view.as_view(),
                name="category",
            ),
            path("ranges/<slug:slug>/", self.range_view.as_view(), name="range"),
        ]
        return self.post_process_urls(urls)


class CatalogueReviewsOnlyConfig(OscarConfig):
    label = "catalogue"
    name = "ecommerce.apps.catalogue"
    verbose_name = _("Catalogue")

    def ready(self):
        from oscar.apps.catalogue import receivers  # noqa

        super().ready()

        self.reviews_app = apps.get_app_config("reviews")

    def get_urls(self):
        urls = super().get_urls()
        urls += [
            re_path(
                r"^(?P<product_slug>[\w-]*)_(?P<product_pk>\d+)/reviews/",
                include(self.reviews_app.urls[0]),
            ),
        ]
        return self.post_process_urls(urls)


class CatalogueConfig(CatalogueOnlyConfig, CatalogueReviewsOnlyConfig):
    """
    Composite class combining Products with Reviews
    """
