from django.urls import path
from django.utils.translation import gettext_lazy as _
from oscar.core.application import OscarDashboardConfig
from oscar.core.loading import get_class


class ReportsDashboardConfig(OscarDashboardConfig):
    label = "reports_dashboard"
    name = "ecommerce.apps.dashboard.reports"
    verbose_name = _("Reports dashboard")

    default_permissions = [
        "is_staff",
    ]

    def ready(self):
        self.index_view = get_class(
            "dashboard.reports.views", "IndexView", "ecommerce.apps"
        )

    def get_urls(self):
        urls = [
            path("", self.index_view.as_view(), name="reports-index"),
        ]
        return self.post_process_urls(urls)
