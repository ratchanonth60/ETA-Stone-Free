import graphene
from graphql_jwt.decorators import login_required

from ecommerce.apps.address.models import UserAddress, Country

from .types import UserAddressType


class CreateUserAddress(graphene.Mutation):
    class Arguments:
        title = graphene.String()
        first_name = graphene.String()
        last_name = graphene.String()
        line1 = graphene.String(required=True)
        line2 = graphene.String()
        line3 = graphene.String()
        line4 = graphene.String()
        state = graphene.String()
        postcode = graphene.String()
        country_iso_3166_1_a2 = graphene.String(required=True)
        is_default_for_shipping = graphene.Boolean()
        is_default_for_billing = graphene.Boolean()

    user_address = graphene.Field(UserAddressType)

    @login_required
    def mutate(self, info, **kwargs):
        country = Country.objects.get(iso_3166_1_a2=kwargs.pop("country_iso_3166_1_a2"))  # type: ignore
        user_address = UserAddress(user=info.context.user, country=country, **kwargs)
        user_address.save()
        return CreateUserAddress(user_address=user_address)  # type: ignore


class UserAddressMutation(graphene.ObjectType):
    create = CreateUserAddress.Field()
