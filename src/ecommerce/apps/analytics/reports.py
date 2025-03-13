from django.utils.translation import gettext_lazy as _

from ecommerce.apps.analytics.models import ProductRecord, UserRecord
from ecommerce.apps.dashboard.reports.reports import (
    ReportCSVFormatter,
    ReportGenerator,
    ReportHTMLFormatter,
)


class ProductReportCSVFormatter(ReportCSVFormatter):
    filename_template = "conditional-offer-performance.csv"

    def generate_csv(self, response, products):
        writer = self.get_csv_writer(response)
        header_row = [_("Product"), _("Views"), _("Basket additions"), _("Purchases")]
        writer.writerow(header_row)

        for record in products:
            row = [
                record.product,
                record.num_views,
                record.num_basket_additions,
                record.num_purchases,
            ]
            writer.writerow(row)


class ProductReportHTMLFormatter(ReportHTMLFormatter):
    filename_template = "eta/dashboard/reports/partials/product_report.html"


class ProductReportGenerator(ReportGenerator):
    code = "product_analytics"
    description = _("Product analytics")
    model_class = ProductRecord

    formatters = {
        "CSV_formatter": ProductReportCSVFormatter,
        "HTML_formatter": ProductReportHTMLFormatter,
    }

    def report_description(self):
        return self.description

    def is_available_to(self, user):
        return user.is_staff


class UserReportCSVFormatter(ReportCSVFormatter):
    filename_template = "user-analytics.csv"

    def generate_csv(self, response, users):
        writer = self.get_csv_writer(response)
        header_row = [
            _("Name"),
            _("Date registered"),
            _("Product views"),
            _("Basket additions"),
            _("Orders"),
            _("Order lines"),
            _("Order items"),
            _("Total spent"),
            _("Date of last order"),
        ]
        writer.writerow(header_row)

        for record in users:
            row = [
                record.user.get_full_name(),
                self.format_date(record.user.date_joined),
                record.num_product_views,
                record.num_basket_additions,
                record.num_orders,
                record.num_order_lines,
                record.num_order_items,
                record.total_spent,
                self.format_datetime(record.date_last_order),
            ]
            writer.writerow(row)


class UserReportHTMLFormatter(ReportHTMLFormatter):
    filename_template = "eta/dashboard/reports/partials/user_report.html"


class UserReportGenerator(ReportGenerator):
    code = "user_analytics"
    description = _("User analytics")
    queryset = UserRecord._default_manager.select_related().all()

    formatters = {
        "CSV_formatter": UserReportCSVFormatter,
        "HTML_formatter": UserReportHTMLFormatter,
    }

    def is_available_to(self, user):
        return user.is_staff
