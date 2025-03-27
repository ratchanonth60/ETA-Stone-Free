import graphene

from .mutations import CatalogueMutation
from .queries import (
    AttributeOptionGroupQuery,
    AttributeOptionQuery,
    CategoryQuery,
    OptionQuery,
    ProductAttributeQuery,
    ProductAttributeValueQuery,
    ProductCategoryQuery,
    ProductClassQuery,
    ProductImageQuery,
    ProductQuery,
    ProductRecommendationQuery,
)


class Query(
    graphene.ObjectType,
):
    product = graphene.Field(ProductQuery)
    category = graphene.Field(CategoryQuery)
    product_class = graphene.Field(ProductClassQuery)
    product_category = graphene.Field(ProductCategoryQuery)
    product_recommendation = graphene.Field(ProductRecommendationQuery)
    product_attribute = graphene.Field(ProductAttributeQuery)
    product_attribute_value = graphene.Field(ProductAttributeValueQuery)
    attribute_option_group = graphene.Field(AttributeOptionGroupQuery)
    attribute_option = graphene.Field(AttributeOptionQuery)
    option = graphene.Field(OptionQuery)
    product_image = graphene.Field(ProductImageQuery)

    def resolve_product(self, _):
        return ProductQuery()

    def resolve_category(self, _):
        return CategoryQuery()

    def resolve_product_class(self, _):
        return ProductClassQuery()

    def resolve_product_category(self, _):
        return ProductCategoryQuery()

    def resolve_product_recommendation(self, _):
        return ProductRecommendationQuery()

    def resolve_product_attribute(self, _):
        return ProductAttributeQuery()

    def resolve_product_attribute_value(self, _):
        return ProductAttributeValueQuery()

    def resolve_attribute_option_group(self, _):
        return AttributeOptionGroupQuery()

    def resolve_attribute_option(self, _):
        return AttributeOptionQuery()

    def resolve_option(self, _):
        return OptionQuery()

    def resolve_product_image(self, _):
        return ProductImageQuery()


class Mutation(graphene.ObjectType):
    product = graphene.Field(CatalogueMutation)
