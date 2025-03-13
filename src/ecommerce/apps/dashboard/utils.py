from django.contrib import messages
from oscar.core.loading import get_class

RelatedFieldWidgetWrapper = get_class(
    "dashboard.widgets", "RelatedFieldWidgetWrapper", "ecommerce.apps"
)


class PopUpWindowMixin:
    @property
    def is_popup(self):
        return self.request.GET.get(
            RelatedFieldWidgetWrapper.IS_POPUP_VAR,
            self.request.POST.get(RelatedFieldWidgetWrapper.IS_POPUP_VAR),
        )

    @property
    def is_popup_var(self):
        return RelatedFieldWidgetWrapper.IS_POPUP_VAR

    def add_success_message(self, message):
        if not self.is_popup:
            messages.info(self.request, message)
