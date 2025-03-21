import graphene
from graphene_django import DjangoObjectType

from ecommerce.apps.address.filters import UserAddressFilter
from ecommerce.apps.address.models import Country, UserAddress


class UserAddressType(DjangoObjectType):
    class Meta:
        model = UserAddress
        fields = "__all__"
        filterset_class = UserAddressFilter
        interfaces = (graphene.relay.Node,)  # รองรับ Relay pagination

    city = graphene.String(source="line4")


class CountryType(DjangoObjectType):
    class Meta:
        model = Country
        fields = "__all__"
        interfaces = (graphene.relay.Node,)
