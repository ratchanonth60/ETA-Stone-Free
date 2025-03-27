import graphene
from django.core.exceptions import PermissionDenied
from graphql_jwt.decorators import login_required, staff_member_required

from ecommerce.apps.users.models import User

from .types import UserType


class UserQueries(graphene.ObjectType):
    all = graphene.List(UserType)
    by_id = graphene.Field(UserType, id=graphene.Int(required=True))
    by_username = graphene.Field(UserType, username=graphene.String(required=True))
    me = graphene.Field(UserType)

    @staff_member_required
    def resolve_all_users(root, info):
        return User.objects.all()

    @login_required
    def resolve_user_by_id(root, info, id):
        try:
            user = User.objects.get(id=id)
            if info.context.user != user and not info.context.user.is_staff:
                raise PermissionDenied("You do not have permission to view this user.")
            return user
        except User.DoesNotExist:
            raise Exception(f"User with id {id} not found")

    @login_required
    def resolve_user_by_username(root, info, username):
        try:
            user = User.objects.get(username=username)
            if info.context.user != user and not info.context.user.is_staff:
                raise PermissionDenied("You do not have permission to view this user.")
            return user
        except User.DoesNotExist:
            raise Exception(f"User with username {username} not found")

    @login_required
    def resolve_me(root, info):
        return info.context.user
