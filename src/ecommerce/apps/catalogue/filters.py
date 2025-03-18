import django_filters

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


# ProductClass Filter
class ProductClassFilter(django_filters.FilterSet):
    class Meta:
        model = ProductClass
        fields = {
            "name": ["exact", "icontains"],
            "slug": ["exact", "icontains"],
            "requires_shipping": ["exact"],
            "track_stock": ["exact"],
        }


# Category Filter
class CategoryFilter(django_filters.FilterSet):
    class Meta:
        model = Category
        fields = {
            "name": ["exact", "icontains"],
            "slug": ["exact", "icontains"],
            "is_public": ["exact"],
            "ancestors_are_public": ["exact"],
            "description": ["icontains"],
        }


# ProductCategory Filter
class ProductCategoryFilter(django_filters.FilterSet):
    class Meta:
        model = ProductCategory
        fields = {
            "product__id": ["exact"],
            "category__id": ["exact"],
            "category__slug": ["exact"],
        }


# Product Filter
class ProductFilter(django_filters.FilterSet):
    class Meta:
        model = Product
        fields = {
            "title": ["exact", "icontains"],
            "slug": ["exact", "icontains"],
            "is_public": ["exact"],
            "upc": ["exact"],
            "product_class__id": ["exact"],
            "product_class__slug": ["exact"],
            "date_created": ["gte", "lte"],
            "date_updated": ["gte", "lte"],
            "rating": ["exact", "gte", "lte"],
            "parent__id": ["exact"],
        }


# ProductRecommendation Filter
class ProductRecommendationFilter(django_filters.FilterSet):
    class Meta:
        model = ProductRecommendation
        fields = {
            "primary__id": ["exact"],
            "recommendation__id": ["exact"],
            "ranking": ["exact", "gte", "lte"],
        }


# ProductAttribute Filter
class ProductAttributeFilter(django_filters.FilterSet):
    class Meta:
        model = ProductAttribute
        fields = {
            "name": ["exact", "icontains"],
            "code": ["exact", "icontains"],
            "type": ["exact"],
            "product_class__id": ["exact"],
            "option_group__id": ["exact"],
            "required": ["exact"],
        }


# ProductAttributeValue Filter
class ProductAttributeValueFilter(django_filters.FilterSet):
    class Meta:
        model = ProductAttributeValue
        fields = {
            "attribute__id": ["exact"],
            "product__id": ["exact"],
            # ค่า value จะขึ้นอยู่กับ type (เช่น value_text, value_integer) ดังนั้นใช้ filter ทั่วไป
            "value_text": ["exact", "icontains"],
            "value_integer": ["exact", "gte", "lte"],
        }


# AttributeOptionGroup Filter
class AttributeOptionGroupFilter(django_filters.FilterSet):
    class Meta:
        model = AttributeOptionGroup
        fields = {
            "name": ["exact", "icontains"],
        }


# AttributeOption Filter
class AttributeOptionFilter(django_filters.FilterSet):
    class Meta:
        model = AttributeOption
        fields = {
            "group__id": ["exact"],
            "option": ["exact", "icontains"],
        }


# Option Filter
class OptionFilter(django_filters.FilterSet):
    class Meta:
        model = Option
        fields = {
            "name": ["exact", "icontains"],
            "code": ["exact", "icontains"],
            "type": ["exact"],
            "required": ["exact"],
            "option_group__id": ["exact"],
            "order": ["exact", "gte", "lte"],
        }


# ProductImage Filter
class ProductImageFilter(django_filters.FilterSet):
    class Meta:
        model = ProductImage
        fields = {
            "product__id": ["exact"],
            "caption": ["exact", "icontains"],
            "display_order": ["exact", "gte", "lte"],
            "date_created": ["gte", "lte"],
        }
