from oscar.apps.shipping import repository

from .methods import Free, NoShippingRequired, Standard


class Repository(repository.Repository):
    methods = (Free(), NoShippingRequired(), Standard())

    def get_available_shipping_methods(self, basket, shipping_addr=None, **kwargs):
        return self.methods
