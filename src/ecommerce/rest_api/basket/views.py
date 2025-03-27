from rest_framework import viewsets

from ecommerce.apps.basket.models import Basket, Line

from .serializers import BasketSerializer, LineSerializer


class BasketViewSet(viewsets.ModelViewSet):
    queryset = Basket.objects.all()
    serializer_class = BasketSerializer


class LineViewSet(viewsets.ModelViewSet):
    queryset = Line.objects.all()
    serializer_class = LineSerializer
