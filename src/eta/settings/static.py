# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/
import os

from .base import BASE_DIR, DEBUG


# Media files
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "public", "media")
# MULTITENANT_RELATIVE_MEDIA_ROOT = "%s/"  # (default: create sub-directory for each tenant)

# Static files
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "public", "static")
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
]

# Storage สำหรับ static files
STATICFILES_STORAGE = "django_tenants.staticfiles.storage.TenantStaticFilesStorage"
# Storage สำหรับ media files
DEFAULT_FILE_STORAGE = (
    "django.contrib.staticfiles.storage.FileSystemStorage"
    if DEBUG
    else "ecommerce.core.storages.tenant_storages.TenantS3Storage"
)

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            os.path.join(BASE_DIR, "ecommerce/templates"),
        ],
        "OPTIONS": {
            "loaders": [
                "ecommerce.core.loaders.filesystem.Loader",
                "django.template.loaders.filesystem.Loader",
                "django.template.loaders.app_directories.Loader",
            ],
            "context_processors": [
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.request",
                "django.template.context_processors.debug",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.i18n",
                "oscar.apps.communication.notifications.context_processors.notifications",
                "ecommerce.core.context_processors.metadata",
                "ecommerce.apps.checkout.context_processors.checkout",
                "ecommerce.apps.search.context_processors.search_form",
            ],
            "libraries": {
                "sorl_thumbnail": "sorl.thumbnail.templatetags.sorl_thumbnail",
            },
            "builtins": [
                "widget_tweaks.templatetags.widget_tweaks",
                "django.templatetags.i18n",
                "django.contrib.humanize.templatetags.humanize",
                "ecommerce.templatetags.basket_tags",
                "ecommerce.templatetags.display_tags",
                "ecommerce.templatetags.form_tags",
                "ecommerce.templatetags.image_tags",
                "ecommerce.templatetags.purchase_info_tags",
                "ecommerce.templatetags.reviews_tags",
                "ecommerce.templatetags.string_filters",
                "ecommerce.templatetags.url_tags",
                "ecommerce.templatetags.wishlist_tags",
            ],
            "debug": DEBUG,
        },
    },
]

MULTITENANT_TEMPLATE_DIRS = [f"{BASE_DIR}/ecommerce/tenants/%s/templates"]
