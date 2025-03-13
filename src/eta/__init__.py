from __future__ import absolute_import, unicode_literals

from ecommerce.core.celery.celery import app as celery_app

from .settings import *

__all__ = ("celery_app",)
