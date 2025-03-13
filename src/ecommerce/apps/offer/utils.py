from importlib import import_module

from django.core import exceptions
from django.urls import reverse


def range_anchor(product_range):
    return '<a href="%s">%s</a>' % (
        reverse("dashboard:range-update", kwargs={"pk": product_range.pk}),
        product_range.name,
    )


# pylint: disable=unused-argument
def unit_price(offer, line):
    """
    Return the relevant price for a given basket line.

    This is required so offers can apply in circumstances where tax isn't known
    """
    return line.unit_effective_price


def load_proxy(proxy_class):
    module, classname = proxy_class.rsplit(".", 1)
    try:
        mod = import_module(module)
    except ImportError as e:
        raise exceptions.ImproperlyConfigured(
            f"Error importing module {module}: {e}"
        ) from e
    try:
        return getattr(mod, classname)
    except AttributeError as exc:
        raise exceptions.ImproperlyConfigured(
            f"Module {module} does not define a {classname}"
        ) from exc
