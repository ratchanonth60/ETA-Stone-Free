"""
Module for managing reviews in the dashboard.
"""

from django.urls import path
from django.utils.translation import gettext_lazy as _
from oscar.core.application import OscarDashboardConfig
from oscar.core.loading import get_class


class ReviewsDashboardConfig(OscarDashboardConfig):
    """
    Configuration class for the Reviews dashboard app.
    """

    label = "reviews_dashboard"
    name = "ecommerce.apps.dashboard.reviews"
    verbose_name = _("Reviews dashboard")

    default_permissions = [
        "is_staff",
    ]

    def ready(self):
        DASHBOARD_REVIEWS_VIEWS = "dashboard.reviews.views"
        APPS_PATH = "ecommerce.apps"

        self.list_view = get_class(DASHBOARD_REVIEWS_VIEWS, "ReviewListView", APPS_PATH)
        self.update_view = get_class(
            DASHBOARD_REVIEWS_VIEWS, "ReviewUpdateView", APPS_PATH
        )
        self.delete_view = get_class(
            DASHBOARD_REVIEWS_VIEWS, "ReviewDeleteView", APPS_PATH
        )

    def get_urls(self):
        """
        Returns the URL patterns for the Reviews dashboard app.
        """
        urls = [
            path("", self.list_view.as_view(), name="reviews-list"),
            path("<int:pk>/", self.update_view.as_view(), name="reviews-update"),
            path("<int:pk>/delete/", self.delete_view.as_view(), name="reviews-delete"),
        ]
        return self.post_process_urls(urls)
