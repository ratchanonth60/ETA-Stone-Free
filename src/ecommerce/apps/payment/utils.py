from django.conf import settings


def get_payment_method_display(payment_method):
    return dict(settings.OSCAR_PAYMENT_METHODS).get(payment_method)
