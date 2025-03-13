from django.utils.translation import gettext_lazy as _
from oscar.core.application import OscarConfig
from oscar.core.loading import get_class
from rest_framework.routers import DefaultRouter


class CommunicationApi(OscarConfig):
    label = "communication_api"
    name = "ecommerce.api.communication"
    verbose_name = _("CommunicationAPI")
    namespace = "communication_api"

    def ready(self):
        COMMUNICATION_VIEWS = "ecommerce.api.communication.views"
        APP_PATH = "ecommerce.apps"
        self.communicate = get_class(
            COMMUNICATION_VIEWS,
            "CommunicationEventTypeViewSet",
            APP_PATH,
        )
        self.email = get_class(COMMUNICATION_VIEWS, "EmailViewSet", APP_PATH)

        self.notification = get_class(
            COMMUNICATION_VIEWS, "NotificationViewSet", APP_PATH
        )

    @property
    def get_urls(self):
        router = DefaultRouter()
        # product
        router.register(r"communicate", self.communicate)
        router.register(r"email", self.email)
        router.register(r"notification", self.notification)

        return router
