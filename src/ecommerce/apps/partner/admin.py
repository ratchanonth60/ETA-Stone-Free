from django.contrib import admin

from .models import Partner, StockRecord


class StockRecordAdmin(admin.ModelAdmin):
    list_display = ("product", "partner", "partner_sku", "price", "num_in_stock")
    list_filter = ("partner",)


admin.site.register(Partner)
admin.site.register(StockRecord, StockRecordAdmin)
