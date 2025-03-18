import graphene
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


class ProductCreateMutation(graphene.Mutation):
    class Arguments:
        title = graphene.String(required=True)
        slug = graphene.String(required=True)
        description = graphene.String()
        product_class_id = graphene.ID(required=True)
        is_public = graphene.Boolean(default_value=True)

    product = graphene.Field(ProductType)

    @login_required
    def mutate(
        self, info, title, slug, description=None, product_class_id=None, is_public=True
    ):
        try:
            product_class = ProductClass.objects.get(id=product_class_id)
            product = Product.objects.create(
                title=title,
                slug=slug,
                description=description or "",
                product_class=product_class,
                is_public=is_public,
            )
            return ProductCreateMutation(product=product)
        except ProductClass.DoesNotExist:
            raise Exception("Product class not found")


class CategoryCreateMutation(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        slug = graphene.String(required=True)
        description = graphene.String()
        is_public = graphene.Boolean(default_value=True)

    category = graphene.Field(CategoryType)

    @login_required
    def mutate(self, info, name, slug, description=None, is_public=True):
        category = Category.objects.create(
            name=name, slug=slug, description=description or "", is_public=is_public
        )
        return CategoryCreateMutation(category=category)


class ProductClassCreateMutation(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        slug = graphene.String(required=True)
        requires_shipping = graphene.Boolean(default_value=True)
        track_stock = graphene.Boolean(default_value=True)

    product_class = graphene.Field(ProductClassType)

    @login_required
    def mutate(self, info, name, slug, requires_shipping=True, track_stock=True):
        product_class = ProductClass.objects.create(
            name=name,
            slug=slug,
            requires_shipping=requires_shipping,
            track_stock=track_stock,
        )
        return ProductClassCreateMutation(product_class=product_class)


class ProductCategoryCreateMutation(graphene.Mutation):
    class Arguments:
        product_id = graphene.ID(required=True)
        category_id = graphene.ID(required=True)

    product_category = graphene.Field(ProductCategoryType)

    @login_required
    def mutate(self, info, product_id, category_id):
        try:
            product = Product.objects.get(id=product_id)
            category = Category.objects.get(id=category_id)
            product_category = ProductCategory.objects.create(
                product=product, category=category
            )
            return ProductCategoryCreateMutation(product_category=product_category)
        except (Product.DoesNotExist, Category.DoesNotExist):
            raise Exception("Product or Category not found")


class ProductRecommendationCreateMutation(graphene.Mutation):
    class Arguments:
        primary_id = graphene.ID(required=True)
        recommendation_id = graphene.ID(required=True)
        ranking = graphene.Int(default_value=0)

    product_recommendation = graphene.Field(ProductRecommendationType)

    @login_required
    def mutate(self, info, primary_id, recommendation_id, ranking=0):
        try:
            primary = Product.objects.get(id=primary_id)
            recommendation = Product.objects.get(id=recommendation_id)
            product_recommendation = ProductRecommendation.objects.create(
                primary=primary, recommendation=recommendation, ranking=ranking
            )
            return ProductRecommendationCreateMutation(
                product_recommendation=product_recommendation
            )
        except Product.DoesNotExist:
            raise Exception("Product not found")


class ProductAttributeCreateMutation(graphene.Mutation):
    class Arguments:
        product_class_id = graphene.ID()
        name = graphene.String(required=True)
        code = graphene.String(required=True)
        type = graphene.String(required=True)
        option_group_id = graphene.ID()
        required = graphene.Boolean(default_value=False)

    product_attribute = graphene.Field(ProductAttributeType)

    @login_required
    def mutate(
        self,
        info,
        product_class_id=None,
        name=None,
        code=None,
        type=None,
        option_group_id=None,
        required=False,
    ):
        try:
            product_class = (
                ProductClass.objects.get(id=product_class_id)
                if product_class_id
                else None
            )
            option_group = (
                AttributeOptionGroup.objects.get(id=option_group_id)
                if option_group_id
                else None
            )
            product_attribute = ProductAttribute.objects.create(
                product_class=product_class,
                name=name,
                code=code,
                type=type,
                option_group=option_group,
                required=required,
            )
            return ProductAttributeCreateMutation(product_attribute=product_attribute)
        except (ProductClass.DoesNotExist, AttributeOptionGroup.DoesNotExist):
            raise Exception("Product class or option group not found")


class ProductAttributeValueCreateMutation(graphene.Mutation):
    class Arguments:
        attribute_id = graphene.ID(required=True)
        product_id = graphene.ID(required=True)
        value = graphene.JSONString(required=True)

    product_attribute_value = graphene.Field(ProductAttributeValueType)

    @login_required
    def mutate(self, info, attribute_id, product_id, value):
        try:
            attribute = ProductAttribute.objects.get(id=attribute_id)
            product = Product.objects.get(id=product_id)
            product_attribute_value = ProductAttributeValue.objects.create(
                attribute=attribute, product=product, value=value
            )
            return ProductAttributeValueCreateMutation(
                product_attribute_value=product_attribute_value
            )
        except (ProductAttribute.DoesNotExist, Product.DoesNotExist):
            raise Exception("Attribute or Product not found")


class AttributeOptionGroupCreateMutation(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)

    attribute_option_group = graphene.Field(AttributeOptionGroupType)

    @login_required
    def mutate(self, info, name):
        attribute_option_group = AttributeOptionGroup.objects.create(name=name)
        return AttributeOptionGroupCreateMutation(
            attribute_option_group=attribute_option_group
        )


class AttributeOptionCreateMutation(graphene.Mutation):
    class Arguments:
        group_id = graphene.ID(required=True)
        option = graphene.String(required=True)

    attribute_option = graphene.Field(AttributeOptionType)

    @login_required
    def mutate(self, info, group_id, option):
        try:
            group = AttributeOptionGroup.objects.get(id=group_id)
            attribute_option = AttributeOption.objects.create(
                group=group, option=option
            )
            return AttributeOptionCreateMutation(attribute_option=attribute_option)
        except AttributeOptionGroup.DoesNotExist:
            raise Exception("Attribute option group not found")


class OptionCreateMutation(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        code = graphene.String(required=True)
        type = graphene.String(required=True)
        required = graphene.Boolean(default_value=False)
        option_group_id = graphene.ID()
        help_text = graphene.String()
        order = graphene.Int()

    option = graphene.Field(OptionType)

    @login_required
    def mutate(
        self,
        info,
        name,
        code,
        type,
        required=False,
        option_group_id=None,
        help_text=None,
        order=None,
    ):
        try:
            option_group = (
                AttributeOptionGroup.objects.get(id=option_group_id)
                if option_group_id
                else None
            )
            option = Option.objects.create(
                name=name,
                code=code,
                type=type,
                required=required,
                option_group=option_group,
                help_text=help_text,
                order=order,
            )
            return OptionCreateMutation(option=option)
        except AttributeOptionGroup.DoesNotExist:
            raise Exception("Option group not found")


class ProductImageCreateMutation(graphene.Mutation):
    class Arguments:
        product_id = graphene.ID(required=True)
        original = graphene.String(required=True)
        caption = graphene.String()
        display_order = graphene.Int(default_value=0)

    product_image = graphene.Field(ProductImageType)

    @login_required
    def mutate(self, info, product_id, original, caption=None, display_order=0):
        try:
            product = Product.objects.get(id=product_id)
            product_image = ProductImage.objects.create(
                product=product,
                original=original,
                caption=caption or "",
                display_order=display_order,
            )
            return ProductImageCreateMutation(product_image=product_image)
        except Product.DoesNotExist:
            raise Exception("Product not found")
