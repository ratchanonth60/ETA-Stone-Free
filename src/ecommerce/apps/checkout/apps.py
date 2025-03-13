from functools import partial

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.urls import path
from django.utils.translation import gettext_lazy as _
from oscar.core.application import OscarConfig
from oscar.core.loading import get_class


class CheckoutConfig(OscarConfig):
    label = "checkout"
    name = "ecommerce.apps.checkout"
    verbose_name = _("Checkout")

    namespace = "checkout"

    def ready(self):
        CHECKOUT_VIEWS = "checkout.views"
        APPS = "ecommerce.apps"

        self.index_view = get_class(CHECKOUT_VIEWS, "IndexView", APPS)
        self.shipping_address_view = get_class(
            CHECKOUT_VIEWS, "ShippingAddressView", APPS
        )
        self.user_address_update_view = get_class(
            CHECKOUT_VIEWS, "UserAddressUpdateView", APPS
        )
        self.user_address_delete_view = get_class(
            CHECKOUT_VIEWS, "UserAddressDeleteView", APPS
        )
        self.shipping_method_view = get_class(
            CHECKOUT_VIEWS, "ShippingMethodView", APPS
        )
        self.payment_method_view = get_class(CHECKOUT_VIEWS, "PaymentMethodView", APPS)
        self.payment_details_view = get_class(
            CHECKOUT_VIEWS, "PaymentDetailsView", APPS
        )
        self.thankyou_view = get_class(CHECKOUT_VIEWS, "ThankYouView", APPS)

    def get_urls(self):
        urls = [
            path("", self.index_view.as_view(), name="index"),
            # Shipping/user address views
            path(
                "shipping-address/",
                self.shipping_address_view.as_view(),
                name="shipping-address",
            ),
            path(
                "user-address/edit/<int:pk>/",
                self.user_address_update_view.as_view(),
                name="user-address-update",
            ),
            path(
                "user-address/delete/<int:pk>/",
                self.user_address_delete_view.as_view(),
                name="user-address-delete",
            ),
            # Shipping method views
            path(
                "shipping-method/",
                self.shipping_method_view.as_view(),
                name="shipping-method",
            ),
            # Payment views
            path(
                "payment-method/",
                self.payment_method_view.as_view(),
                name="payment-method",
            ),
            path(
                "payment-details/",
                self.payment_details_view.as_view(),
                name="payment-details",
            ),
            # Preview and thankyou
            path(
                "preview/",
                self.payment_details_view.as_view(preview=True),
                name="preview",
            ),
            path("thank-you/", self.thankyou_view.as_view(), name="thank-you"),
        ]
        return self.post_process_urls(urls)

    def get_url_decorator(self, pattern):
        if settings.OSCAR_ALLOW_ANON_CHECKOUT and not pattern.name.startswith(
            "user-address"
        ):
            return partial(login_required)
        return None
