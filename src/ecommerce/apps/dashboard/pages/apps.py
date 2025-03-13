from django.urls import path
from django.utils.translation import gettext_lazy as _
from oscar.core.application import OscarDashboardConfig
from oscar.core.loading import get_class


class PagesDashboardConfig(OscarDashboardConfig):
    label = "pages_dashboard"
    name = "ecommerce.apps.dashboard.pages"
    verbose_name = _("Pages dashboard")

    default_permissions = [
        "is_staff",
    ]

    def ready(self):
        DASHBOARD_PAGES_VIEWS = "dashboard.pages.views"
        APPS_PATH = "ecommerce.apps"

        self.list_view = get_class(DASHBOARD_PAGES_VIEWS, "PageListView", APPS_PATH)
        self.create_view = get_class(DASHBOARD_PAGES_VIEWS, "PageCreateView", APPS_PATH)
        self.update_view = get_class(DASHBOARD_PAGES_VIEWS, "PageUpdateView", APPS_PATH)
        self.delete_view = get_class(DASHBOARD_PAGES_VIEWS, "PageDeleteView", APPS_PATH)

    def get_urls(self):
        """
        Get URL patterns defined for flatpage management application.
        """
        urls = [
            path("", self.list_view.as_view(), name="page-list"),
            path("create/", self.create_view.as_view(), name="page-create"),
            path("update/<str:pk>/", self.update_view.as_view(), name="page-update"),
            path("delete/<str:pk>/", self.delete_view.as_view(), name="page-delete"),
        ]
        return self.post_process_urls(urls)
