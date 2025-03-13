from django.urls import path
from django.utils.translation import gettext_lazy as _
from oscar.core.application import OscarDashboardConfig
from oscar.core.loading import get_class


class PartnersDashboardConfig(OscarDashboardConfig):
    label = "partners_dashboard"
    name = "ecommerce.apps.dashboard.partners"
    verbose_name = _("Partners dashboard")

    default_permissions = [
        "is_staff",
    ]

    def ready(self):
        DASHBOARD_PARTNERS_VIEWS = "dashboard.partners.views"
        APPS_PATH = "ecommerce.apps"

        self.list_view = get_class(
            DASHBOARD_PARTNERS_VIEWS, "PartnerListView", APPS_PATH
        )
        self.create_view = get_class(
            DASHBOARD_PARTNERS_VIEWS, "PartnerCreateView", APPS_PATH
        )
        self.manage_view = get_class(
            DASHBOARD_PARTNERS_VIEWS, "PartnerManageView", APPS_PATH
        )
        self.delete_view = get_class(
            DASHBOARD_PARTNERS_VIEWS, "PartnerDeleteView", APPS_PATH
        )

        self.user_link_view = get_class(
            DASHBOARD_PARTNERS_VIEWS, "PartnerUserLinkView", APPS_PATH
        )
        self.user_unlink_view = get_class(
            DASHBOARD_PARTNERS_VIEWS, "PartnerUserUnlinkView", APPS_PATH
        )
        self.user_create_view = get_class(
            DASHBOARD_PARTNERS_VIEWS, "PartnerUserCreateView", APPS_PATH
        )
        self.user_select_view = get_class(
            DASHBOARD_PARTNERS_VIEWS, "PartnerUserSelectView", APPS_PATH
        )
        self.user_update_view = get_class(
            DASHBOARD_PARTNERS_VIEWS, "PartnerUserUpdateView", APPS_PATH
        )

    def get_urls(self):
        urls = [
            path("", self.list_view.as_view(), name="partner-list"),
            path("create/", self.create_view.as_view(), name="partner-create"),
            path("<int:pk>/", self.manage_view.as_view(), name="partner-manage"),
            path("<int:pk>/delete/", self.delete_view.as_view(), name="partner-delete"),
            path(
                "<int:partner_pk>/users/add/",
                self.user_create_view.as_view(),
                name="partner-user-create",
            ),
            path(
                "<int:partner_pk>/users/select/",
                self.user_select_view.as_view(),
                name="partner-user-select",
            ),
            path(
                "<int:partner_pk>/users/<int:user_pk>/link/",
                self.user_link_view.as_view(),
                name="partner-user-link",
            ),
            path(
                "<int:partner_pk>/users/<int:user_pk>/unlink/",
                self.user_unlink_view.as_view(),
                name="partner-user-unlink",
            ),
            path(
                "<int:partner_pk>/users/<int:user_pk>/update/",
                self.user_update_view.as_view(),
                name="partner-user-update",
            ),
        ]
        return self.post_process_urls(urls)
