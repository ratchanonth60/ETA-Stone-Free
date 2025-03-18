import graphene
from graphene_django.filter import DjangoFilterConnectionField
from graphql_jwt.decorators import login_required

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


class ProductQuery(graphene.ObjectType):
    by_id = graphene.Field(ProductType, id=graphene.ID())
    filter = DjangoFilterConnectionField(
        ProductType,
    )

    @login_required
    def resolve_by_id(self, info, id):
        try:
            return Product.objects.get(id=id)
        except Product.DoesNotExist:
            raise Exception("Product not found")


class CategoryQuery(graphene.ObjectType):
    by_id = graphene.Field(CategoryType, id=graphene.ID())
    filter = DjangoFilterConnectionField(
        CategoryType,
    )

    @login_required
    def resolve_by_id(self, info, id):
        try:
            return Category.objects.get(id=id)
        except Category.DoesNotExist:
            raise Exception("Category not found")


class ProductClassQuery(graphene.ObjectType):
    by_id = graphene.Field(ProductClassType, id=graphene.ID())
    filter = DjangoFilterConnectionField(
        ProductClassType,
    )

    @login_required
    def resolve_by_id(self, info, id):
        try:
            return ProductClass.objects.get(id=id)
        except ProductClass.DoesNotExist:
            raise Exception("Product class not found")


class ProductCategoryQuery(graphene.ObjectType):
    by_id = graphene.Field(ProductCategoryType, id=graphene.ID())
    filter = DjangoFilterConnectionField(
        ProductCategoryType,
    )

    @login_required
    def resolve_by_id(self, info, id):
        try:
            return ProductCategory.objects.get(id=id)
        except ProductCategory.DoesNotExist:
            raise Exception("Product category not found")


class ProductRecommendationQuery(graphene.ObjectType):
    by_id = graphene.Field(ProductRecommendationType, id=graphene.ID())
    filter = DjangoFilterConnectionField(
        ProductRecommendationType,
    )

    @login_required
    def resolve_by_id(self, info, id):
        try:
            return ProductRecommendation.objects.get(id=id)
        except ProductRecommendation.DoesNotExist:
            raise Exception("Product recommendation not found")


class ProductAttributeQuery(graphene.ObjectType):
    by_id = graphene.Field(ProductAttributeType, id=graphene.ID())
    filter = DjangoFilterConnectionField(
        ProductAttributeType,
    )

    @login_required
    def resolve_by_id(self, info, id):
        try:
            return ProductAttribute.objects.get(id=id)
        except ProductAttribute.DoesNotExist:
            raise Exception("Product attribute not found")


class ProductAttributeValueQuery(graphene.ObjectType):
    by_id = graphene.Field(ProductAttributeValueType, id=graphene.ID())
    filter = DjangoFilterConnectionField(
        ProductAttributeValueType,
    )

    @login_required
    def resolve_by_id(self, info, id):
        try:
            return ProductAttributeValue.objects.get(id=id)
        except ProductAttributeValue.DoesNotExist:
            raise Exception("Product attribute value not found")


class AttributeOptionGroupQuery(graphene.ObjectType):
    by_id = graphene.Field(AttributeOptionGroupType, id=graphene.ID())
    filter = DjangoFilterConnectionField(AttributeOptionGroupType)

    @login_required
    def resolve_by_id(self, info, id):
        try:
            return AttributeOptionGroup.objects.get(id=id)
        except AttributeOptionGroup.DoesNotExist:
            raise Exception("Attribute option group not found")


class AttributeOptionQuery(graphene.ObjectType):
    by_id = graphene.Field(AttributeOptionType, id=graphene.ID())
    filter = DjangoFilterConnectionField(AttributeOptionType)

    @login_required
    def resolve_by_id(self, info, id):
        try:
            return AttributeOption.objects.get(id=id)
        except AttributeOption.DoesNotExist:
            raise Exception("Attribute option not found")


class OptionQuery(graphene.ObjectType):
    by_id = graphene.Field(OptionType, id=graphene.ID())
    filter = DjangoFilterConnectionField(
        OptionType,
    )

    @login_required
    def resolve_by_id(self, info, id):
        try:
            return Option.objects.get(id=id)
        except Option.DoesNotExist:
            raise Exception("Option not found")


class ProductImageQuery(graphene.ObjectType):
    by_id = graphene.Field(ProductImageType, id=graphene.ID())
    filter = DjangoFilterConnectionField(
        ProductImageType,
    )

    @login_required
    def resolve_by_id(self, info, id):
        try:
            return ProductImage.objects.get(id=id)
        except ProductImage.DoesNotExist:
            raise Exception("Product image not found")
