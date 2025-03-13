from django.urls import path
from django.utils.translation import gettext_lazy as _
from oscar.core.application import OscarDashboardConfig
from oscar.core.loading import get_class


class RangesDashboardConfig(OscarDashboardConfig):
    label = "ranges_dashboard"
    name = "ecommerce.apps.dashboard.ranges"
    verbose_name = _("Ranges dashboard")

    default_permissions = [
        "is_staff",
    ]

    def ready(self):
        DASHBOARD_RANGES_VIEWS = "dashboard.ranges.views"
        APP_PATH = "ecommerce.apps"
        self.list_view = get_class(DASHBOARD_RANGES_VIEWS, "RangeListView", APP_PATH)
        self.create_view = get_class(
            DASHBOARD_RANGES_VIEWS, "RangeCreateView", APP_PATH
        )
        self.update_view = get_class(
            DASHBOARD_RANGES_VIEWS, "RangeUpdateView", APP_PATH
        )
        self.delete_view = get_class(
            DASHBOARD_RANGES_VIEWS, "RangeDeleteView", APP_PATH
        )
        self.products_view = get_class(
            DASHBOARD_RANGES_VIEWS, "RangeProductListView", APP_PATH
        )
        self.reorder_view = get_class(
            DASHBOARD_RANGES_VIEWS, "RangeReorderView", APP_PATH
        )

    def get_urls(self):
        urlpatterns = [
            path("", self.list_view.as_view(), name="range-list"),
            path("create/", self.create_view.as_view(), name="range-create"),
            path("<int:pk>/", self.update_view.as_view(), name="range-update"),
            path("<int:pk>/delete/", self.delete_view.as_view(), name="range-delete"),
            path(
                "<int:pk>/products/",
                self.products_view.as_view(),
                name="range-products",
            ),
            path(
                "<int:pk>/reorder/", self.reorder_view.as_view(), name="range-reorder"
            ),
        ]
        return self.post_process_urls(urlpatterns)
