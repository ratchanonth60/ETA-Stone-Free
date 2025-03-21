from rest_framework import serializers

from ecommerce.apps.catalogue.models import (
    Category,
    Product,
    ProductClass,
    ProductImage,
)


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = "__all__"


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"


class ProductClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductClass
        fields = "__all__"


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = "__all__"
