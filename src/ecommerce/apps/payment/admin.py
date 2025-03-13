from django.contrib import admin

from .models import Bankcard, Source, SourceType, Transaction


class SourceAdmin(admin.ModelAdmin):
    list_display = (
        "order",
        "source_type",
        "amount_allocated",
        "amount_debited",
        "balance",
        "reference",
    )


class BankcardAdmin(admin.ModelAdmin):
    list_display = ("id", "obfuscated_number", "card_type", "expiry_month")


admin.site.register(Source, SourceAdmin)
admin.site.register(SourceType)
admin.site.register(Transaction)
admin.site.register(Bankcard, BankcardAdmin)
