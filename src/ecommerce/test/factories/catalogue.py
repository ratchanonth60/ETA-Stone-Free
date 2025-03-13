# coding=utf-8
import factory
from factory.django import DjangoModelFactory

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
)
from ecommerce.apps.catalogue.reviews.models import ProductReview

__all__ = [
    "ProductClassFactory",
    "ProductFactory",
    "CategoryFactory",
    "ProductCategoryFactory",
    "ProductAttributeFactory",
    "AttributeOptionGroupFactory",
    "OptionFactory",
    "AttributeOptionFactory",
    "ProductAttributeValueFactory",
    "ProductReviewFactory",
    "ProductImageFactory",
]


class ProductClassFactory(DjangoModelFactory):
    name = "Books"
    requires_shipping = True
    track_stock = True

    class Meta:
        model = ProductClass


class ProductFactory(DjangoModelFactory):
    upc = factory.Sequence(lambda n: "978080213020%d" % n)
    title = "A confederacy of dunces"
    product_class = factory.SubFactory(ProductClassFactory)

    stockrecords = factory.RelatedFactory(
        "ecommerce.test.factories.StockRecordFactory", "product"
    )
    categories = factory.RelatedFactory(
        "ecommerce.test.factories.ProductCategoryFactory", "product"
    )

    class Meta:
        model = Product

    structure = Meta.model.STANDALONE


class CategoryFactory(DjangoModelFactory):
    name = factory.Sequence(lambda n: "Category %d" % n)

    # Very naive handling of treebeard node fields. Works though!
    depth = 1
    path = factory.Sequence(lambda n: "%04d" % n)

    class Meta:
        model = Category


class ProductCategoryFactory(DjangoModelFactory):
    category = factory.SubFactory(CategoryFactory)

    class Meta:
        model = ProductCategory


class ProductAttributeFactory(DjangoModelFactory):
    code = name = "weight"
    product_class = factory.SubFactory(ProductClassFactory)
    type = "float"

    class Meta:
        model = ProductAttribute


class OptionFactory(DjangoModelFactory):
    class Meta:
        model = Option

    name = "example option"
    code = "example"
    type = Meta.model.TEXT
    required = False


class AttributeOptionFactory(DjangoModelFactory):
    # Ideally we'd get_or_create a AttributeOptionGroup here, but I'm not
    # aware of how to not create a unique option group for each call of the
    # factory

    option = factory.Sequence(lambda n: "Option %d" % n)

    class Meta:
        model = AttributeOption


class AttributeOptionGroupFactory(DjangoModelFactory):
    name = "Grüppchen"

    class Meta:
        model = AttributeOptionGroup


class ProductAttributeValueFactory(DjangoModelFactory):
    attribute = factory.SubFactory(ProductAttributeFactory)
    product = factory.SubFactory(ProductFactory)

    class Meta:
        model = ProductAttributeValue


class ProductReviewFactory(DjangoModelFactory):
    score = 5
    product = factory.SubFactory(ProductFactory, stockrecords=[])

    class Meta:
        model = ProductReview


class ProductImageFactory(DjangoModelFactory):
    product = factory.SubFactory(ProductFactory, stockrecords=[])
    original = factory.django.ImageField(
        width=100, height=200, filename="test_image.jpg"
    )

    class Meta:
        model = ProductImage
