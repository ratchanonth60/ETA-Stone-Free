from django.urls import path
from django.utils.translation import gettext_lazy as _
from oscar.core.application import OscarDashboardConfig
from oscar.core.loading import get_class


class ShippingDashboardConfig(OscarDashboardConfig):
    label = "shipping_dashboard"
    name = "ecommerce.apps.dashboard.shipping"
    verbose_name = _("Shipping dashboard")

    default_permissions = ["is_staff"]

    def ready(self):
        DASHBOARD_SHIPPING_VIEWS = "dashboard.shipping.views"
        APPS_MODULE = "ecommerce.apps"

        self.weight_method_list_view = get_class(
            DASHBOARD_SHIPPING_VIEWS, "WeightBasedListView", APPS_MODULE
        )
        self.weight_method_create_view = get_class(
            DASHBOARD_SHIPPING_VIEWS, "WeightBasedCreateView", APPS_MODULE
        )
        self.weight_method_edit_view = get_class(
            DASHBOARD_SHIPPING_VIEWS, "WeightBasedUpdateView", APPS_MODULE
        )
        self.weight_method_delete_view = get_class(
            DASHBOARD_SHIPPING_VIEWS, "WeightBasedDeleteView", APPS_MODULE
        )
        # This doubles as the weight_band create view
        self.weight_method_detail_view = get_class(
            DASHBOARD_SHIPPING_VIEWS, "WeightBasedDetailView", APPS_MODULE
        )
        self.weight_band_edit_view = get_class(
            DASHBOARD_SHIPPING_VIEWS, "WeightBandUpdateView", APPS_MODULE
        )
        self.weight_band_delete_view = get_class(
            DASHBOARD_SHIPPING_VIEWS, "WeightBandDeleteView", APPS_MODULE
        )

    def get_urls(self):
        urlpatterns = [
            path(
                "weight-based/",
                self.weight_method_list_view.as_view(),
                name="shipping-method-list",
            ),
            path(
                "weight-based/create/",
                self.weight_method_create_view.as_view(),
                name="shipping-method-create",
            ),
            path(
                "weight-based/<int:pk>/",
                self.weight_method_detail_view.as_view(),
                name="shipping-method-detail",
            ),
            path(
                "weight-based/<int:pk>/edit/",
                self.weight_method_edit_view.as_view(),
                name="shipping-method-edit",
            ),
            path(
                "weight-based/<int:pk>/delete/",
                self.weight_method_delete_view.as_view(),
                name="shipping-method-delete",
            ),
            path(
                "weight-based/<int:method_pk>/bands/<int:pk>/",
                self.weight_band_edit_view.as_view(),
                name="shipping-method-band-edit",
            ),
            path(
                "weight-based/<int:method_pk>/bands/<int:pk>/delete/",
                self.weight_band_delete_view.as_view(),
                name="shipping-method-band-delete",
            ),
        ]
        return self.post_process_urls(urlpatterns)
