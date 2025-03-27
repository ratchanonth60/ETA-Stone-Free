from graphene import relay
from graphene_django import DjangoObjectType

from ecommerce.apps.catalogue.filters import (
    AttributeOptionFilter,
    AttributeOptionGroupFilter,
    CategoryFilter,
    OptionFilter,
    ProductAttributeFilter,
    ProductAttributeValueFilter,
    ProductCategoryFilter,
    ProductClassFilter,
    ProductFilter,
    ProductImageFilter,
    ProductRecommendationFilter,
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


class ProductClassType(DjangoObjectType):
    class Meta:
        model = ProductClass
        fields = ("id", "name", "slug", "requires_shipping", "track_stock")
        interfaces = (relay.Node,)
        filterset_class = ProductClassFilter


class CategoryType(DjangoObjectType):
    class Meta:
        model = Category
        fields = (
            "id",
            "name",
            "description",
            "meta_title",
            "meta_description",
            "image",
            "slug",
            "is_public",
            "ancestors_are_public",
        )
        interfaces = (relay.Node,)
        filterset_class = CategoryFilter


class ProductCategoryType(DjangoObjectType):
    class Meta:
        model = ProductCategory
        fields = ("id", "product", "category")
        interfaces = (relay.Node,)
        filterset_class = ProductCategoryFilter


class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = (
            "id",
            "is_public",
            "upc",
            "parent",
            "title",
            "slug",
            "description",
            "meta_title",
            "meta_description",
            "product_class",
            "attributes",
            "product_options",
            "recommended_products",
            "rating",
            "date_created",
            "date_updated",
            "categories",
        )
        interfaces = (relay.Node,)
        filterset_class = ProductFilter


class ProductRecommendationType(DjangoObjectType):
    class Meta:
        model = ProductRecommendation
        fields = ("id", "primary", "recommendation", "ranking")
        interfaces = (relay.Node,)
        filterset_class = ProductRecommendationFilter


class ProductAttributeType(DjangoObjectType):
    class Meta:
        model = ProductAttribute
        fields = (
            "id",
            "product_class",
            "name",
            "code",
            "type",
            "option_group",
            "required",
        )
        interfaces = (relay.Node,)
        filterset_class = ProductAttributeFilter


class ProductAttributeValueType(DjangoObjectType):
    class Meta:
        model = ProductAttributeValue
        fields = ("id", "attribute", "product", "value")
        interfaces = (relay.Node,)
        filterset_class = ProductAttributeValueFilter


class AttributeOptionGroupType(DjangoObjectType):
    class Meta:
        model = AttributeOptionGroup
        fields = ("id", "name", "options")
        interfaces = (relay.Node,)
        filterset_class = AttributeOptionGroupFilter


class AttributeOptionType(DjangoObjectType):
    class Meta:
        model = AttributeOption
        fields = ("id", "group", "option")
        interfaces = (relay.Node,)
        filterset_class = AttributeOptionFilter


class OptionType(DjangoObjectType):
    class Meta:
        model = Option
        fields = (
            "id",
            "name",
            "code",
            "type",
            "required",
            "option_group",
            "help_text",
            "order",
        )
        interfaces = (relay.Node,)
        filterset_class = OptionFilter


class ProductImageType(DjangoObjectType):
    class Meta:
        model = ProductImage
        fields = (
            "id",
            "product",
            "original",
            "caption",
            "display_order",
            "date_created",
        )
        interfaces = (relay.Node,)
        filterset_class = ProductImageFilter
