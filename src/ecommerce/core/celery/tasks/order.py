from smtplib import SMTPException

from celery.utils.log import get_task_logger

from ecommerce.apps.order.models import Order
from ecommerce.apps.order.utils import OrderDispatcher
from ecommerce.core.celery.celery import app

logger = get_task_logger(__name__)


@app.task(bind=True, max_retries=0)
def send_confirmation_message(self, order_number):
    logger.info("Create order confirmation email for order_number: {}".format(order_number))
    try:
        order = Order.objects.get(number=order_number)
        extra_context = {
            'user': order.user,
            'order': order,
            'lines': list(order.lines.all())
        }
        OrderDispatcher(logger=logger).send_order_placed_email_for_user(order, extra_context)
    except SMTPException as error:
        logger.exception(
            "Create order confirmation email for order_number: {}, Error: {}".format(order_number, error))
        self.retry(countdown=60 ** self.request.retries)
