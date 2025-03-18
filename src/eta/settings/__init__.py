from .auth import *  # noqa: F403
from .aws import *  # noqa: F403
from .base import *  # noqa: F403  # Load base settings (including INSTALLED_APPS) first
from .caching import *  # noqa: F403
from .celery_conf import *  # noqa: F403
from .db import *  # noqa: F403  # DATABASES should come after base
from .graphql import *  # noqa: F403
from .middleware import *  # noqa: F403
from .oscar import *  # noqa: F403
from .rest_framework import *  # noqa: F403
from .static import *  # noqa: F403
from .stripe import *  # noqa: F403
from .tenant import *  # noqa: F403  # Tenant settings last to override if needed
from .timezone import *  # noqa: F403

LOGGING = {
    "version": 1,
    # Setting this to True may disable preexisting loggers, for eg. Celery
    "disable_existing_loggers": False,
    "formatters": {
        "short": {
            "format": "[%(asctime)s]-[%(levelname)-7s]: %(message)s",
            "datefmt": "%H:%M:%S",
        },
        "verbose": {
            "format": "[%(asctime)s]-[%(levelname)-7s]-[%(filename)s]:%(lineno)s | %(funcName)s | %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "simple": {"format": "%(levelname)s %(message)s"},
        "tenant_context": {
            "format": "[%(schema_name)s:%(domain_url)s]"
            "%(levelname)-7s %(asctime)s %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "short",
            "level": "DEBUG",
            "filters": ["tenant_context"],
        },
        "mail_admins": {
            "level": "ERROR",
            "email_backend": "django.core.mail.backends.smtp.EmailBackend",
            "class": "django.utils.log.AdminEmailHandler",
        },
        "sentry": {
            "level": "ERROR",  # To capture more than ERROR, change to WARNING, INFO, etc.
            "class": "raven.contrib.django.raven_compat.handlers.SentryHandler",
            "tags": {"custom-tag": "x"},
        },
    },
    "loggers": {
        "django.request": {
            "handlers": ["mail_admins"],
            "level": "ERROR",
            "propagate": True,
        },
        "django.template": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "django": {
            "handlers": ["console"],
            "propagate": False,
            "level": "INFO",
        },
        "django.security.DisallowedHost": {
            "handlers": [],
            "propagate": False,
        },
        "suds": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": True,
        },
        "django.db.backends": {
            "handlers": ["console"],
            "propagate": True,
            "level": "WARNING",
        },
        "factory.generate": {
            "handlers": ["console"],
            "propagate": True,
            "level": "WARNING",
        },
        "factory.containers": {
            "handlers": ["console"],
            "propagate": True,
            "level": "WARNING",
        },
        "raven": {
            "level": "INFO",
            "handlers": ["console"],
            "propagate": False,
        },
        "sentry.errors": {
            "level": "DEBUG",
            "handlers": ["console"],
            "propagate": False,
        },
        "sorl.thumbnail": {
            "handlers": ["console"],
            "propagate": True,
            "level": "INFO",
        },
    },
    "root": {
        "level": "DEBUG",
        "handlers": ["console"],
    },
    "filters": {
        "tenant_context": {"()": "django_tenants.log.TenantContextFilter"},
    },
}
