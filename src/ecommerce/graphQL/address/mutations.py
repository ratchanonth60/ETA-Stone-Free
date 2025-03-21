import graphene
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext_lazy as _
from graphene.types.generic import GenericScalar
from graphene_django.forms.mutation import DjangoModelFormMutation
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
        # ดึง id จาก input ถ้ามี
        address_id = input.get("id")
        instance = None

        if address_id:
            # ถ้ามี id ให้ดึง instance เดิมมา
            try:
                instance = UserAddress.objects.get(
                    id=address_id, user=info.context.user
                )
            except ObjectDoesNotExist:
                raise Exception(_("Address with id '%s' not found") % address_id)
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
