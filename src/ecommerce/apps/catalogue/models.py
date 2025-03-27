from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import RegexValidator
from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy
from oscar.apps.catalogue.abstract_models import (
    AbstractAttributeOption,
    AbstractAttributeOptionGroup,
    AbstractCategory,
    AbstractOption,
    AbstractProduct,
    AbstractProductAttribute,
    AbstractProductAttributeValue,
    AbstractProductCategory,
    AbstractProductClass,
    AbstractProductImage,
    AbstractProductRecommendation,
)
from oscar.core.decorators import deprecated
from oscar.core.validators import non_python_keyword
from oscar.models.fields import AutoSlugField, NullCharField
from oscar.models.fields.slugfield import SlugField
from oscar.utils.models import get_image_upload_path

from ecommerce.apps.catalogue.abstract_models import MissingProductImage
from ecommerce.apps.catalogue.product_attributes import ProductAttributesContainer
from ecommerce.core.defults import (
    STRUCTURE_CHOICES_PRODUCT,
    TYPE_CHOICES_OPTIONS,
    TYPE_CHOICES_PRODUCT_ATTR,
)


class ProductClass(AbstractProductClass):
    name = models.CharField(_("Name"), max_length=128)
    slug = AutoSlugField(_("Slug"), max_length=128, unique=True, populate_from="name")

    #: Some product type don't require shipping (e.g. digital products) - we use
    #: this field to take some shortcuts in the checkout.
    requires_shipping = models.BooleanField(_("Requires shipping?"), default=True)

    #: Digital products generally don't require their stock levels to be
    #: tracked.
    track_stock = models.BooleanField(_("Track stock levels?"), default=True)


class Category(AbstractCategory):
    name = models.CharField(_("Name"), max_length=255, db_index=True)
    description = models.TextField(_("Description"), blank=True)
    meta_title = models.CharField(
        _("Meta title"), max_length=255, blank=True, null=True
    )
    meta_description = models.TextField(_("Meta description"), blank=True, null=True)
    image = models.ImageField(
        _("Image"), upload_to="categories", blank=True, null=True, max_length=255
    )
    slug = SlugField(_("Slug"), max_length=255, db_index=True)

    is_public = models.BooleanField(
        _("Is public"),
        default=True,
        db_index=True,
        help_text=_("Show this category in search results and catalogue listings."),
    )

    ancestors_are_public = models.BooleanField(
        _("Ancestor categories are public"),
        default=True,
        db_index=True,
        help_text=_("The ancestors of this category are public"),
    )


class ProductCategory(AbstractProductCategory):
    product = models.ForeignKey(
        "catalogue.Product", on_delete=models.CASCADE, verbose_name=_("Product")
    )
    category = models.ForeignKey(
        "catalogue.Category", on_delete=models.CASCADE, verbose_name=_("Category")
    )


class Product(AbstractProduct):
    STRUCTURE_CHOICES = STRUCTURE_CHOICES_PRODUCT

    is_public = models.BooleanField(
        _("Is public"),
        default=True,
        db_index=True,
        help_text=_("Show this product in search results and catalogue listings."),
    )

    upc = NullCharField(
        _("UPC"),
        max_length=64,
        blank=True,
        null=True,
        unique=True,
        help_text=_(
            "Universal Product Code (UPC) is an identifier for "
            "a product which is not specific to a particular "
            " supplier. Eg an ISBN for a book."
        ),
    )

    parent = models.ForeignKey(
        "self",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name="children",
        verbose_name=_("Parent product"),
        help_text=_(
            "Only choose a parent product if you're creating a child "
            "product.  For example if this is a size "
            "4 of a particular t-shirt.  Leave blank if this is a "
            "stand-alone product (i.e. there is only one version of"
            " this product)."
        ),
    )

    # Title is mandatory for canonical products but optional for child products
    title = models.CharField(
        pgettext_lazy("Product title", "Title"), max_length=255, blank=True
    )
    slug = SlugField(_("Slug"), max_length=255, unique=False)
    description = models.TextField(_("Description"), blank=True)
    meta_title = models.CharField(
        _("Meta title"), max_length=255, blank=True, null=True
    )
    meta_description = models.TextField(_("Meta description"), blank=True, null=True)

    #: "Kind" of product, e.g. T-Shirt, Book, etc.
    #: None for child products, they inherit their parent's product class
    product_class = models.ForeignKey(
        "catalogue.ProductClass",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        verbose_name=_("Product type"),
        related_name="products",
        help_text=_("Choose what type of product this is"),
    )
    attributes = models.ManyToManyField(
        "catalogue.ProductAttribute",
        through="ProductAttributeValue",
        verbose_name=_("Attributes"),
        help_text=_(
            "A product attribute is something that this product may "
            "have, such as a size, as specified by its class"
        ),
    )
    #: It's possible to have options product class-wide, and per product.
    product_options = models.ManyToManyField(
        "catalogue.Option",
        blank=True,
        verbose_name=_("Product options"),
        help_text=_(
            "Options are values that can be associated with a item "
            "when it is added to a customer's basket.  This could be "
            "something like a personalised message to be printed on "
            "a T-shirt."
        ),
    )

    recommended_products = models.ManyToManyField(
        "catalogue.Product",
        through="ProductRecommendation",
        blank=True,
        verbose_name=_("Recommended products"),
        help_text=_(
            "These are products that are recommended to accompany the main product."
        ),
    )

    # Denormalised product rating - used by reviews app.
    # Product has no ratings if rating is None
    rating = models.FloatField(_("Rating"), null=True, editable=False)

    date_created = models.DateTimeField(
        _("Date created"), auto_now_add=True, db_index=True
    )

    # This field is used by Haystack to reindex search
    date_updated = models.DateTimeField(_("Date updated"), auto_now=True, db_index=True)

    categories = models.ManyToManyField(
        "catalogue.Category", through="ProductCategory", verbose_name=_("Categories")
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attr = ProductAttributesContainer(product=self)

    @deprecated
    def get_is_discountable(self):
        """
        It used to be that, :py:attr:`.is_discountable` couldn't be set individually for child
        products; so they had to inherit it from their parent. This is nolonger the case because
        ranges can include child products as well. That make this method useless.
        """
        return self.is_discountable

    def primary_image(self):
        """
        Returns the primary image for a product. Usually used when one can
        only display one product image, e.g. in a list of products.
        """
        images = self.get_all_images()
        ordering = self.images.model.Meta.ordering
        if not ordering or ordering[0] != "display_order":
            # Only apply order_by() if a custom model doesn't use default
            # ordering. Applying order_by() busts the prefetch cache of
            # the ProductManager
            images = images.order_by("display_order")
        try:
            return images[0]
        except IndexError:
            # We return a dict with fields that mirror the key properties of
            # the ProductImage class so this missing image can be used
            # interchangeably in templates.  Strategy pattern ftw!
            missing_image = self.get_missing_image()
            return {"original": missing_image.name, "caption": "", "is_missing": True}


class ProductRecommendation(AbstractProductRecommendation):
    primary = models.ForeignKey(
        "catalogue.Product",
        on_delete=models.CASCADE,
        related_name="primary_recommendations",
        verbose_name=_("Primary product"),
    )
    recommendation = models.ForeignKey(
        "catalogue.Product",
        on_delete=models.CASCADE,
        verbose_name=_("Recommended product"),
    )
    ranking = models.PositiveSmallIntegerField(
        _("Ranking"),
        default=0,
        db_index=True,
        help_text=_(
            "Determines order of the products. A product with a higher"
            " value will appear before one with a lower ranking."
        ),
    )


class ProductAttribute(AbstractProductAttribute):
    TYPE_CHOICES = TYPE_CHOICES_PRODUCT_ATTR

    product_class = models.ForeignKey(
        "catalogue.ProductClass",
        blank=True,
        on_delete=models.CASCADE,
        related_name="attributes",
        null=True,
        verbose_name=_("Product type"),
    )
    name = models.CharField(_("Name"), max_length=128)
    code = models.SlugField(
        _("Code"),
        max_length=128,
        validators=[
            RegexValidator(
                regex=r"^[a-zA-Z_][0-9a-zA-Z_]*$",
                message=_(
                    "Code can only contain the letters a-z, A-Z, digits, "
                    "and underscores, and can't start with a digit."
                ),
            ),
            non_python_keyword,
        ],
    )

    type = models.CharField(
        choices=TYPE_CHOICES,
        default=TYPE_CHOICES[0][0],
        max_length=20,
        verbose_name=_("Type"),
    )

    option_group = models.ForeignKey(
        "catalogue.AttributeOptionGroup",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name="product_attributes",
        verbose_name=_("Option Group"),
        help_text=_('Select an option group if using type "Option" or "Multi Option"'),
    )
    required = models.BooleanField(_("Required"), default=False)

    def _get_value_obj(self, product, value):
        try:
            return product.attribute_values.get(attribute=self)
        except ObjectDoesNotExist:
            # FileField uses False for announcing deletion of the file
            # not creating a new value
            delete_file = self.is_file and value is False
            if value is None or value == "" or delete_file:
                return None
            return product.attribute_values.create(attribute=self)

    def _bind_value_file(self, value_obj, value):
        if value is None:
            # No change
            return value_obj
        elif value is False:
            return None
        else:
            # New uploaded file
            value_obj.value = value
            return value_obj

    def _bind_value_multi_option(self, value_obj, value):
        # ManyToMany fields are handled separately
        if value is None:
            return None
        try:
            count = value.count()
        except (AttributeError, TypeError):
            count = len(value)
        if count == 0:
            return None
        value_obj.value = value
        return value_obj

    def _bind_value(self, value_obj, value):
        if value is None or value == "":
            return None
        value_obj.value = value
        return value_obj

    def bind_value(self, value_obj, value):
        """
        bind_value will bind the value passed to the value_obj, if the bind_value
        return None, that means the value_obj is supposed to be deleted.
        """
        if self.is_file:
            return self._bind_value_file(value_obj, value)
        elif self.is_multi_option:
            return self._bind_value_multi_option(value_obj, value)
        else:
            return self._bind_value(value_obj, value)

    def save_value(self, product, value):
        value_obj = self._get_value_obj(product, value)

        if value_obj is None:
            return None

        updated_value_obj = self.bind_value(value_obj, value)
        if updated_value_obj is None:
            value_obj.delete()
        elif updated_value_obj.is_dirty:
            updated_value_obj.save()

        return updated_value_obj


class ProductAttributeValue(AbstractProductAttributeValue):
    attribute = models.ForeignKey(
        "catalogue.ProductAttribute",
        on_delete=models.CASCADE,
        verbose_name=_("Attribute"),
    )
    product = models.ForeignKey(
        "catalogue.Product",
        on_delete=models.CASCADE,
        related_name="attribute_values",
        verbose_name=_("Product"),
    )
    _dirty = False

    @cached_property
    def type(self):
        return self.attribute.type

    @property
    def value_field_name(self):
        return f"value_{self.type}"

    def _get_value(self):
        value = getattr(self, self.value_field_name)
        if hasattr(value, "all"):
            value = value.all()
        return value

    def _set_value(self, new_value):
        attr_name = self.value_field_name

        if self.attribute.is_option and isinstance(new_value, str):
            # Need to look up instance of AttributeOption
            new_value = self.attribute.option_group.options.get(option=new_value)
        elif self.attribute.is_multi_option:
            getattr(self, attr_name).set(new_value)
            self._dirty = True
            return

        setattr(self, attr_name, new_value)
        self._dirty = True

    value = property(_get_value, _set_value)

    @property
    def is_dirty(self):
        return self._dirty


class AttributeOptionGroup(AbstractAttributeOptionGroup):
    name = models.CharField(_("Name"), max_length=128)


class AttributeOption(AbstractAttributeOption):
    group = models.ForeignKey(
        "catalogue.AttributeOptionGroup",
        on_delete=models.CASCADE,
        related_name="options",
        verbose_name=_("Group"),
    )
    option = models.CharField(_("Option"), max_length=255)


class Option(AbstractOption):
    TYPE_CHOICES = TYPE_CHOICES_OPTIONS

    name = models.CharField(_("Name"), max_length=128, db_index=True)
    code = AutoSlugField(_("Code"), max_length=128, unique=True, populate_from="name")
    required = models.BooleanField(_("Is this option required?"), default=False)
    option_group = models.ForeignKey(
        "catalogue.AttributeOptionGroup",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name="product_options",
        verbose_name=_("Option Group"),
        help_text=_('Select an option group if using type "Option" or "Multi Option"'),
    )
    help_text = models.CharField(
        verbose_name=_("Help text"),
        blank=True,
        null=True,
        max_length=255,
        help_text=_("Help text shown to the user on the add to basket form"),
    )
    order = models.IntegerField(
        _("Ordering"),
        null=True,
        blank=True,
        help_text=_("Controls the ordering of product options on product detail pages"),
        db_index=True,
    )


class ProductImage(AbstractProductImage):
    product = models.ForeignKey(
        "catalogue.Product",
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name=_("Product"),
    )
    original = models.ImageField(
        _("Original"), upload_to=get_image_upload_path, max_length=255
    )
    caption = models.CharField(_("Caption"), max_length=200, blank=True)

    #: Use display_order to determine which is the "primary" image
    display_order = models.PositiveIntegerField(
        _("Display order"),
        default=0,
        db_index=True,
        help_text=_(
            "An image with a display order of zero will be the primary"
            " image for a product"
        ),
    )
    date_created = models.DateTimeField(_("Date created"), auto_now_add=True)

    def get_missing_image(self):
        """
        Returns a missing image object.
        """
        # This class should have a 'name' property so it mimics the Django file
        # field.
        return MissingProductImage()
