from django.contrib.auth.decorators import login_required
from django.urls import path
from django.utils.translation import gettext_lazy as _
from oscar.core.application import OscarConfig
from oscar.core.loading import get_class


class BasketConfig(OscarConfig):
    label = "basket"
    name = "ecommerce.apps.basket"
    verbose_name = _("Basket")

    namespace = "basket"

    def ready(self):
        BASKET_VIEWS = "basket.views"
        APP_PATH = "ecommerce.apps"
        self.summary_view = get_class(BASKET_VIEWS, "BasketView", APP_PATH)
        self.saved_view = get_class(BASKET_VIEWS, "SavedView", APP_PATH)
        self.add_view = get_class(BASKET_VIEWS, "BasketAddView", APP_PATH)
        self.add_voucher_view = get_class(BASKET_VIEWS, "VoucherAddView", APP_PATH)
        self.remove_voucher_view = get_class(
            BASKET_VIEWS, "VoucherRemoveView", APP_PATH
        )

    def get_urls(self):
        urls = [
            path("", self.summary_view.as_view(), name="summary"),
            path("add/<int:pk>/", self.add_view.as_view(), name="add"),
            path("vouchers/add/", self.add_voucher_view.as_view(), name="vouchers-add"),
            path(
                "vouchers/<int:pk>/remove/",
                self.remove_voucher_view.as_view(),
                name="vouchers-remove",
            ),
            path("saved/", login_required(self.saved_view.as_view()), name="saved"),
        ]
        return self.post_process_urls(urls)
