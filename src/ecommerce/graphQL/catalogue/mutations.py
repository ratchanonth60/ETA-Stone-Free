import graphene
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext_lazy as _
from graphene.types.generic import GenericScalar
from graphene_django.forms.mutation import DjangoModelFormMutation
from graphql_jwt.decorators import login_required

from ecommerce.apps.catalogue.forms import (
    AttributeOptionForm,
    AttributeOptionGroupForm,
    CategoryForm,
    OptionForm,
    ProductAttributeForm,
    ProductAttributeValueForm,
    ProductCategoryForm,
    ProductClassForm,
    ProductForm,
    ProductImageForm,
    ProductRecommendationForm,
)
from ecommerce.apps.catalogue.models import (
    AttributeOption,
    AttributeOptionGroup,
    Category,
    Option,
    Product,
    ProductAttribute,
    ProductAttributeValue,
    ProductCategory,
    ProductClass,
    ProductImage,
    ProductRecommendation,
)

from .types import (
    AttributeOptionGroupType,
    AttributeOptionType,
    CategoryType,
    OptionType,
    ProductAttributeType,
    ProductAttributeValueType,
    ProductCategoryType,
    ProductClassType,
    ProductImageType,
    ProductRecommendationType,
    ProductType,
)


class ProductClassMutation(DjangoModelFormMutation):
    class Meta:
        form_class = ProductClassForm
        return_field_name = "product_class"

    product_class = graphene.Field(ProductClassType)
    errors = GenericScalar()

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, **input):
        instance_id = input.get("id")
        instance = None
        if instance_id:
            try:
                instance = ProductClass.objects.get(id=instance_id)
            except ObjectDoesNotExist:
                raise Exception(_("ProductClass with id '%s' not found") % instance_id)
            form = cls.get_form(root, info, instance=instance, **input)
        else:
            form = cls.get_form(root, info, **input)
        if form.is_valid():
            instance = form.save()
            return cls(product_class=instance)
        return cls(errors=form.errors.get_json_data())


class CategoryMutation(DjangoModelFormMutation):
    class Meta:
        form_class = CategoryForm
        return_field_name = "category"

    category = graphene.Field(CategoryType)
    errors = GenericScalar()

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, **input):
        instance_id = input.get("id")
        instance = None
        if instance_id:
            try:
                instance = Category.objects.get(id=instance_id)
            except ObjectDoesNotExist:
                raise Exception(_("Category with id '%s' not found") % instance_id)
            form = cls.get_form(root, info, instance=instance, **input)
        else:
            form = cls.get_form(root, info, **input)
        if form.is_valid():
            instance = form.save()
            return cls(category=instance)
        return cls(errors=form.errors.get_json_data())


class ProductCategoryMutation(DjangoModelFormMutation):
    class Meta:
        form_class = ProductCategoryForm
        return_field_name = "product_category"

    product_category = graphene.Field(ProductCategoryType)
    errors = GenericScalar()

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, **input):
        instance_id = input.get("id")
        instance = None
        if instance_id:
            try:
                instance = ProductCategory.objects.get(id=instance_id)
            except ObjectDoesNotExist:
                raise Exception(
                    _("ProductCategory with id '%s' not found") % instance_id
                )
            form = cls.get_form(root, info, instance=instance, **input)
        else:
            form = cls.get_form(root, info, **input)
        if form.is_valid():
            instance = form.save()
            return cls(product_category=instance)
        return cls(errors=form.errors.get_json_data())


class ProductMutation(DjangoModelFormMutation):
    class Meta:
        form_class = ProductForm
        return_field_name = "product"

    product = graphene.Field(ProductType)
    errors = GenericScalar()

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, **input):
        instance_id = input.get("id")
        instance = None
        if instance_id:
            try:
                instance = Product.objects.get(id=instance_id)
            except ObjectDoesNotExist:
                raise Exception(_("Product with id '%s' not found") % instance_id)
            form = cls.get_form(root, info, instance=instance, **input)
        else:
            form = cls.get_form(root, info, **input)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.save()
            form.save_m2m()  # บันทึก ManyToMany fields
            return cls(product=instance)
        return cls(errors=form.errors.get_json_data())


class ProductRecommendationMutation(DjangoModelFormMutation):
    class Meta:
        form_class = ProductRecommendationForm
        return_field_name = "product_recommendation"

    product_recommendation = graphene.Field(ProductRecommendationType)
    errors = GenericScalar()

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, **input):
        instance_id = input.get("id")
        instance = None
        if instance_id:
            try:
                instance = ProductRecommendation.objects.get(id=instance_id)
            except ObjectDoesNotExist:
                raise Exception(
                    _("ProductRecommendation with id '%s' not found") % instance_id
                )
            form = cls.get_form(root, info, instance=instance, **input)
        else:
            form = cls.get_form(root, info, **input)
        if form.is_valid():
            instance = form.save()
            return cls(product_recommendation=instance)
        return cls(errors=form.errors.get_json_data())


class ProductAttributeMutation(DjangoModelFormMutation):
    class Meta:
        form_class = ProductAttributeForm
        return_field_name = "product_attribute"

    product_attribute = graphene.Field(ProductAttributeType)
    errors = GenericScalar()

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, **input):
        instance_id = input.get("id")
        instance = None
        if instance_id:
            try:
                instance = ProductAttribute.objects.get(id=instance_id)
            except ObjectDoesNotExist:
                raise Exception(
                    _("ProductAttribute with id '%s' not found") % instance_id
                )
            form = cls.get_form(root, info, instance=instance, **input)
        else:
            form = cls.get_form(root, info, **input)
        if form.is_valid():
            instance = form.save()
            return cls(product_attribute=instance)
        return cls(errors=form.errors.get_json_data())


class ProductAttributeValueMutation(DjangoModelFormMutation):
    class Meta:
        form_class = ProductAttributeValueForm
        return_field_name = "product_attribute_value"

    product_attribute_value = graphene.Field(ProductAttributeValueType)
    errors = GenericScalar()

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, **input):
        instance_id = input.get("id")
        instance = None
        if instance_id:
            try:
                instance = ProductAttributeValue.objects.get(id=instance_id)
            except ObjectDoesNotExist:
                raise Exception(
                    _("ProductAttributeValue with id '%s' not found") % instance_id
                )
            form = cls.get_form(root, info, instance=instance, **input)
        else:
            form = cls.get_form(root, info, **input)
        if form.is_valid():
            instance = form.save()
            return cls(product_attribute_value=instance)
        return cls(errors=form.errors.get_json_data())


class AttributeOptionGroupMutation(DjangoModelFormMutation):
    class Meta:
        form_class = AttributeOptionGroupForm
        return_field_name = "attribute_option_group"

    attribute_option_group = graphene.Field(AttributeOptionGroupType)
    errors = GenericScalar()

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, **input):
        instance_id = input.get("id")
        instance = None
        if instance_id:
            try:
                instance = AttributeOptionGroup.objects.get(id=instance_id)
            except ObjectDoesNotExist:
                raise Exception(
                    _("AttributeOptionGroup with id '%s' not found") % instance_id
                )
            form = cls.get_form(root, info, instance=instance, **input)
        else:
            form = cls.get_form(root, info, **input)
        if form.is_valid():
            instance = form.save()
            return cls(attribute_option_group=instance)
        return cls(errors=form.errors.get_json_data())


class AttributeOptionMutation(DjangoModelFormMutation):
    class Meta:
        form_class = AttributeOptionForm
        return_field_name = "attribute_option"

    attribute_option = graphene.Field(AttributeOptionType)
    errors = GenericScalar()

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, **input):
        instance_id = input.get("id")
        instance = None
        if instance_id:
            try:
                instance = AttributeOption.objects.get(id=instance_id)
            except ObjectDoesNotExist:
                raise Exception(
                    _("AttributeOption with id '%s' not found") % instance_id
                )
            form = cls.get_form(root, info, instance=instance, **input)
        else:
            form = cls.get_form(root, info, **input)
        if form.is_valid():
            instance = form.save()
            return cls(attribute_option=instance)
        return cls(errors=form.errors.get_json_data())


class OptionMutation(DjangoModelFormMutation):
    class Meta:
        form_class = OptionForm
        return_field_name = "option"

    option = graphene.Field(OptionType)
    errors = GenericScalar()

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, **input):
        instance_id = input.get("id")
        instance = None
        if instance_id:
            try:
                instance = Option.objects.get(id=instance_id)
            except ObjectDoesNotExist:
                raise Exception(_("Option with id '%s' not found") % instance_id)
            form = cls.get_form(root, info, instance=instance, **input)
        else:
            form = cls.get_form(root, info, **input)
        if form.is_valid():
            instance = form.save()
            return cls(option=instance)
        return cls(errors=form.errors.get_json_data())


class ProductImageMutation(DjangoModelFormMutation):
    class Meta:
        form_class = ProductImageForm
        return_field_name = "product_image"

    product_image = graphene.Field(ProductImageType)
    errors = GenericScalar()

    @classmethod
    @login_required
    def mutate_and_get_payload(cls, root, info, **input):
        instance_id = input.get("id")
        instance = None
        if instance_id:
            try:
                instance = ProductImage.objects.get(id=instance_id)
            except ObjectDoesNotExist:
                raise Exception(_("ProductImage with id '%s' not found") % instance_id)
            form = cls.get_form(root, info, instance=instance, **input)
        else:
            form = cls.get_form(root, info, **input)
        if form.is_valid():
            instance = form.save()
            return cls(product_image=instance)
        return cls(errors=form.errors.get_json_data())


class CatalogueMutation(graphene.ObjectType):
    create_or_update_product_class = ProductClassMutation.Field()
    create_or_update_category = CategoryMutation.Field()
    create_or_update_product_category = ProductCategoryMutation.Field()
    create_or_update_product = ProductMutation.Field()
    create_or_update_product_recommendation = ProductRecommendationMutation.Field()
    create_or_update_product_attribute = ProductAttributeMutation.Field()
    create_or_update_product_attribute_value = ProductAttributeValueMutation.Field()
    create_or_update_attribute_option_group = AttributeOptionGroupMutation.Field()
    create_or_update_attribute_option = AttributeOptionMutation.Field()
    create_or_update_option = OptionMutation.Field()
    create_or_update_product_image = ProductImageMutation.Field()
