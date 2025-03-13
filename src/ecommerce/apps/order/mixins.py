from ecommerce.apps.order.processing import EventHandler


class EventHandlerMixin:
    handler_class = EventHandler

    def get_handler_class(self):
        return self.handler_class

    def get_handler(self, user=None, **kwargs):
        handler_kwargs = self.get_handler_kwargs()
        handler_kwargs.update(**kwargs)
        return self.get_handler_class()(user, **handler_kwargs)

    def get_handler_kwargs(self):
        return {}
