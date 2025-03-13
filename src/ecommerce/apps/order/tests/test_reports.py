import datetime

from django.utils.timezone import now

from ecommerce.apps.order import reports
from ecommerce.test.testcases import TestCase


class TestOrderReportGenerator(TestCase):
    def test_generate_csv_no_filter(self):
        generator = reports.OrderReportGenerator(formatter='CSV')
        generator.generate()

    def test_generate_csv_start_and_end_date(self):
        start_date = now() - datetime.timedelta(days=28)
        end_date = now() + datetime.timedelta(days=28)

        generator = reports.OrderReportGenerator(
            start_date=start_date, end_date=end_date, formatter='CSV')
        generator.generate()
