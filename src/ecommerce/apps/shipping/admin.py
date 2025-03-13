from django.contrib import admin

from ecommerce.apps.shipping.models import OrderAndItemCharges, WeightBand, WeightBased


@admin.register(OrderAndItemCharges)
class OrderChargesAdmin(admin.ModelAdmin):
    filter_horizontal = ("countries",)
    list_display = (
        "name",
        "description",
        "price_per_order",
        "price_per_item",
        "free_shipping_threshold",
    )


class WeightBandInline(admin.TabularInline):
    model = WeightBand


@admin.register(WeightBased)
class WeightBasedAdmin(admin.ModelAdmin):
    filter_horizontal = ("countries",)
    inlines = [WeightBandInline]
