from django.urls import path
from django.utils.translation import gettext_lazy as _
from oscar.core.application import OscarDashboardConfig
from oscar.core.loading import get_class


class OrdersDashboardConfig(OscarDashboardConfig):
    label = "orders_dashboard"
    name = "ecommerce.apps.dashboard.orders"
    verbose_name = _("Orders dashboard")

    default_permissions = [
        "is_staff",
    ]
    PERMISSION_PARTNER_DASHBOARD_ACCESS = "partner.dashboard_access"

    permissions_map = {
        "order-list": (["is_staff"], [PERMISSION_PARTNER_DASHBOARD_ACCESS]),
        "order-stats": (["is_staff"], [PERMISSION_PARTNER_DASHBOARD_ACCESS]),
        "order-detail": (["is_staff"], [PERMISSION_PARTNER_DASHBOARD_ACCESS]),
        "order-detail-note": (["is_staff"], [PERMISSION_PARTNER_DASHBOARD_ACCESS]),
        "order-line-detail": (["is_staff"], [PERMISSION_PARTNER_DASHBOARD_ACCESS]),
        "order-shipping-address": (["is_staff"], [PERMISSION_PARTNER_DASHBOARD_ACCESS]),
    }

    def ready(self):
        DASHBOARD_ORDERS_VIEWS = "dashboard.orders.views"
        DASHBOARD_APPS = "ecommerce.apps"
        self.order_list_view = get_class(
            DASHBOARD_ORDERS_VIEWS, "OrderListView", DASHBOARD_APPS
        )
        self.order_detail_view = get_class(
            DASHBOARD_ORDERS_VIEWS, "OrderDetailView", DASHBOARD_APPS
        )
        self.shipping_address_view = get_class(
            DASHBOARD_ORDERS_VIEWS, "ShippingAddressUpdateView", DASHBOARD_APPS
        )
        self.line_detail_view = get_class(
            DASHBOARD_ORDERS_VIEWS, "LineDetailView", DASHBOARD_APPS
        )
        self.order_stats_view = get_class(
            DASHBOARD_ORDERS_VIEWS, "OrderStatsView", DASHBOARD_APPS
        )

    def get_urls(self):
        urls = [
            path("", self.order_list_view.as_view(), name="order-list"),
            path("statistics/", self.order_stats_view.as_view(), name="order-stats"),
            path(
                "<str:number>/", self.order_detail_view.as_view(), name="order-detail"
            ),
            path(
                "<str:number>/notes/<int:note_id>/",
                self.order_detail_view.as_view(),
                name="order-detail-note",
            ),
            path(
                "<str:number>/lines/<int:line_id>/",
                self.line_detail_view.as_view(),
                name="order-line-detail",
            ),
            path(
                "<str:number>/shipping-address/",
                self.shipping_address_view.as_view(),
                name="order-shipping-address",
            ),
        ]
        return self.post_process_urls(urls)
