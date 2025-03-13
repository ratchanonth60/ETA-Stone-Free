from django.urls import path
from django.utils.translation import gettext_lazy as _
from oscar.core.application import OscarDashboardConfig
from oscar.core.loading import get_class


class VouchersDashboardConfig(OscarDashboardConfig):
    label = "vouchers_dashboard"
    name = "ecommerce.apps.dashboard.vouchers"
    verbose_name = _("Vouchers dashboard")

    default_permissions = [
        "is_staff",
    ]

    def ready(self):
        DASHBOARD_VOUCHERS_VIEWS = "dashboard.vouchers.views"
        APPS_MODULE = "ecommerce.apps"

        self.list_view = get_class(
            DASHBOARD_VOUCHERS_VIEWS, "VoucherListView", APPS_MODULE
        )
        self.create_view = get_class(
            DASHBOARD_VOUCHERS_VIEWS, "VoucherCreateView", APPS_MODULE
        )
        self.update_view = get_class(
            DASHBOARD_VOUCHERS_VIEWS, "VoucherUpdateView", APPS_MODULE
        )
        self.delete_view = get_class(
            DASHBOARD_VOUCHERS_VIEWS, "VoucherDeleteView", APPS_MODULE
        )
        self.stats_view = get_class(
            DASHBOARD_VOUCHERS_VIEWS, "VoucherStatsView", APPS_MODULE
        )

        self.set_list_view = get_class(
            DASHBOARD_VOUCHERS_VIEWS, "VoucherSetListView", APPS_MODULE
        )
        self.set_create_view = get_class(
            DASHBOARD_VOUCHERS_VIEWS, "VoucherSetCreateView", APPS_MODULE
        )
        self.set_update_view = get_class(
            DASHBOARD_VOUCHERS_VIEWS, "VoucherSetUpdateView", APPS_MODULE
        )
        self.set_detail_view = get_class(
            DASHBOARD_VOUCHERS_VIEWS, "VoucherSetDetailView", APPS_MODULE
        )
        self.set_download_view = get_class(
            DASHBOARD_VOUCHERS_VIEWS, "VoucherSetDownloadView", APPS_MODULE
        )
        self.set_delete_view = get_class(
            DASHBOARD_VOUCHERS_VIEWS, "VoucherSetDeleteView", APPS_MODULE
        )

    def get_urls(self):
        urls = [
            path("", self.list_view.as_view(), name="voucher-list"),
            path("create/", self.create_view.as_view(), name="voucher-create"),
            path("update/<int:pk>/", self.update_view.as_view(), name="voucher-update"),
            path("delete/<int:pk>/", self.delete_view.as_view(), name="voucher-delete"),
            path("stats/<int:pk>/", self.stats_view.as_view(), name="voucher-stats"),
            path("sets/", self.set_list_view.as_view(), name="voucher-set-list"),
            path(
                "sets/create/",
                self.set_create_view.as_view(),
                name="voucher-set-create",
            ),
            path(
                "sets/update/<int:pk>/",
                self.set_update_view.as_view(),
                name="voucher-set-update",
            ),
            path(
                "sets/detail/<int:pk>/",
                self.set_detail_view.as_view(),
                name="voucher-set-detail",
            ),
            path(
                "sets/download/<int:pk>/",
                self.set_download_view.as_view(),
                name="voucher-set-download",
            ),
            path(
                "sets/delete/<int:pk>/",
                self.set_delete_view.as_view(),
                name="voucher-set-delete",
            ),
        ]
        return self.post_process_urls(urls)
