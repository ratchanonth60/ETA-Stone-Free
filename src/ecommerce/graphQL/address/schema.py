import graphene

from .mutations import AddressMutation
from .queries import AddressQueries


class Query(graphene.ObjectType):
    address = graphene.Field(AddressQueries)


class Mutation(graphene.ObjectType):
    address = graphene.Field(AddressMutation)

    def resolve_address(self, info):
        return AddressMutation()
