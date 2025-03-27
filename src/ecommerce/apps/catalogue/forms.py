from django import forms

from .models import (
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


class ProductClassForm(forms.ModelForm):
    class Meta:
        model = ProductClass
        fields = [
            "name",
            "requires_shipping",
            "track_stock",
        ]


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = [
            "name",
            "description",
            "meta_title",
            "meta_description",
            "image",
            "is_public",
            "ancestors_are_public",
        ]


class ProductCategoryForm(forms.ModelForm):
    class Meta:
        model = ProductCategory
        fields = [
            "product",
            "category",
        ]


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            "is_public",
            "upc",
            "parent",
            "title",
            "description",
            "meta_title",
            "meta_description",
            "product_class",
            "product_options",
            "recommended_products",
            "categories",
        ]


class ProductRecommendationForm(forms.ModelForm):
    class Meta:
        model = ProductRecommendation
        fields = [
            "primary",
            "recommendation",
            "ranking",
        ]


class ProductAttributeForm(forms.ModelForm):
    class Meta:
        model = ProductAttribute
        fields = [
            "product_class",
            "name",
            "code",
            "type",
            "option_group",
            "required",
        ]


class ProductAttributeValueForm(forms.ModelForm):
    class Meta:
        model = ProductAttributeValue
        fields = [
            "attribute",
            "product",
            "value_text",  # ตัวอย่างสำหรับ type="text" (ปรับตาม type ได้)
        ]


class AttributeOptionGroupForm(forms.ModelForm):
    class Meta:
        model = AttributeOptionGroup
        fields = [
            "name",
        ]


class AttributeOptionForm(forms.ModelForm):
    class Meta:
        model = AttributeOption
        fields = [
            "group",
            "option",
        ]


class OptionForm(forms.ModelForm):
    class Meta:
        model = Option
        fields = [
            "name",
            "required",
            "option_group",
            "help_text",
            "order",
        ]


class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = [
            "product",
            "original",
            "caption",
            "display_order",
        ]
