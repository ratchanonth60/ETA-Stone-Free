from django.urls import path
from django.utils.translation import gettext_lazy as _
from oscar.core.application import OscarDashboardConfig
from oscar.core.loading import get_class


class CommunicationsDashboardConfig(OscarDashboardConfig):
    label = "communications_dashboard"
    name = "ecommerce.apps.dashboard.communications"
    verbose_name = _("Communications dashboard")

    default_permissions = [
        "is_staff",
    ]

    def ready(self):
        self.list_view = get_class(
            "dashboard.communications.views", "ListView", "ecommerce.apps"
        )
        self.update_view = get_class(
            "dashboard.communications.views", "UpdateView", "ecommerce.apps"
        )

    def get_urls(self):
        urls = [
            path("", self.list_view.as_view(), name="comms-list"),
            path("<slug:slug>/", self.update_view.as_view(), name="comms-update"),
        ]
        return self.post_process_urls(urls)
