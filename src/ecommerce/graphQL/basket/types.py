import graphene
from graphene_django import DjangoObjectType

from ecommerce.apps.basket.models import Basket, Line, LineAttribute


# LineAttribute Type
class LineAttributeType(DjangoObjectType):
    class Meta:
        model = LineAttribute
        fields = ("id", "line", "option", "value")


# Line Type
class LineType(DjangoObjectType):
    class Meta:
        model = Line
        fields = (
            "id",
            "basket",
            "line_reference",
            "product",
            "stockrecord",
            "quantity",
            "price_currency",
            "price_excl_tax",
            "price_incl_tax",
            "date_created",
            "date_updated",
            "attributes",
        )


# First, create a type for Basket
class BasketType(DjangoObjectType):
    class Meta:
        model = Basket
        fields = (
            "id",
            "owner",
            "status",
            "vouchers",
            "date_created",
            "date_merged",
            "date_submitted",
            "total_excl_tax",
            "total_tax",
            "total_incl_tax",
            "total_discount",
            "num_items",
            "is_empty",
            "can_be_edited",
            "currency",
        )

    # Custom resolvers for computed properties
    total_excl_tax = graphene.Decimal()
    total_tax = graphene.Decimal()
    total_incl_tax = graphene.Decimal()
    total_discount = graphene.Decimal()
    num_items = graphene.Int()
    is_empty = graphene.Boolean()
    can_be_edited = graphene.Boolean()
    currency = graphene.String()

    def resolve_total_excl_tax(self, info):
        return self.total_excl_tax

    def resolve_total_tax(self, info):
        return self.total_tax

    def resolve_total_incl_tax(self, info):
        return self.total_incl_tax

    def resolve_total_discount(self, info):
        return self.total_discount

    def resolve_num_items(self, info):
        return self.num_items

    def resolve_is_empty(self, info):
        return self.is_empty

    def resolve_can_be_edited(self, info):
        return self.can_be_edited

    def resolve_currency(self, info):
        return self.currency
