from rest_framework import serializers

from ecommerce.apps.basket.models import Basket, Line


class BasketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Basket
        fields = ['id', 'status', 'owner', 'lines']


class LineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Line
        fields = ['id', 'basket', 'line_reference', 'product', 'stockrecord', 'quantity',
                  'price_currency', 'price_excl_tax', 'price_incl_tax', 'date_created', 'date_updated']
