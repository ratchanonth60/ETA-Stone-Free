from django.contrib.auth.decorators import login_required
from django.urls import path, re_path
from django.utils.translation import gettext_lazy as _
from django.views import generic
from oscar.core.application import OscarConfig
from oscar.core.loading import get_class


class CustomerConfig(OscarConfig):
    label = "customer"
    name = "ecommerce.apps.customer"
    verbose_name = _("Customer")

    namespace = "customer"

    def ready(self):
        from oscar.apps.customer import receivers  # noqa
        from oscar.apps.customer.alerts import receivers  # noqa

        CUSTOMER_VIEWS = "customer.views"
        CUSTOMER_ALERTS_VIEWS = "customer.alerts.views"
        WISHLISTS_VIEWS = "customer.wishlists.views"

        APPS_PATH = (
            "ecommerce.apps"  # Define a constant for the "ecommerce.apps" string
        )

        self.summary_view = get_class(CUSTOMER_VIEWS, "AccountSummaryView", APPS_PATH)
        self.order_history_view = get_class(
            CUSTOMER_VIEWS, "OrderHistoryView", APPS_PATH
        )
        self.order_detail_view = get_class(CUSTOMER_VIEWS, "OrderDetailView", APPS_PATH)
        self.anon_order_detail_view = get_class(
            CUSTOMER_VIEWS, "AnonymousOrderDetailView", APPS_PATH
        )
        self.order_line_view = get_class(CUSTOMER_VIEWS, "OrderLineView", APPS_PATH)

        self.address_list_view = get_class(CUSTOMER_VIEWS, "AddressListView", APPS_PATH)
        self.address_create_view = get_class(
            CUSTOMER_VIEWS, "AddressCreateView", APPS_PATH
        )
        self.address_update_view = get_class(
            CUSTOMER_VIEWS, "AddressUpdateView", APPS_PATH
        )
        self.address_delete_view = get_class(
            CUSTOMER_VIEWS, "AddressDeleteView", APPS_PATH
        )
        self.address_change_status_view = get_class(
            CUSTOMER_VIEWS, "AddressChangeStatusView", APPS_PATH
        )

        self.email_list_view = get_class(CUSTOMER_VIEWS, "EmailHistoryView", APPS_PATH)
        self.email_detail_view = get_class(CUSTOMER_VIEWS, "EmailDetailView", APPS_PATH)
        self.login_view = get_class(CUSTOMER_VIEWS, "AccountAuthView", APPS_PATH)
        self.logout_view = get_class(CUSTOMER_VIEWS, "LogoutView", APPS_PATH)
        self.register_view = get_class(
            CUSTOMER_VIEWS, "AccountRegistrationView", APPS_PATH
        )
        self.profile_view = get_class(CUSTOMER_VIEWS, "ProfileView", APPS_PATH)
        self.profile_update_view = get_class(
            CUSTOMER_VIEWS, "ProfileUpdateView", APPS_PATH
        )
        self.profile_delete_view = get_class(
            CUSTOMER_VIEWS, "ProfileDeleteView", APPS_PATH
        )
        NOTIFICATIONS_VIEWS = "communication.notifications.views"

        self.change_password_view = get_class(
            CUSTOMER_VIEWS, "ChangePasswordView", APPS_PATH
        )

        self.notification_inbox_view = get_class(
            NOTIFICATIONS_VIEWS, "InboxView", APPS_PATH
        )
        self.notification_archive_view = get_class(
            NOTIFICATIONS_VIEWS, "ArchiveView", APPS_PATH
        )
        self.notification_update_view = get_class(
            NOTIFICATIONS_VIEWS, "UpdateView", APPS_PATH
        )

        self.notification_detail_view = get_class(
            "communication.notifications.views", "DetailView", APPS_PATH
        )

        self.alert_list_view = get_class(
            CUSTOMER_ALERTS_VIEWS, "ProductAlertListView", APPS_PATH
        )

        self.alert_create_view = get_class(
            CUSTOMER_ALERTS_VIEWS, "ProductAlertCreateView", APPS_PATH
        )
        self.alert_confirm_view = get_class(
            CUSTOMER_ALERTS_VIEWS, "ProductAlertConfirmView", APPS_PATH
        )

        self.alert_cancel_view = get_class(
            CUSTOMER_ALERTS_VIEWS, "ProductAlertCancelView", APPS_PATH
        )

        self.wishlists_add_product_view = get_class(
            WISHLISTS_VIEWS, "WishListAddProduct", APPS_PATH
        )
        self.wishlists_list_view = get_class(
            WISHLISTS_VIEWS, "WishListListView", APPS_PATH
        )
        self.wishlists_detail_view = get_class(
            WISHLISTS_VIEWS, "WishListDetailView", APPS_PATH
        )
        self.wishlists_create_view = get_class(
            WISHLISTS_VIEWS, "WishListCreateView", APPS_PATH
        )
        self.wishlists_create_with_product_view = get_class(
            WISHLISTS_VIEWS, "WishListCreateView", APPS_PATH
        )
        self.wishlists_update_view = get_class(
            WISHLISTS_VIEWS, "WishListUpdateView", APPS_PATH
        )
        self.wishlists_delete_view = get_class(
            WISHLISTS_VIEWS, "WishListDeleteView", APPS_PATH
        )
        self.wishlists_remove_product_view = get_class(
            WISHLISTS_VIEWS, "WishListRemoveProduct", APPS_PATH
        )
        self.wishlists_move_product_to_another_view = get_class(
            WISHLISTS_VIEWS,
            "WishListMoveProductToAnotherWishList",
            APPS_PATH,
        )
        self.payment_manage_list = get_class(
            CUSTOMER_VIEWS,
            "PaymentManagementListView",
            APPS_PATH,
        )
        self.payment_manage_create = get_class(
            CUSTOMER_VIEWS,
            "PaymentManagementCreateView",
            APPS_PATH,
        )

    def get_urls(self):
        urls = [
            # Login, logout and register doesn't require login
            path("login/", self.login_view.as_view(), name="login"),
            path("logout/", self.logout_view.as_view(), name="logout"),
            path("register/", self.register_view.as_view(), name="register"),
            path("", login_required(self.summary_view.as_view()), name="summary"),
            path(
                "change-password/",
                login_required(self.change_password_view.as_view()),
                name="change-password",
            ),
            # Profile
            path(
                "profile/",
                login_required(self.profile_view.as_view()),
                name="profile-view",
            ),
            path(
                "profile/edit/",
                login_required(self.profile_update_view.as_view()),
                name="profile-update",
            ),
            path(
                "profile/delete/",
                login_required(self.profile_delete_view.as_view()),
                name="profile-delete",
            ),
            # Order history
            path(
                "orders/",
                login_required(self.order_history_view.as_view()),
                name="order-list",
            ),
            re_path(
                r"^order-status/(?P<order_number>[\w-]*)/(?P<hash>[A-z0-9-_=:]+)/$",
                self.anon_order_detail_view.as_view(),
                name="anon-order",
            ),
            path(
                "orders/<str:order_number>/",
                login_required(self.order_detail_view.as_view()),
                name="order",
            ),
            path(
                "orders/<str:order_number>/<int:line_id>/",
                login_required(self.order_line_view.as_view()),
                name="order-line",
            ),
            # Address book
            path(
                "addresses/",
                login_required(self.address_list_view.as_view()),
                name="address-list",
            ),
            path(
                "addresses/add/",
                login_required(self.address_create_view.as_view()),
                name="address-create",
            ),
            path(
                "addresses/<int:pk>/",
                login_required(self.address_update_view.as_view()),
                name="address-detail",
            ),
            path(
                "addresses/<int:pk>/delete/",
                login_required(self.address_delete_view.as_view()),
                name="address-delete",
            ),
            re_path(
                r"^addresses/(?P<pk>\d+)/(?P<action>default_for_(billing|shipping))/$",
                login_required(self.address_change_status_view.as_view()),
                name="address-change-status",
            ),
            # Email history
            path(
                "emails/",
                login_required(self.email_list_view.as_view()),
                name="email-list",
            ),
            path(
                "emails/<int:email_id>/",
                login_required(self.email_detail_view.as_view()),
                name="email-detail",
            ),
            # Notifications
            # Redirect to notification inbox
            path(
                "notifications/",
                generic.RedirectView.as_view(
                    url="/accounts/notifications/inbox/", permanent=False
                ),
            ),
            path(
                "notifications/inbox/",
                login_required(self.notification_inbox_view.as_view()),
                name="notifications-inbox",
            ),
            path(
                "notifications/archive/",
                login_required(self.notification_archive_view.as_view()),
                name="notifications-archive",
            ),
            path(
                "notifications/update/",
                login_required(self.notification_update_view.as_view()),
                name="notifications-update",
            ),
            path(
                "notifications/<int:pk>/",
                login_required(self.notification_detail_view.as_view()),
                name="notifications-detail",
            ),
            # Alerts
            # Alerts can be setup by anonymous users: some views do not
            # require login
            path(
                "alerts/",
                login_required(self.alert_list_view.as_view()),
                name="alerts-list",
            ),
            path(
                "alerts/create/<int:pk>/",
                self.alert_create_view.as_view(),
                name="alert-create",
            ),
            path(
                "alerts/confirm/<str:key>/",
                self.alert_confirm_view.as_view(),
                name="alerts-confirm",
            ),
            path(
                "alerts/cancel/key/<str:key>/",
                self.alert_cancel_view.as_view(),
                name="alerts-cancel-by-key",
            ),
            path(
                "alerts/cancel/<int:pk>/",
                login_required(self.alert_cancel_view.as_view()),
                name="alerts-cancel-by-pk",
            ),
            # Wishlists
            path(
                "wishlists/",
                login_required(self.wishlists_list_view.as_view()),
                name="wishlists-list",
            ),
            path(
                "wishlists/add/<int:product_pk>/",
                login_required(self.wishlists_add_product_view.as_view()),
                name="wishlists-add-product",
            ),
            path(
                "wishlists/<str:key>/add/<int:product_pk>/",
                login_required(self.wishlists_add_product_view.as_view()),
                name="wishlists-add-product",
            ),
            path(
                "wishlists/create/",
                login_required(self.wishlists_create_view.as_view()),
                name="wishlists-create",
            ),
            path(
                "wishlists/create/with-product/<int:product_pk>/",
                login_required(self.wishlists_create_view.as_view()),
                name="wishlists-create-with-product",
            ),
            # Wishlists can be publicly shared, no login required
            path(
                "wishlists/<str:key>/",
                self.wishlists_detail_view.as_view(),
                name="wishlists-detail",
            ),
            path(
                "wishlists/<str:key>/update/",
                login_required(self.wishlists_update_view.as_view()),
                name="wishlists-update",
            ),
            path(
                "wishlists/<str:key>/delete/",
                login_required(self.wishlists_delete_view.as_view()),
                name="wishlists-delete",
            ),
            path(
                "wishlists/<str:key>/lines/<int:line_pk>/delete/",
                login_required(self.wishlists_remove_product_view.as_view()),
                name="wishlists-remove-product",
            ),
            path(
                "wishlists/<str:key>/products/<int:product_pk>/delete/",
                login_required(self.wishlists_remove_product_view.as_view()),
                name="wishlists-remove-product",
            ),
            path(
                "wishlists/<str:key>/lines/<int:line_pk>/move-to/<str:to_key>/",
                login_required(self.wishlists_move_product_to_another_view.as_view()),
                name="wishlists-move-product-to-another",
            ),
            path(
                "payment-manage/",
                self.payment_manage_list.as_view(),
                name="payment-list",
            ),
            path(
                "payment-manage/create/",
                self.payment_manage_create.as_view(),
                name="payment-create",
            ),
        ]

        return self.post_process_urls(urls)
