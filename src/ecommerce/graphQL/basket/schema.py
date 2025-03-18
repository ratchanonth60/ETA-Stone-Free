import graphene

from .mutations import BasketMutation
from .queries import BasketQuery


class Query(graphene.ObjectType):
    basket = graphene.Field(BasketQuery)

    def resolve_basket(self, info):
        return BasketQuery()


class Mutation(graphene.ObjectType):
    basket = graphene.Field(BasketMutation)

    def resolve_basket(self, info):
        return BasketMutation()
