import os

from django.contrib.messages import constants as messages

from ecommerce import SHARED_APPS, TENANT_APPS

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-zj&vjj0q&b=tivqeuidpze37%kdok%ea(k)cjhawg051)(+^7k"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DEBUG", False)

ALLOWED_HOSTS = ["*"]

FIXTURE_DIRS = ("/ecommerce/fixtures/",)

# Application definition
INSTALLED_APPS = list(set(SHARED_APPS + TENANT_APPS))
AUTH_USER_MODEL = "users.User"

INTERNAL_IPS = [
    "127.0.0.1",
]

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

MESSAGE_TAGS = {messages.ERROR: "danger"}

# Haystack settings
HAYSTACK_CONNECTIONS = {
    "default": {
        "ENGINE": "haystack.backends.simple_backend.SimpleEngine",
    },
}

SWAGGER_SETTINGS = {"LOGIN_URL": "admin:login", "LOGOUT_URL": "admin:logout"}

SITE_ID = 1
# if not DEBUG:
#     SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
#     CSRF_TRUSTED_ORIGINS = os.environ.get("CSRF_TRUSTED_ORIGINS").split(" ")

SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"
SESSION_FILE_PATH = "django.contrib.sessions.backends.file"

# SMTP SETTINGS
EMAIL_BACKEND = (
    "django.core.mail.backends.locmem.EmailBackend"
    if DEBUG
    else "django.core.mail.backends.smtp.EmailBackend"
)
EMAIL_USE_TLS = True
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_HOST_USER = "b13m123kiss@gmail.com"
EMAIL_HOST_PASSWORD = "zuuofmqbcujdwtsq"
DEFAULT_FROM_EMAIL = "b13m123kiss@gmail.com"

DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": lambda request: DEBUG,
}

DEBUG_TOOLBAR_PANELS = [
    "debug_toolbar.panels.history.HistoryPanel",
    "debug_toolbar.panels.versions.VersionsPanel",
    "debug_toolbar.panels.timer.TimerPanel",
    "debug_toolbar.panels.settings.SettingsPanel",
    "debug_toolbar.panels.headers.HeadersPanel",
    "debug_toolbar.panels.request.RequestPanel",
    "debug_toolbar.panels.sql.SQLPanel",
    "debug_toolbar.panels.staticfiles.StaticFilesPanel",
    "debug_toolbar.panels.templates.TemplatesPanel",
    "debug_toolbar.panels.cache.CachePanel",
    "debug_toolbar.panels.signals.SignalsPanel",
    "debug_toolbar.panels.logging.LoggingPanel",
    "debug_toolbar.panels.redirects.RedirectsPanel",
    "debug_toolbar.panels.profiling.ProfilingPanel",
    "template_profiler_panel.panels.template.TemplateProfilerPanel",
]
