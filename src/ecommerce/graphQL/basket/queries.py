import graphene
from graphql_jwt.decorators import login_required

from .types import Basket, BasketType, Line, LineAttribute, LineAttributeType, LineType


class BasketQuery(graphene.ObjectType):
    by_id = graphene.Field(BasketType, id=graphene.ID())
    all = graphene.List(BasketType)
    user_baskets = graphene.List(BasketType)
    line = graphene.Field(LineType, id=graphene.ID())
    lines = graphene.List(LineType, basket_id=graphene.ID(required=True))
    line_attributes = graphene.List(
        LineAttributeType, line_id=graphene.ID(required=True)
    )

    @login_required
    def resolve_basket(self, info, id):
        try:
            basket = Basket.objects.get(id=id)
            if basket.owner != info.context.user:
                raise Exception("You don't have permission to view this basket")
            return basket
        except Basket.DoesNotExist:
            return None

    @login_required
    def resolve_baskets(self, info):
        return Basket.objects.filter(owner=info.context.user)

    @login_required
    def resolve_user_baskets(self, info):
        return Basket.objects.filter(owner=info.context.user)

    @login_required
    def resolve_line(self, info, id):
        try:
            line = Line.objects.get(id=id)
            if line.basket.owner != info.context.user:
                raise Exception("You don't have permission to view this line")
            return line
        except Line.DoesNotExist:
            return None

    @login_required
    def resolve_lines(self, info, basket_id):
        try:
            basket = Basket.objects.get(id=basket_id)
            if basket.owner != info.context.user:
                raise Exception("You don't have permission to view these lines")
            return Line.objects.filter(basket=basket)
        except Basket.DoesNotExist:
            raise Exception("Basket not found")

    @login_required
    def resolve_line_attributes(self, info, line_id):
        try:
            line = Line.objects.get(id=line_id)
            if line.basket.owner != info.context.user:
                raise Exception(
                    "You don't have permission to view these line attributes"
                )
            return LineAttribute.objects.filter(line=line)
        except Line.DoesNotExist:
            raise Exception("Line not found")
