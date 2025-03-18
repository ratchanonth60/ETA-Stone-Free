import graphene

from .mutations import UserAddressMutation
from .queries import AddressQueries


class Query(graphene.ObjectType):
    address = graphene.Field(AddressQueries)


class Mutation(graphene.ObjectType):
    address = graphene.Field(UserAddressMutation)
