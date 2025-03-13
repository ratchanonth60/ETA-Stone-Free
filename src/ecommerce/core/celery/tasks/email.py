from smtplib import SMTPException

from celery.utils.log import get_task_logger

from ecommerce.apps.customer.utils import CustomerDispatcher
from ecommerce.apps.users.models import User
from ecommerce.core.celery.celery import app

logger = get_task_logger(__name__)


@app.task(bind=True, max_retries=3)
def send_registration_email_for_user(self, user_id):
    # Assume User is the correct model
    logger.info(f"Create register email for user_id: {user_id}")
    try:
        user = User.objects.get(id=user_id)
        extra_context = {"user": user}
        CustomerDispatcher().send_registration_email_for_user(user, extra_context)
    except SMTPException as error:
        logger.exception(
            f"Create register email for user_id: {user_id}, Error: {error}"
        )
        self.retry(countdown=60**self.request.retries)


@app.task(bind=True, max_retries=3)
def send_password_reset_email_for_user(self, user_id):
    logger.info(f"Reset email for user_id: {user_id}")
    try:
        user = User.objects.get(id=user_id)
        extra_context = {"user": user}
        CustomerDispatcher().send_password_reset_email_for_user(user, extra_context)
    except SMTPException as error:
        logger.exception(f"Reset email for user_id: {user_id}, Error: {error}")
        self.retry(countdown=60**self.request.retries)


@app.task(bind=True, max_retries=3)
def send_password_changed_email_for_user(self, user_id):
    logger.info(f"Password changed for user_id: {user_id}")
    try:
        user = User.objects.get(id=user_id)
        extra_context = {"user": user}
        CustomerDispatcher().send_password_changed_email_for_user(user, extra_context)
    except SMTPException as error:
        logger.exception(f"Password changed for user_id: {user_id}, Error: {error}")
        self.retry(countdown=60**self.request.retries)
