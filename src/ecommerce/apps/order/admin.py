from django.contrib import admin
from oscar.apps.order.models import PaymentEventQuantity

from .models import (
    BillingAddress,
    CommunicationEvent,
    Line,
    LineAttribute,
    LinePrice,
    Order,
    OrderDiscount,
    OrderNote,
    OrderStatusChange,
    PaymentEvent,
    PaymentEventType,
    ShippingAddress,
    ShippingEvent,
    ShippingEventType,
    Surcharge,
)


class LineInline(admin.TabularInline):
    model = Line
    extra = 0


class OrderAdmin(admin.ModelAdmin):
    raw_id_fields = [
        "user",
        "billing_address",
        "shipping_address",
    ]
    list_display = (
        "number",
        "total_incl_tax",
        "site",
        "user",
        "billing_address",
        "date_placed",
    )
    readonly_fields = (
        "number",
        "basket",
        "total_incl_tax",
        "total_excl_tax",
        "shipping_incl_tax",
        "shipping_excl_tax",
    )
    inlines = [LineInline]


class LineAdmin(admin.ModelAdmin):
    list_display = ("order", "product", "stockrecord", "quantity")


class LinePriceAdmin(admin.ModelAdmin):
    list_display = ("order", "line", "price_incl_tax", "quantity")


class ShippingEventTypeAdmin(admin.ModelAdmin):
    list_display = ("name",)


class PaymentEventQuantityInline(admin.TabularInline):
    model = PaymentEventQuantity
    extra = 0


class PaymentEventAdmin(admin.ModelAdmin):
    list_display = (
        "order",
        "event_type",
        "amount",
        "num_affected_lines",
        "date_created",
    )
    inlines = [PaymentEventQuantityInline]


class PaymentEventTypeAdmin(admin.ModelAdmin):
    pass


class OrderDiscountAdmin(admin.ModelAdmin):
    readonly_fields = (
        "order",
        "category",
        "offer_id",
        "offer_name",
        "voucher_id",
        "voucher_code",
        "amount",
    )
    list_display = ("order", "category", "offer", "voucher", "voucher_code", "amount")


class SurchargeAdmin(admin.ModelAdmin):
    raw_id_fields = ("order",)


admin.site.register(Order, OrderAdmin)
admin.site.register(OrderNote)
admin.site.register(OrderStatusChange)
admin.site.register(ShippingAddress)
admin.site.register(Line, LineAdmin)
admin.site.register(LinePrice, LinePriceAdmin)
admin.site.register(ShippingEvent)
admin.site.register(ShippingEventType, ShippingEventTypeAdmin)
admin.site.register(PaymentEvent, PaymentEventAdmin)
admin.site.register(PaymentEventType, PaymentEventTypeAdmin)
admin.site.register(LineAttribute)
admin.site.register(OrderDiscount, OrderDiscountAdmin)
admin.site.register(CommunicationEvent)
admin.site.register(BillingAddress)
admin.site.register(Surcharge, SurchargeAdmin)
