from django.urls import path, re_path
from django.utils.translation import gettext_lazy as _
from oscar.core.application import OscarDashboardConfig
from oscar.core.loading import get_class


class UsersDashboardConfig(OscarDashboardConfig):
    label = "users_dashboard"
    name = "ecommerce.apps.dashboard.users"
    verbose_name = _("Users dashboard")

    default_permissions = [
        "is_staff",
    ]

    def ready(self):
        self.index_view = get_class(
            "dashboard.users.views", "IndexView", "ecommerce.apps"
        )
        self.user_detail_view = get_class(
            "dashboard.users.views", "UserDetailView", "ecommerce.apps"
        )
        self.password_reset_view = get_class(
            "dashboard.users.views", "PasswordResetView", "ecommerce.apps"
        )
        self.alert_list_view = get_class(
            "dashboard.users.views", "ProductAlertListView", "ecommerce.apps"
        )
        self.alert_update_view = get_class(
            "dashboard.users.views", "ProductAlertUpdateView", "ecommerce.apps"
        )
        self.alert_delete_view = get_class(
            "dashboard.users.views", "ProductAlertDeleteView", "ecommerce.apps"
        )

    def get_urls(self):
        urls = [
            path("", self.index_view.as_view(), name="users-index"),
            re_path(
                r"^(?P<pk>-?\d+)/$", self.user_detail_view.as_view(), name="user-detail"
            ),
            re_path(
                r"^(?P<pk>-?\d+)/password-reset/$",
                self.password_reset_view.as_view(),
                name="user-password-reset",
            ),
            # Alerts
            path("alerts/", self.alert_list_view.as_view(), name="user-alert-list"),
            re_path(
                r"^alerts/(?P<pk>-?\d+)/delete/$",
                self.alert_delete_view.as_view(),
                name="user-alert-delete",
            ),
            re_path(
                r"^alerts/(?P<pk>-?\d+)/update/$",
                self.alert_update_view.as_view(),
                name="user-alert-update",
            ),
        ]
        return self.post_process_urls(urls)
