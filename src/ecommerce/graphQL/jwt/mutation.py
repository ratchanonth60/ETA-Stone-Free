import graphene
import graphql_jwt
from graphene.types.generic import GenericScalar
from graphql_jwt.mixins import ObtainJSONWebTokenMixin

from .types import User, UserType


class ObtainJSONWebToken(graphene.Mutation, ObtainJSONWebTokenMixin):
    access_token = graphene.String()
    refresh_token = graphene.String()
    payload = GenericScalar()
    refresh_expires_in = graphene.Int()
    user = graphene.Field(UserType)

    @classmethod
    def Field(cls, *args, **kwargs):
        cls._meta.arguments.update(
            {
                User.USERNAME_FIELD: graphene.String(required=True),
                "password": graphene.String(required=True),
            },
        )
        return super().Field(*args, **kwargs)

    @classmethod
    def mutate(cls, root, info, **kwargs):
        result = graphql_jwt.ObtainJSONWebToken.mutate(root, info, **kwargs)
        return cls(
            access_token=result.token,
            refresh_token=result.refresh_token,
            payload=result.payload,
            refresh_expires_in=result.refresh_expires_in,
            user=info.context.user,
        )


class DeleteJSONWebTokenCookie(graphql_jwt.DeleteJSONWebTokenCookie):
    pass


class VerifyToken(graphql_jwt.Verify):
    pass


class RefreshToken(graphql_jwt.Refresh):
    pass


class RevokeToken(graphql_jwt.Revoke):
    pass


class AuthMutations(graphene.ObjectType):
    login = ObtainJSONWebToken.Field()
    verify_token = VerifyToken.Field()
    refresh_token = RefreshToken.Field()
    revoke_token = RevokeToken.Field()
    delete_token_cookie = DeleteJSONWebTokenCookie.Field()
    delete_refresh_token_cookie = graphql_jwt.DeleteRefreshTokenCookie.Field()


class AuthRelayMutation(graphene.ObjectType):
    login = graphql_jwt.relay.ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.relay.Verify.Field()
    refresh_token = graphql_jwt.relay.Refresh.Field()
    delete_token_cookie = graphql_jwt.relay.DeleteJSONWebTokenCookie.Field()

    # Long running refresh tokens
    revoke_token = graphql_jwt.relay.Revoke.Field()

    delete_refresh_token_cookie = graphql_jwt.relay.DeleteRefreshTokenCookie.Field()
