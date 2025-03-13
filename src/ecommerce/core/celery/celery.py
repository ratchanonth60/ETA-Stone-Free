import os

from celery.utils.log import get_task_logger
from tenant_schemas_celery.app import CeleryApp as TenantAwareCeleryApp

os.environ.setdefault("DJANGO_SETTINGS_MODULE", os.getenv("DJANGO_SETTINGS_MODULE", ""))
logger = get_task_logger(__name__)

app = TenantAwareCeleryApp("eta")

app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
