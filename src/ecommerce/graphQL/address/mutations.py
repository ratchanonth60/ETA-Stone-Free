import graphene
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext_lazy as _
from graphene.types.generic import GenericScalar
from graphene_django.forms.mutation import DjangoModelFormMutation
from graphql import GraphQLError
from graphql_jwt.decorators import login_required

from ecommerce.apps.address.forms import UserAddressForm

from .types import UserAddress, UserAddressType


class UserAddressMutation(DjangoModelFormMutation):
    class Meta:
        form_class = UserAddressForm
        return_field_name = "user_address"
        exclude_fields = ("user",)  # ไม่รับ user จาก input

    user_address = graphene.Field(UserAddressType)
    errors = GenericScalar()

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, **input):
        """
        Handle mutation to create or update a UserAddress.

        Args:
            root: The root object (usually None in mutations).
            info: GraphQL ResolveInfo object containing context and user.
            **input: Input data from the GraphQL mutation.

        Returns:
            UserAddressMutation: Payload with user_address or errors.

        Raises:
            GraphQLError: If the address ID is provided but not found.
        """
        address_id = input.get("id")
        instance = None

        if address_id:
            # ถ้ามี id ให้ดึง instance เดิมมา
            try:
                instance = UserAddress.objects.get(
                    id=address_id, user=info.context.user
                )
            except ObjectDoesNotExist:
                raise GraphQLError(
                    message=_("Address with id '%s' not found") % address_id,
                    extensions={"code": "ADDRESS_NOT_FOUND"},
                )
            # ส่ง instance เดิมไปที่ฟอร์มเพื่ออัปเดต
            form = cls.get_form(root, info, instance=instance, **input)
        else:
            # ถ้าไม่มี id ให้สร้างฟอร์มใหม่
            form = cls.get_form(root, info, **input)

        if form.is_valid():
            instance = form.save(commit=False)
            instance.user = info.context.user  # กำหนด user เฉพาะกรณีสร้างใหม่
            instance.save()
            return cls(user_address=instance)

        return cls(errors=form.errors.get_json_data())


class AddressMutation(graphene.ObjectType):
    create_or_update = UserAddressMutation.Field()
