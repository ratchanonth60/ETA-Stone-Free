import contextlib
from django.utils.translation import ngettext_lazy
from django_tables2 import Table


class DashboardTable(Table):
    caption = ngettext_lazy('%d Row', '%d Rows')

    def get_caption_display(self):
        # Allow overriding the caption with an arbitrary string that we cannot
        # interpolate the number of rows in
        with contextlib.suppress(TypeError):
            return self.caption % self.paginator.count
        return self.caption

    class Meta:
        template_name = 'eta/dashboard/table.html'
        attrs = {'class': 'table table-striped table-bordered'}
