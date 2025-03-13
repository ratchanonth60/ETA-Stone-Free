import functools

from celery.utils.log import get_task_logger
from django.db import connection
from django_tenants.utils import get_tenant_model, tenant_context

from ecommerce.core.celery.celery import app

logger = get_task_logger(__name__)


def tenant_aware_periodic_task(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        for tenant in get_tenant_model().objects.exclude(schema_name="public"):
            with tenant_context(tenant):
                try:
                    func(*args, **kwargs)
                except Exception:
                    logger.exception(f"{func} periodic task error on {tenant}")

    return wrapper


@app.task
@tenant_aware_periodic_task
def test_tenant_ware_periodic_test():
    my_task.delay()


@app.task
def my_task():
    logger.info(f"test connection: {connection.schema_name}")


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
