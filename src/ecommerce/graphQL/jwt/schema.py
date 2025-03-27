import graphene

from .mutation import AuthMutations, AuthRelayMutation
from .queries import UserQueries


class Mutation(graphene.ObjectType):
    auth = graphene.Field(AuthMutations)
    auth_relay = graphene.Field(AuthRelayMutation)

    def resolve_auth(self, info):
        return AuthMutations()

    def resolve_auth_relay(self, info):
        return AuthRelayMutation()


class Query(graphene.ObjectType):
    user = graphene.Field(UserQueries)

    def resolve_user(self, info):
        return UserQueries()
