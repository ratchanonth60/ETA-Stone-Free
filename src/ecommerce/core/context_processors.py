import re

import stripe
from django.conf import settings


def strip_language_code(request):
    """
    When using Django's i18n_patterns, we need a language-neutral variant of
    the current URL to be able to use set_language to change languages.
    This naive approach strips the language code from the beginning of the URL
    and will likely fail if using translated URLs.
    """
    path = request.path
    if settings.USE_I18N and hasattr(request, "LANGUAGE_CODE"):
        return re.sub(f"^/{request.LANGUAGE_CODE}/", "/", path)
    return path


def metadata(request):
    """
    Add some generally useful metadata to the template context
    """
    meta = {
        "stripe_public_key": None,
        "shop_name": settings.OSCAR_SHOP_NAME,
        "shop_tagline": settings.OSCAR_SHOP_TAGLINE,
        "homepage_url": settings.OSCAR_HOMEPAGE,
        "language_neutral_url_path": strip_language_code(request),
        # Fallback to old settings name for backwards compatibility
        "google_analytics_id": (
            getattr(settings, "OSCAR_GOOGLE_ANALYTICS_ID", None)
            or getattr(settings, "GOOGLE_ANALYTICS_ID", None)
        ),
    }
    tenant_key = settings.STRIPE_TENANT.get(request.tenant.name, None)
    if tenant_key:
        publickey, stripe.api_key = tenant_key.values()
        meta["stripe_public_key"] = publickey

    return meta
