from django.utils.translation import gettext_lazy as _

from ecommerce.apps.dashboard.reports.reports import (
    ReportCSVFormatter,
    ReportGenerator,
    ReportHTMLFormatter,
)

from .models import Voucher


class VoucherReportCSVFormatter(ReportCSVFormatter):
    filename_template = "voucher-performance.csv"

    def generate_csv(self, response, vouchers):
        writer = self.get_csv_writer(response)
        header_row = [
            _("Voucher code"),
            _("Added to a basket"),
            _("Used in an order"),
            _("Total discount"),
        ]
        writer.writerow(header_row)

        for voucher in vouchers:
            row = [
                voucher.code,
                voucher.num_basket_additions,
                voucher.num_orders,
                voucher.total_discount,
            ]
            writer.writerow(row)


class VoucherReportHTMLFormatter(ReportHTMLFormatter):
    filename_template = "eta/dashboard/reports/partials/voucher_report.html"


class VoucherReportGenerator(ReportGenerator):
    code = "vouchers"
    description = _("Voucher performance")
    model_class = Voucher

    formatters = {
        "CSV_formatter": VoucherReportCSVFormatter,
        "HTML_formatter": VoucherReportHTMLFormatter,
    }
