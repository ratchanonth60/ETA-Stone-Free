from django_filters import FilterSet, OrderingFilter

from .models import UserAddress, Country


# create filter class for address
class UserAddressFilter(FilterSet):
    class Meta:
        model = UserAddress
        fields = {
            "user__username": ["exact", "icontains"],  # กรองตาม username ของ user
            "title": ["exact"],
            "first_name": ["exact", "icontains"],
            "last_name": ["exact", "icontains"],
            "line1": ["exact", "icontains"],
            "postcode": ["exact"],
            "country__iso_3166_1_a2": ["exact"],  # กรองตามรหัสประเทศ
            "is_default_for_shipping": ["exact"],
            "is_default_for_billing": ["exact"],
            "num_orders_as_shipping_address": [
                "gte",
                "lte",
            ],  # มากกว่าหรือเท่ากับ, น้อยกว่าหรือเท่ากับ
        }

    order_by = OrderingFilter(
        fields=(
            ("postcode", "postcode"),
            ("date_created", "date_created"),
            ("num_orders_as_shipping_address", "num_orders_as_shipping_address"),
            ("num_orders_as_billing_address", "num_orders_as_billing_address"),
            ("first_name", "first_name"),
            ("last_name", "last_name"),
        )
    )


class CountryFilter(FilterSet):
    class Meta:
        model = Country
        fields = {
            "iso_3166_1_a2": ["exact"],
            "printable_name": ["exact", "icontains"],
            "is_shipping_country": ["exact"],
            "display_order": ["gte", "lte"],
        }
