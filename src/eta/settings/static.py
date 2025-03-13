# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/
import os

from .base import BASE_DIR, DEBUG

# def location(x):
#     return os.path.join(
#         os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), x
#     )


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
if not DEBUG:
    # Media and static
    STATIC_ROOT = os.environ.get("STATIC_ROOT", "/var/www/pod/static")
    MEDIA_ROOT = os.environ.get("MEDIA_ROOT", "/var/www/pod/media")

# if not DEBUG:
#     REWRITE_STATIC_URLS = True
# STATICFILES_STORAGE = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"
# STATICFILES_DIRS = (location("static/"),)

# PUBLIC_ROOT = location("public")
# MULTITENANT_RELATIVE_STATIC_ROOT = ""  # (default: create sub-directory for each tenant)
# MULTITENANT_STATICFILES_DIRS = [
#     os.path.join(BASE_DIR, "static/%s"),
# ]
# MULTITENANT_STATICFILES_DIRS = []

# STATICFILES_FINDERS = (
#     "django_tenants.staticfiles.finders.TenantFileSystemFinder",  # Must be first
#     "django.contrib.staticfiles.finders.FileSystemFinder",
#     "django.contrib.staticfiles.finders.AppDirectoriesFinder",
#     "compressor.finders.CompressorFinder",
# )
STATICFILES_STORAGE = "django_tenants.staticfiles.storage.TenantStaticFilesStorage"

DEFAULT_FILE_STORAGE = "django_tenants.files.storage.TenantFileSystemStorage"

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
