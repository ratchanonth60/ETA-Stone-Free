import graphene
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext_lazy as _
from graphene.types.generic import GenericScalar
from graphene_django.forms.mutation import DjangoModelFormMutation
from graphql.error import GraphQLError
from graphql_jwt.decorators import login_required

from ecommerce.apps.basket.forms import BasketForm, LineAttributeForm, LineForm

from .types import Basket, BasketType, Line, LineAttribute, LineAttributeType, LineType


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
        """
        Handle mutation to create or update a Basket.

        Args:
            root: The root object (usually None in mutations).
            info: GraphQL ResolveInfo object containing context and user.
            **input: Input data from the GraphQL mutation, including optional 'id'.

        Returns:
            BasketsMutation: Payload with basket or errors.

        Raises:
            GraphQLError: If the basket ID is provided but not found for the current user.
        """
        basket_id = input.get("id")
        instance = None

        if basket_id:
            try:
                instance = Basket.objects.get(id=basket_id, owner=info.context.user)
            except ObjectDoesNotExist:
                raise GraphQLError(_("Basket with id '%s' not found") % basket_id)
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
        """
        Handle mutation to create or update a Line.

        Args:
            root: The root object (usually None in mutations).
            info: GraphQL ResolveInfo object containing context and user.
            **input: Input data from the GraphQL mutation, including optional 'id'.

        Returns:
            LineMutation: Payload with line or errors.

        Raises:
            GraphQLError: If the line ID is provided but not found in a basket owned by the current user.
        """
        line_id = input.get("id")
        instance = None

        if line_id:
            try:
                instance = Line.objects.get(id=line_id, basket__owner=info.context.user)
            except ObjectDoesNotExist:
                raise GraphQLError(_("Line with id '%s' not found") % line_id)
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
        """
        Handle mutation to create or update a LineAttribute.

        Args:
            root: The root object (usually None in mutations).
            info: GraphQL ResolveInfo object containing context and user.
            **input: Input data from the GraphQL mutation, including optional 'id'.

        Returns:
            LineAttributeMutation: Payload with line_attribute or errors.

        Raises:
            GraphQLError: If the line attribute ID is provided but not found in a line
                         within a basket owned by the current user.
        """
        attr_id = input.get("id")
        instance = None

        if attr_id:
            try:
                instance = LineAttribute.objects.get(
                    id=attr_id, line__basket__owner=info.context.user
                )
            except ObjectDoesNotExist:
                raise GraphQLError(_("Line attribute with id '%s' not found") % attr_id)
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
