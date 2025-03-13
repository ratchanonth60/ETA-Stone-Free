from rest_framework import viewsets

from ecommerce.apps.catalogue.models import (
    Category,
    Product,
    ProductClass,
    ProductImage,
)

from .serializers import (
    CategorySerializer,
    ProductClassSerializer,
    ProductImageSerializer,
    ProductSerializer,
)


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class ProductClassViewSet(viewsets.ModelViewSet):
    queryset = ProductClass.objects.all()
    serializer_class = ProductClassSerializer


class ProductImageViewSet(viewsets.ModelViewSet):
    queryset = ProductImage.objects.all()
    serializer_class = ProductImageSerializer
