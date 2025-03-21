import graphene
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext_lazy as _
from graphene.types.generic import GenericScalar
from graphene_django.forms.mutation import DjangoModelFormMutation
from graphql_jwt.decorators import login_required

from ecommerce.apps.basket.forms import BasketForm, LineAttributeForm, LineForm

from .types import Basket, BasketType, Line, LineAttribute, LineType, LineAttributeType


class BasketsMutation(DjangoModelFormMutation):
    class Meta:
        form_class = BasketForm
        return_field_name = "basket"
        exclude_fields = ("owner",)  # กำหนด owner จาก context

    basket = graphene.Field(BasketType)
    errors = GenericScalar()

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, **input):
        basket_id = input.get("id")
        instance = None

        if basket_id:
            try:
                instance = Basket.objects.get(id=basket_id, owner=info.context.user)
            except ObjectDoesNotExist:
                raise Exception(_("Basket with id '%s' not found") % basket_id)
            form = cls.get_form(root, info, instance=instance, **input)
        else:
            form = cls.get_form(root, info, **input)

        if form.is_valid():
            instance = form.save(commit=False)
            instance.owner = info.context.user
            instance.save()
            form.save_m2m()  # บันทึก ManyToManyField (vouchers)
            return cls(basket=instance)
        return cls(errors=form.errors.get_json_data())


class LineMutation(DjangoModelFormMutation):
    class Meta:
        form_class = LineForm
        return_field_name = "line"

    line = graphene.Field(LineType)
    errors = GenericScalar()

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, **input):
        line_id = input.get("id")
        instance = None

        if line_id:
            try:
                instance = Line.objects.get(id=line_id, basket__owner=info.context.user)
            except ObjectDoesNotExist:
                raise Exception(_("Line with id '%s' not found") % line_id)
            form = cls.get_form(root, info, instance=instance, **input)
        else:
            form = cls.get_form(root, info, **input)

        if form.is_valid():
            instance = form.save(commit=False)
            instance.save()
            return cls(line=instance)
        return cls(errors=form.errors.get_json_data())


class LineAttributeMutation(DjangoModelFormMutation):
    class Meta:
        form_class = LineAttributeForm
        return_field_name = "line_attribute"

    line_attribute = graphene.Field(LineAttributeType)
    errors = GenericScalar()

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, **input):
        attr_id = input.get("id")
        instance = None

        if attr_id:
            try:
                instance = LineAttribute.objects.get(
                    id=attr_id, line__basket__owner=info.context.user
                )
            except ObjectDoesNotExist:
                raise Exception(_("Line attribute with id '%s' not found") % attr_id)
            form = cls.get_form(root, info, instance=instance, **input)
        else:
            form = cls.get_form(root, info, **input)

        if form.is_valid():
            instance = form.save(commit=False)
            instance.save()
            return cls(line_attribute=instance)
        return cls(errors=form.errors.get_json_data())


class BasketMutation(graphene.ObjectType):
    create_or_update_basket = BasketsMutation.Field()
    create_or_update_line = LineMutation.Field()
    create_or_update_line_attribute = LineAttributeMutation.Field()
