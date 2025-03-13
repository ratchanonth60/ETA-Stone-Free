import os
import tempfile
import unittest
from copy import deepcopy
from datetime import date, datetime
from unittest import mock

import pytest
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
from django.test.utils import override_settings
from oscar.apps.catalogue.abstract_models import MissingProductImage
from oscar.templatetags.category_tags import get_annotated_list

from ecommerce.apps.catalogue import models
from ecommerce.apps.catalogue.categories import create_from_breadcrumbs
from ecommerce.apps.catalogue.models import (
    AttributeOption,
    Category,
    Product,
    ProductAttribute,
    ProductAttributeValue,
    ProductClass,
    ProductRecommendation,
)
from ecommerce.test import factories
from ecommerce.test.factories.catalogue import (
    ProductAttributeFactory,
    ProductClassFactory,
    ProductFactory,
)
from ecommerce.test.testcases import TestCase
from ecommerce.test.utils import ThumbnailMixin


class ProductTestCase(TestCase):
    def setUp(self) -> None:
        super().setUp()

    @staticmethod
    def _get_saved(model_obj):
        model_obj.save()
        model_obj.refresh_from_db()
        return model_obj

    def test_get_meta_title(self):
        parent_title, child_title = "P title", "C title"
        parent_meta_title, child_meta_title = "P meta title", "C meta title"
        parent_product = ProductFactory(
            structure=Product.PARENT, title=parent_title, meta_title=parent_meta_title
        )
        child_product = ProductFactory(
            structure=Product.CHILD,
            title=child_title,
            meta_title=child_meta_title,
            parent=parent_product,
        )
        self.assertEqual(child_product.get_meta_title(), child_meta_title)
        child_product.meta_title = ""
        self.assertEqual(
            self._get_saved(child_product).get_meta_title(), parent_meta_title
        )
        parent_product.meta_title = ""
        child_product.parent = self._get_saved(parent_product)
        self.assertEqual(self._get_saved(child_product).get_meta_title(), child_title)

    def test_get_meta_description(self):
        parent_description, child_description = "P description", "C description"
        parent_meta_description, child_meta_description = (
            "P meta description",
            "C meta description",
        )
        parent_product = ProductFactory(
            structure=Product.PARENT,
            description=parent_description,
            meta_description=parent_meta_description,
        )
        child_product = ProductFactory(
            structure=Product.CHILD,
            description=child_description,
            meta_description=child_meta_description,
            parent=parent_product,
        )
        self.assertEqual(child_product.get_meta_description(), child_meta_description)
        child_product.meta_description = ""
        self.assertEqual(
            self._get_saved(child_product).get_meta_description(),
            parent_meta_description,
        )
        parent_product.meta_description = ""
        child_product.parent = self._get_saved(parent_product)
        self.assertEqual(
            self._get_saved(child_product).get_meta_description(), child_description
        )


class CatalogueTestModels(TestCase):
    def setUp(self) -> None:
        super().setUp()

    def test_product_attributes_can_contain_underscores(self):
        attr = models.ProductAttribute(name="A", code="a_b")
        attr.full_clean()

    def test_product_attributes_cant_contain_hyphens(self):
        attr = models.ProductAttribute(name="A", code="a-b")
        with pytest.raises(ValidationError):
            attr.full_clean()

    def test_product_attributes_cant_be_python_keywords(self):
        attr = models.ProductAttribute(name="A", code="import")
        with pytest.raises(ValidationError):
            attr.full_clean()

    def test_product_boolean_attribute_cant_be_required(self):
        attr = models.ProductAttribute(
            name="A", code="a", type=models.ProductAttribute.BOOLEAN, required=True
        )
        with pytest.raises(ValidationError):
            attr.full_clean()


# -------  test_attributes -----------
class TestContainer(TestCase):
    def setUp(self) -> None:
        super().setUp()

    def test_attributes_initialised_before_write(self):
        product_class = factories.ProductClassFactory()
        product_class.attributes.create(name="a1", code="a1", required=True)
        product_class.attributes.create(name="a2", code="a2", required=False)
        product_class.attributes.create(name="a3", code="a3", required=True)
        product = factories.ProductFactory(product_class=product_class)
        product.attr.a1 = "v1"
        product.attr.a3 = "v3"
        product.attr.save()

        product = Product.objects.get(pk=product.pk)
        product.attr.a1 = "v2"
        product.attr.a3 = "v6"
        product.attr.save()

        product = Product.objects.get(pk=product.pk)
        assert product.attr.a1 == "v2"
        assert product.attr.a3 == "v6"

    def test_attributes_refresh(self):
        product_class = factories.ProductClassFactory()
        product_class.attributes.create(name="a1", code="a1", required=True)
        product = factories.ProductFactory(product_class=product_class)
        product.attr.a1 = "v1"
        product.attr.save()

        product_attr = ProductAttribute.objects.get(code="a1", product=product)
        product_attr.save_value(product, "v2")
        assert product.attr.a1 == "v1"

        product.attr.refresh()
        assert product.attr.a1 == "v2"

    def test_attribute_code_uniqueness(self):
        product_class = factories.ProductClassFactory()
        attribute1 = ProductAttribute.objects.create(
            name="a1", code="a1", product_class=product_class
        )
        attribute1.full_clean()

        with self.assertRaises(ValidationError):
            ProductAttribute(
                name="a1", code="a1", product_class=product_class
            ).full_clean()

        another_product_class = ProductClass.objects.create(
            name="another product class"
        )
        ProductAttribute(
            name="a1", code="a1", product_class=another_product_class
        ).full_clean()


class TestBooleanAttributes(TestCase):
    def setUp(self):
        super().setUp()
        self.attr = factories.ProductAttributeFactory(type="boolean")

    def test_validate_boolean_values(self):
        self.assertIsNone(self.attr.validate_value(True))

    def test_validate_invalid_boolean_values(self):
        with self.assertRaises(ValidationError):
            self.attr.validate_value(1)

    def test_boolean_value_as_text_true(self):
        product = factories.ProductFactory()
        self.attr.save_value(product, True)
        attr_val = product.attribute_values.get(attribute=self.attr)
        assert attr_val.value_as_text == "Yes"

    def test_boolean_value_as_text_false(self):
        product = factories.ProductFactory()
        self.attr.save_value(product, False)
        attr_val = product.attribute_values.get(attribute=self.attr)
        assert attr_val.value_as_text == "No"


class TestMultiOptionAttributes(TestCase):
    def setUp(self):
        super().setUp()
        self.option_group = factories.AttributeOptionGroupFactory()
        self.attr = factories.ProductAttributeFactory(
            type="multi_option",
            name="Sizes",
            code="sizes",
            option_group=self.option_group,
        )

        # Add some options to the group
        self.options = factories.AttributeOptionFactory.create_batch(
            3, group=self.option_group
        )

    def test_validate_multi_option_values(self):
        self.assertIsNone(self.attr.validate_value([self.options[0], self.options[1]]))

    def test_validate_invalid_multi_option_values(self):
        with self.assertRaises(ValidationError):
            # value must be an iterable
            self.attr.validate_value("foobar")

        with self.assertRaises(ValidationError):
            # Items must all be AttributeOption objects
            self.attr.validate_value([self.options[0], "notanOption"])

    def test_save_multi_option_value(self):
        product = factories.ProductFactory()
        # We'll save two out of the three available options
        self.attr.save_value(product, [self.options[0], self.options[2]])
        product = Product.objects.get(pk=product.pk)
        self.assertEqual(
            list(product.attr.sizes.order_by("id")), [self.options[0], self.options[2]]
        )

    def test_delete_multi_option_value(self):
        product = factories.ProductFactory()
        self.attr.save_value(product, [self.options[0], self.options[1]])
        # Now delete these values
        self.attr.save_value(product, None)
        product = Product.objects.get(pk=product.pk)
        self.assertFalse(hasattr(product.attr, "sizes"))

    def test_multi_option_value_as_text(self):
        product = factories.ProductFactory()
        self.attr.save_value(product, self.options)
        attr_val = product.attribute_values.get(attribute=self.attr)
        self.assertEqual(
            attr_val.value_as_text, ", ".join(o.option for o in self.options)
        )


class TestOptionAttributes(TestCase):
    def setUp(self):
        super().setUp()
        self.option_group = factories.AttributeOptionGroupFactory()
        self.attr = factories.ProductAttributeFactory(
            type="option",
            name="Size",
            code="size",
            option_group=self.option_group,
        )

        # Add some options to the group
        self.options = factories.AttributeOptionFactory.create_batch(
            3, group=self.option_group
        )

    def test_option_value_as_text(self):
        product = factories.ProductFactory()
        option_2 = self.options[1]
        self.attr.save_value(product, option_2)
        attr_val = product.attribute_values.get(attribute=self.attr)
        assert attr_val.value_as_text == str(option_2)


class TestDatetimeAttributes(TestCase):
    def setUp(self):
        super().setUp()
        self.attr = factories.ProductAttributeFactory(type="datetime")

    def test_validate_datetime_values(self):
        self.assertIsNone(self.attr.validate_value(datetime.now()))

    def test_validate_invalid_datetime_values(self):
        with self.assertRaises(ValidationError):
            self.attr.validate_value(1)


class TestDateAttributes(TestCase):
    def setUp(self):
        super().setUp()
        self.attr = factories.ProductAttributeFactory(type="date")

    def test_validate_datetime_values(self):
        self.assertIsNone(self.attr.validate_value(datetime.now()))

    def test_validate_date_values(self):
        self.assertIsNone(self.attr.validate_value(date.today()))

    def test_validate_invalid_date_values(self):
        with self.assertRaises(ValidationError):
            self.attr.validate_value(1)


class TestIntegerAttributes(TestCase):
    def setUp(self):
        super().setUp()
        self.attr = factories.ProductAttributeFactory(type="integer")

    def test_validate_integer_values(self):
        self.assertIsNone(self.attr.validate_value(1))

    def test_validate_str_integer_values(self):
        self.assertIsNone(self.attr.validate_value("1"))

    def test_validate_invalid_integer_values(self):
        with self.assertRaises(ValidationError):
            self.attr.validate_value("notanInteger")


class TestFloatAttributes(TestCase):
    def setUp(self):
        super().setUp()
        self.attr = factories.ProductAttributeFactory(type="float")

    def test_validate_integer_values(self):
        self.assertIsNone(self.attr.validate_value(1))

    def test_validate_float_values(self):
        self.assertIsNone(self.attr.validate_value(1.2))

    def test_validate_str_float_values(self):
        self.assertIsNone(self.attr.validate_value("1.2"))

    def test_validate_invalid_float_values(self):
        with self.assertRaises(ValidationError):
            self.attr.validate_value("notaFloat")


class TestTextAttributes(TestCase):
    def setUp(self):
        super().setUp()
        self.attr = factories.ProductAttributeFactory(type="text")

    def test_validate_string_and_unicode_values(self):
        self.assertIsNone(self.attr.validate_value("String"))

    def test_validate_invalid_float_values(self):
        with self.assertRaises(ValidationError):
            self.attr.validate_value(1)


class TestFileAttributes(TestCase):
    def setUp(self):
        super().setUp()
        self.attr = factories.ProductAttributeFactory(type="file")

    def test_validate_file_values(self):
        file_field = SimpleUploadedFile("test_file.txt", b"Test")
        self.assertIsNone(self.attr.validate_value(file_field))


# -------  Testcategory -----------
class TestCategory(TestCase):
    def setUp(self):
        super().setUp()
        self.products = Category.add_root(name="Pröducts")
        self.books = self.products.add_child(name="Bücher")

    def tearDown(self):
        cache.clear()

    def test_includes_parents_name_in_full_name(self):
        self.assertTrue(self.products.name in self.books.full_name)

    def test_has_children_method(self):
        self.assertTrue(self.products.has_children())

    def test_slugs_were_autogenerated(self):
        self.assertTrue(self.products.slug)
        self.assertTrue(self.books.slug)

    def test_supplied_slug_is_not_altered(self):
        more_books = self.products.add_child(name=self.books.name, slug=self.books.slug)
        self.assertEqual(more_books.slug, self.books.slug)

    @override_settings(OSCAR_SLUG_ALLOW_UNICODE=True)
    def test_unicode_slug(self):
        root_category = Category.add_root(name="Vins français")
        child_category = root_category.add_child(name="Château d'Yquem")
        self.assertEqual(root_category.slug, "vins-français")
        self.assertEqual(
            root_category.get_absolute_url(),
            f"/catalogue/category/vins-fran%C3%A7ais_{root_category.pk}/",
        )
        self.assertEqual(child_category.slug, "château-dyquem")
        self.assertEqual(
            child_category.get_absolute_url(),
            f"/catalogue/category/vins-fran%C3%A7ais/ch%C3%A2teau-dyquem_{child_category.pk}/",
        )

    @override_settings(OSCAR_SLUG_ALLOW_UNICODE=True)
    def test_url_caching(self):
        category = self.products.add_child(name="Fromages français")
        absolute_url = category.get_absolute_url()
        url = cache.get(category.get_url_cache_key())
        self.assertEqual(url, "products/fromages-français")
        self.assertEqual(
            absolute_url,
            f"/catalogue/category/products/fromages-fran%C3%A7ais_{category.pk}/",
        )


class TestMovingACategory(TestCase):
    def setUp(self):
        super().setUp()
        breadcrumbs = (
            "Books > Fiction > Horror > Teen",
            "Books > Fiction > Horror > Gothic",
            "Books > Fiction > Comedy",
            "Books > Non-fiction > Biography",
            "Books > Non-fiction > Programming",
            "Books > Children",
        )
        for trail in breadcrumbs:
            create_from_breadcrumbs(trail)

        horror = Category.objects.get(name="Horror")
        programming = Category.objects.get(name="Programming")
        horror.move(programming)

        # Reload horror instance to pick up changes
        self.horror = Category.objects.get(name="Horror")

    def test_updates_instance_name(self):
        self.assertEqual("Books > Non-fiction > Horror", self.horror.full_name)

    def test_updates_subtree_names(self):
        teen = Category.objects.get(name="Teen")
        self.assertEqual("Books > Non-fiction > Horror > Teen", teen.full_name)
        gothic = Category.objects.get(name="Gothic")
        self.assertEqual("Books > Non-fiction > Horror > Gothic", gothic.full_name)


class TestCategoryFactory(TestCase):
    def setUp(self):
        super().setUp()

    def test_can_create_single_level_category(self):
        trail = "Books"
        category = create_from_breadcrumbs(trail)
        self.assertIsNotNone(category)
        self.assertEqual(category.name, "Books")
        self.assertEqual(category.slug, "books")

    def test_can_create_parent_and_child_categories(self):
        trail = "Books > Science-Fiction"
        category = create_from_breadcrumbs(trail)

        self.assertIsNotNone(category)
        self.assertEqual(category.name, "Science-Fiction")
        self.assertEqual(category.get_depth(), 2)
        self.assertEqual(category.get_parent().name, "Books")
        self.assertEqual(2, Category.objects.count())
        self.assertEqual(category.full_slug, "books/science-fiction")

    def test_can_create_multiple_categories(self):
        trail = "Books > Science-Fiction > Star Trek"
        create_from_breadcrumbs(trail)
        trail = "Books > Factual > Popular Science"
        category = create_from_breadcrumbs(trail)

        self.assertIsNotNone(category)
        self.assertEqual(category.name, "Popular Science")
        self.assertEqual(category.get_depth(), 3)
        self.assertEqual(category.get_parent().name, "Factual")
        self.assertEqual(5, Category.objects.count())
        self.assertEqual(
            category.full_slug,
            "books/factual/popular-science",
        )

    def test_can_use_alternative_separator(self):
        trail = "Food|Cheese|Blue"
        create_from_breadcrumbs(trail, separator="|")
        self.assertEqual(3, len(Category.objects.all()))

    def test_updating_subtree_slugs_when_moving_category_to_new_parent(self):
        trail = "A > B > C"
        create_from_breadcrumbs(trail)
        trail = "A > B > D"
        create_from_breadcrumbs(trail)
        trail = "A > E > F"
        create_from_breadcrumbs(trail)
        trail = "A > E > G"
        create_from_breadcrumbs(trail)

        trail = "T"
        target = create_from_breadcrumbs(trail)
        category = Category.objects.get(name="A")

        category.move(target, pos="first-child")

        c1 = Category.objects.get(name="A")
        self.assertEqual(c1.full_slug, "t/a")
        self.assertEqual(c1.full_name, "T > A")

        child = Category.objects.get(name="F")
        self.assertEqual(child.full_slug, "t/a/e/f")
        self.assertEqual(child.full_name, "T > A > E > F")

        child = Category.objects.get(name="D")
        self.assertEqual(child.full_slug, "t/a/b/d")
        self.assertEqual(child.full_name, "T > A > B > D")

    def test_updating_subtree_when_moving_category_to_new_sibling(self):
        trail = "A > B > C"
        create_from_breadcrumbs(trail)
        trail = "A > B > D"
        create_from_breadcrumbs(trail)
        trail = "A > E > F"
        create_from_breadcrumbs(trail)
        trail = "A > E > G"
        create_from_breadcrumbs(trail)

        category = Category.objects.get(name="E")
        target = Category.objects.get(name="A")

        category.move(target, pos="right")

        child = Category.objects.get(name="E")
        self.assertEqual(child.full_slug, "e")
        self.assertEqual(child.full_name, "E")

        child = Category.objects.get(name="F")
        self.assertEqual(child.full_slug, "e/f")
        self.assertEqual(child.full_name, "E > F")


class TestCategoryTemplateTags(TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.template = """
          {% if tree_categories %}
              <ul>
              {% for tree_category, info in tree_categories %}
                  <li>
                  {% if tree_category.pk == category.pk %}
                      <strong>{{ tree_category.name }}</strong>
                  {% else %}
                      <a href="{{ tree_category.get_absolute_url }}">
                          {{ tree_category.name }}</a>
                  {% endif %}
                  {% if info.has_children %}<ul>{% else %}</li>{% endif %}
                  {% for n in info.num_to_close %}
                      </ul></li>
                  {% endfor %}
              {% endfor %}
              </ul>
          {% endif %}
        """

    def setUp(self):
        super().setUp()
        breadcrumbs = (
            "Books > Fiction > Horror > Teen",
            "Books > Fiction > Horror > Gothic",
            "Books > Fiction > Comedy",
            "Books > Non-fiction > Biography",
            "Books > Non-fiction > Programming",
            "Books > Children",
        )
        for trail in breadcrumbs:
            create_from_breadcrumbs(trail)

    def get_category_names(self, depth=None, parent=None):
        """
        For the tests, we are only interested in the category names returned
        from the template tag. This helper calls the template tag and
        returns a list of the included categories.
        """
        annotated_list = get_annotated_list(depth, parent)
        names = [category.name for category, __ in annotated_list]

        names_set = set(names)
        # We return a set to ease testing, but need to be sure we're not
        # losing any duplicates through that conversion.
        self.assertEqual(len(names_set), len(names))
        return names_set

    def test_all_categories(self):
        expected_categories = {
            "Books",
            "Fiction",
            "Horror",
            "Teen",
            "Gothic",
            "Comedy",
            "Non-fiction",
            "Biography",
            "Programming",
            "Children",
        }
        actual_categories = self.get_category_names()
        self.assertEqual(expected_categories, actual_categories)

    def test_categories_depth(self):
        expected_categories = {"Books"}
        actual_categories = self.get_category_names(depth=1)
        self.assertEqual(expected_categories, actual_categories)

    def test_categories_parent(self):
        parent = Category.objects.get(name="Fiction")
        actual_categories = self.get_category_names(parent=parent)
        expected_categories = {"Horror", "Teen", "Gothic", "Comedy"}
        self.assertEqual(expected_categories, actual_categories)

    def test_categories_depth_parent(self):
        parent = Category.objects.get(name="Fiction")
        actual_categories = self.get_category_names(depth=1, parent=parent)
        expected_categories = {"Horror", "Comedy"}
        self.assertEqual(expected_categories, actual_categories)


# -------  TestOption -----------
class ProductOptionTests(TestCase):
    def setUp(self):
        super().setUp()
        self.product_class = factories.ProductClassFactory()
        self.product = factories.create_product(product_class=self.product_class)
        self.option = factories.OptionFactory()

    def test_product_has_options_per_product_class(self):
        self.product_class.options.add(self.option)
        self.assertTrue(self.product.has_options)

    def test_product_has_options_per_product(self):
        self.product.product_options.add(self.option)
        self.assertTrue(self.product.has_options)

    def test_queryset_per_product_class(self):
        self.product_class.options.add(self.option)
        qs = Product.objects.browsable().base_queryset().filter(id=self.product.id)
        product = qs.first()
        self.assertTrue(product.has_options)
        self.assertTrue(product.has_product_class_options)

    def test_queryset_per_product(self):
        self.product.product_options.add(self.option)
        qs = Product.objects.browsable().base_queryset().filter(id=self.product.id)
        product = qs.first()
        self.assertTrue(product.has_options)
        self.assertTrue(product.has_product_options, 1)

    def test_queryset_both(self):
        "The options attribute on a product should return a queryset containing"
        "both the product class options and any extra options defined on the"
        "product"
        # set up the options on product and product_class
        self.test_product_has_options_per_product_class()
        self.test_product_has_options_per_product()
        self.assertTrue(self.product.has_options, "Options should be present")
        self.assertEqual(
            self.product.options.count(),
            1,
            "options attribute should not contain duplicates",
        )
        qs = Product.objects.browsable().base_queryset().filter(id=self.product.id)
        product = qs.first()
        self.assertTrue(
            product.has_product_class_options,
            "has_product_class_options should indicate the product_class option",
        )
        self.assertTrue(
            product.has_product_options,
            "has_product_options should indicate the number of product options",
        )
        self.product_class.options.add(factories.OptionFactory(code="henk"))
        self.assertEqual(
            self.product.options.count(),
            2,
            "New product_class options should be immediately visible",
        )
        self.product.product_options.add(factories.OptionFactory(code="klaas"))
        self.assertEqual(
            self.product.options.count(),
            3,
            "New product options should be immediately visible",
        )


# -------  TestProductClass -----------
class TestProductClassModel(TestCase):
    def test_slug_is_auto_created(self):
        books = models.ProductClass.objects.create(
            name="Book",
        )
        self.assertEqual("book", books.slug)

    def test_has_attribute_for_whether_shipping_is_required(self):
        models.ProductClass.objects.create(
            name="Download",
            requires_shipping=False,
        )


# -------  TestProductImages -----------
class TestProductImages(ThumbnailMixin, TestCase):
    def setUp(self):
        TestCase.setUp(self)

    def _test_product_images_and_thumbnails_deleted_when_product_deleted(self):
        product = factories.create_product()
        images_qty = 3
        self.create_product_images(qty=images_qty, product=product)

        assert product.images.count() == images_qty
        thumbnails_full_paths = self.create_thumbnails()

        product.delete()

        self._test_images_folder_is_empty()
        self._test_thumbnails_not_exist(thumbnails_full_paths)

    def test_images_are_in_consecutive_order(self):
        product = factories.create_product()
        for i in range(4):
            factories.create_product_image(product=product, display_order=i)

        product.images.all()[2].delete()

        for idx, im in enumerate(product.images.all()):
            self.assertEqual(im.display_order, idx)

    def test_variant_images(self):
        parent = factories.ProductFactory(structure="parent")
        variant = factories.create_product(parent=parent)
        factories.create_product_image(product=variant, caption="Variant Image")
        all_images = variant.get_all_images()
        self.assertEqual(all_images.count(), 1)
        product_image = all_images.first()
        self.assertEqual(product_image.caption, "Variant Image")

    def test_variant_images_fallback_to_parent(self):
        parent = factories.ProductFactory(structure="parent")
        variant = factories.create_product(parent=parent)
        factories.create_product_image(product=parent, caption="Parent Product Image")
        all_images = variant.get_all_images()
        self.assertEqual(all_images.count(), 1)
        product_image = all_images.first()
        self.assertEqual(product_image.caption, "Parent Product Image")


class TestMissingProductImage(StaticLiveServerTestCase):
    TEMP_MEDIA_ROOT = tempfile.mkdtemp()

    @override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
    @mock.patch("oscar.apps.catalogue.abstract_models.find")
    def test_symlink_creates_directories(self, mock_find):
        # Create a fake empty file to symlink
        img = tempfile.NamedTemporaryFile(delete=False)
        img.close()

        mock_find.return_value = img.name
        # Initialise the class with a nested path
        path = "image/path.jpg"
        MissingProductImage(path)
        # Check that the directory exists
        image_path = os.path.join(self.TEMP_MEDIA_ROOT, path)
        self.assertTrue(os.path.exists(image_path))

        # Clean up
        for f in [image_path, img.name]:
            os.unlink(f)
        for d in [os.path.join(self.TEMP_MEDIA_ROOT, "image"), self.TEMP_MEDIA_ROOT]:
            os.rmdir(d)

    @override_settings(MEDIA_ROOT="")
    @mock.patch(
        "oscar.apps.catalogue.abstract_models.MissingProductImage.symlink_missing_image"
    )
    def test_no_symlink_when_no_media_root(self, mock_symlink):
        MissingProductImage()
        self.assertEqual(mock_symlink.call_count, 0)


# -------  TestProduct -----------
class ProductTests(TestCase):
    def setUp(self):
        super().setUp()
        self.product_class, _ = ProductClass.objects.get_or_create(name="Clothing")


class ProductCreationTests(ProductTests):
    def setUp(self):
        super().setUp()
        ProductAttribute.objects.create(
            product_class=self.product_class,
            name="Number of pages",
            code="num_pages",
            type="integer",
        )
        Product.ENABLE_ATTRIBUTE_BINDING = True

    def tearDown(self):
        Product.ENABLE_ATTRIBUTE_BINDING = False

    def test_create_products_with_attributes(self):
        product = Product(upc="1234", product_class=self.product_class, title="testing")
        product.attr.num_pages = 100
        product.save()

    def test_none_upc_is_represented_as_empty_string(self):
        product = Product(product_class=self.product_class, title="testing", upc=None)
        product.save()
        product.refresh_from_db()
        self.assertEqual(product.upc, "")

    def test_upc_uniqueness_enforced(self):
        Product.objects.create(
            product_class=self.product_class, title="testing", upc="bah"
        )
        self.assertRaises(
            IntegrityError,
            Product.objects.create,
            product_class=self.product_class,
            title="testing",
            upc="bah",
        )

    def test_allow_two_products_without_upc(self):
        for x in range(2):
            Product.objects.create(
                product_class=self.product_class, title="testing", upc=None
            )


class TopLevelProductTests(ProductTests):
    def test_top_level_products_must_have_titles(self):
        product = Product(product_class=self.product_class)
        self.assertRaises(ValidationError, product.clean)

    def test_top_level_products_must_have_product_class(self):
        product = Product(title="Kopfhörer")
        self.assertRaises(ValidationError, product.clean)

    # def test_top_level_products_are_part_of_browsable_set(self):
    #     product = Product.objects.create(
    #         product_class=self.product_class, title="Kopfhörer")
    #     self.assertEqual(set([product]), set(Product.objects.browsable()))


class ChildProductTests(ProductTests):
    def setUp(self):
        super().setUp()
        self.parent = Product.objects.create(
            title="Parent product",
            product_class=self.product_class,
            structure=Product.PARENT,
            is_discountable=False,
        )
        ProductAttribute.objects.create(
            product_class=self.product_class,
            name="The first attribute",
            code="first_attribute",
            type="text",
        )
        ProductAttribute.objects.create(
            product_class=self.product_class,
            name="The second attribute",
            code="second_attribute",
            type="text",
        )

    def test_child_products_dont_need_titles(self):
        Product.objects.create(parent=self.parent, structure=Product.CHILD)

    def test_child_products_dont_need_a_product_class(self):
        Product.objects.create(parent=self.parent, structure=Product.CHILD)

    def test_child_products_inherit_fields(self):
        p = Product.objects.create(
            parent=self.parent, structure=Product.CHILD, is_discountable=True
        )
        self.assertEqual("Parent product", p.get_title())
        self.assertEqual("Clothing", p.get_product_class().name)

    # def test_child_products_are_not_part_of_browsable_set(self):
    #     Product.objects.create(
    #         product_class=self.product_class, parent=self.parent,
    #         structure=Product.CHILD)
    #     self.assertEqual(set([self.parent]), set(Product.objects.browsable()))

    def test_child_products_attribute_values(self):
        product = Product.objects.create(
            product_class=self.product_class,
            parent=self.parent,
            structure=Product.CHILD,
        )

        self.parent.attr.first_attribute = "klats"
        product.attr.second_attribute = "henk"
        self.parent.save()
        product.save()

        product = Product.objects.get(pk=product.pk)
        parent = Product.objects.get(pk=self.parent.pk)

        self.assertEqual(parent.get_attribute_values().count(), 1)
        self.assertEqual(product.get_attribute_values().count(), 2)
        self.assertTrue(hasattr(parent.attr, "first_attribute"))
        self.assertFalse(hasattr(parent.attr, "second_attribute"))
        self.assertTrue(hasattr(product.attr, "first_attribute"))
        self.assertTrue(hasattr(product.attr, "second_attribute"))

    def test_child_products_attribute_values_no_parent_values(self):
        product = Product.objects.create(
            product_class=self.product_class,
            parent=self.parent,
            structure=Product.CHILD,
        )

        product.attr.second_attribute = "henk"
        product.save()

        product = Product.objects.get(pk=product.pk)

        self.assertEqual(self.parent.get_attribute_values().count(), 0)
        self.assertEqual(product.get_attribute_values().count(), 1)
        self.assertFalse(hasattr(self.parent.attr, "first_attribute"))
        self.assertFalse(hasattr(self.parent.attr, "second_attribute"))
        self.assertFalse(hasattr(product.attr, "first_attribute"))
        self.assertTrue(hasattr(product.attr, "second_attribute"))


class TestAChildProduct(TestCase):
    def setUp(self):
        super().setUp()
        clothing = ProductClass.objects.create(name="Clothing", requires_shipping=True)
        self.parent = clothing.products.create(title="Parent", structure=Product.PARENT)
        self.child = self.parent.children.create(structure=Product.CHILD)

    def test_delegates_requires_shipping_logic(self):
        self.assertTrue(self.child.is_shipping_required)


class ProductAttributeCreationTests(TestCase):
    def test_validating_option_attribute(self):
        option_group = factories.AttributeOptionGroupFactory()
        option_1 = factories.AttributeOptionFactory(group=option_group)
        option_2 = factories.AttributeOptionFactory(group=option_group)
        pa = factories.ProductAttributeFactory(type="option", option_group=option_group)

        self.assertRaises(ValidationError, pa.validate_value, "invalid")
        pa.validate_value(option_1)
        pa.validate_value(option_2)

        invalid_option = AttributeOption(option="invalid option")
        self.assertRaises(ValidationError, pa.validate_value, invalid_option)

    def test_entity_attributes(self):
        unrelated_object = factories.PartnerFactory()
        attribute = factories.ProductAttributeFactory(type="entity")

        attribute_value = factories.ProductAttributeValueFactory(
            attribute=attribute, value_entity=unrelated_object
        )

        self.assertEqual(attribute_value.value, unrelated_object)


class ProductRecommendationTests(ProductTests):
    def setUp(self):
        super().setUp()
        self.primary_product = Product.objects.create(
            upc="1234", product_class=self.product_class, title="Primary Product"
        )

    def test_recommended_products_ordering(self):
        secondary_products = [
            Product.objects.create(
                upc=f"secondary{i}",
                product_class=self.product_class,
                title=f"Secondary Product #{i}",
            )
            for i in range(5)
        ]
        ProductRecommendation.objects.create(
            primary=self.primary_product,
            recommendation=secondary_products[3],
            ranking=5,
        )
        ProductRecommendation.objects.create(
            primary=self.primary_product,
            recommendation=secondary_products[1],
            ranking=2,
        )
        ProductRecommendation.objects.create(
            primary=self.primary_product,
            recommendation=secondary_products[2],
            ranking=4,
        )
        ProductRecommendation.objects.create(
            primary=self.primary_product,
            recommendation=secondary_products[4],
            ranking=1,
        )
        ProductRecommendation.objects.create(
            primary=self.primary_product,
            recommendation=secondary_products[0],
            ranking=3,
        )
        recommended_products = [
            secondary_products[3],
            secondary_products[2],
            secondary_products[0],
            secondary_products[1],
            secondary_products[4],
        ]
        self.assertEqual(
            self.primary_product.sorted_recommended_products, recommended_products
        )


class ProductAttributeTest(TestCase):
    def setUp(self):
        super().setUp()
        Category.objects.all().delete()
        # setup the productclass
        self.product_class = product_class = ProductClassFactory(
            name="Cows", slug="cows"
        )
        self.name_attr = ProductAttributeFactory(
            type=ProductAttribute.TEXT,
            product_class=product_class,
            name="name",
            code="name",
        )
        self.weight_attr = ProductAttributeFactory(
            type=ProductAttribute.INTEGER,
            name="weight",
            code="weight",
            product_class=product_class,
            required=True,
        )
        self.richtext_attr = ProductAttributeFactory(
            type=ProductAttribute.RICHTEXT,
            name="html",
            code="html",
            product_class=product_class,
            required=False,
        )

        # create the parent product
        self.product = product = ProductFactory(
            title="I am your father",
            stockrecords=None,
            product_class=product_class,
            structure="parent",
            upc="1234",
        )
        product.attr.weight = 3
        product.full_clean()
        product.save()

        # create the child product
        self.child_product = ProductFactory(
            parent=product,
            structure="child",
            categories=None,
            product_class=None,
            title="You are my father",
            upc="child-1234",
        )
        self.child_product.full_clean()

    def test_update_child_with_attributes(self):
        """
        Attributes preseent on the parent should not be copied to the child
        when title of the child is modified
        """

        self.assertEqual(
            ProductAttributeValue.objects.filter(product_id=self.product.pk).count(),
            1,
            "The parent has 1 attributes",
        )

        # establish baseline
        self.assertEqual(
            ProductAttributeValue.objects.filter(product=self.child_product).count(),
            0,
            "The child has no attributes",
        )
        self.assertEqual(self.child_product.parent_id, self.product.pk)
        self.assertIsNone(self.child_product.product_class)
        self.assertEqual(self.child_product.upc, "child-1234")
        self.assertEqual(self.child_product.slug, "you-are-my-father")
        self.assertNotEqual(self.child_product.title, "Klaas is my real father")

        self.child_product.title = "Klaas is my real father"
        self.child_product.save()

        self.child_product.refresh_from_db()
        self.assertEqual(self.child_product.title, "Klaas is my real father")
        self.assertEqual(
            ProductAttributeValue.objects.filter(product=self.child_product).count(),
            0,
            "The child has no attributes",
        )

    def test_update_child_attributes(self):
        """
        Attributes preseent on the parent should not be copied to the child
        when the child attributes are modified
        """

        self.assertEqual(
            ProductAttributeValue.objects.filter(product_id=self.product.pk).count(),
            1,
            "The parent has 1 attributes",
        )

        # establish baseline
        self.assertEqual(
            ProductAttributeValue.objects.filter(product=self.child_product).count(),
            0,
            "The child has no attributes",
        )
        self.assertEqual(self.child_product.parent_id, self.product.pk)
        self.assertIsNone(self.child_product.product_class)
        self.assertEqual(self.child_product.upc, "child-1234")
        self.assertEqual(self.child_product.slug, "you-are-my-father")
        self.assertNotEqual(self.child_product.title, "Klaas is my real father")

        self.child_product.title = "Klaas is my real father"
        self.child_product.attr.name = "Berta"
        self.child_product.save()

        self.child_product.refresh_from_db()
        self.assertEqual(self.child_product.title, "Klaas is my real father")
        self.assertEqual(
            ProductAttributeValue.objects.filter(product=self.child_product).count(),
            1,
            "The child now has 1 attribute",
        )

    def test_update_attributes_to_parent_and_child(self):
        """
        Attributes present on the parent should not be copied to the child
        ever, not even newly added attributes
        """

        self.assertEqual(
            ProductAttributeValue.objects.filter(product_id=self.product.pk).count(),
            1,
            "The parent has 1 attributes",
        )
        self.product.attr.name = "Greta"
        self.product.save()
        self.product.refresh_from_db()
        self.product.attr.refresh()

        self.assertEqual(
            ProductAttributeValue.objects.filter(product_id=self.product.pk).count(),
            2,
            "The parent now has 2 attributes",
        )

        # establish baseline
        self.assertEqual(
            ProductAttributeValue.objects.filter(product=self.child_product).count(),
            0,
            "The child has no attributes",
        )
        self.assertEqual(self.child_product.parent_id, self.product.pk)
        self.assertIsNone(self.child_product.product_class)
        self.assertEqual(self.child_product.upc, "child-1234")
        self.assertEqual(self.child_product.slug, "you-are-my-father")
        self.assertNotEqual(self.child_product.title, "Klaas is my real father")

        self.child_product.title = "Klaas is my real father"
        self.child_product.attr.name = "Berta"
        self.child_product.save()

        self.child_product.refresh_from_db()
        self.assertEqual(self.child_product.title, "Klaas is my real father")
        self.assertEqual(
            ProductAttributeValue.objects.filter(product=self.child_product).count(),
            1,
            "The child now has 1 attribute",
        )

    def test_explicit_identical_child_attribute(self):
        self.assertEqual(self.product.attr.weight, 3, "parent product has weight 3")
        self.assertEqual(
            self.child_product.attr.weight, 3, "chiuld product also has weight 3"
        )
        self.assertEqual(
            ProductAttributeValue.objects.filter(product_id=self.product.pk).count(),
            1,
            "The parent has 1 attributes, which is the weight",
        )
        self.assertEqual(
            ProductAttributeValue.objects.filter(product=self.child_product).count(),
            0,
            "The child has no attributes, because it gets weight from the parent",
        )
        # explicitly set a value to the child
        self.child_product.attr.weight = 3
        self.child_product.full_clean()
        self.child_product.save()
        self.assertEqual(
            ProductAttributeValue.objects.filter(product=self.child_product).count(),
            1,
            "The child now has 1 attribute, because we explicitly set the attribute, "
            "so it saved, even when the parent has the same value",
        )

    def test_delete_attribute_value(self):
        "Attributes should be deleted when they are nulled"
        self.assertEqual(self.product.attr.weight, 3)
        self.product.attr.weight = None
        self.product.save()

        p = Product.objects.get(pk=self.product.pk)
        with self.assertRaises(AttributeError):
            p.attr.weight  # pylint: disable=pointless-statement

    def test_validate_attribute_value(self):
        self.test_delete_attribute_value()
        with self.assertRaises(ValidationError):
            self.product.attr.validate_attributes()

    def test_deepcopy(self):
        "Deepcopy should not cause a recursion error"
        deepcopy(self.product)
        deepcopy(self.child_product)

    def test_set(self):
        "Attributes should be settable from a string key"
        self.product.attr.set("weight", 101)
        self.assertEqual(self.product.attr._dirty, {"weight"})
        self.product.attr.save()

        p = Product.objects.get(pk=self.product.pk)

        self.assertEqual(p.attr.weight, 101)

    def test_set_error(self):
        "set should only accept attributes which are valid python identifiers"
        with self.assertRaises(ValidationError):
            self.product.attr.set("bina-weight", 101)

        with self.assertRaises(ValidationError):
            self.product.attr.set("8_oepla", "oegaranos")

        with self.assertRaises(ValidationError):
            self.product.attr.set("set", "validate_identifier=True")

        with self.assertRaises(ValidationError):
            self.product.attr.set("save", "raise=True")

    def test_update(self):
        "Attributes should be updateble from a dictionary"
        self.product.attr.update({"weight": 808, "name": "a banana"})
        self.assertEqual(self.product.attr._dirty, {"weight", "name"})
        self.product.attr.save()

        p = Product.objects.get(pk=self.product.pk)

        self.assertEqual(p.attr.weight, 808)
        self.assertEqual(p.attr.name, "a banana")

    def test_validate_attributes(self):
        "validate_attributes should raise ValidationError on erroneous inputs"
        self.product.attr.validate_attributes()
        self.product.attr.weight = "koe"
        with self.assertRaises(ValidationError):
            self.product.attr.validate_attributes()

    def test_get_attribute_by_code(self):
        at = self.product.attr.get_attribute_by_code("weight")
        self.assertEqual(at.code, "weight")
        self.assertEqual(at.product_class, self.product.get_product_class())

        self.assertIsNone(self.product.attr.get_attribute_by_code("stoubafluppie"))

    def test_attribute_html(self):
        self.product.attr.html = "<h1>Hi</h1>"
        self.product.save()

        value = self.product.attr.get_value_by_attribute(self.richtext_attr)
        html = value.value_as_html
        self.assertEqual(html, "<h1>Hi</h1>")
        self.assertTrue(hasattr(html, "__html__"))


class MultiOptionTest(TestCase):
    fixtures = ["productattributes.json"]
    maxDiff = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_multi_option_recursion_error(self):
        product = Product.objects.get(pk=4)
        with self.assertRaises(ValueError):
            product.attr.set("subkinds", "harrie")
            product.save()

    def test_value_as_html(self):
        product = Product.objects.get(pk=4)
        # pylint: disable=unused-variable
        (
            additional_info,
            available,
            facets,
            hypothenusa,
            kind,
            releasedate,
            starttime,
            subkinds,
            subtitle,
        ) = product.attr.get_values().order_by("id")

        self.assertTrue(
            additional_info.value_as_html.startswith(
                '<p style="margin: 0px; font-stretch: normal; font-size: 12px;'
            )
        )
        self.assertEqual(available.value_as_html, "Yes")
        self.assertEqual(kind.value_as_html, "bombastic")
        self.assertEqual(subkinds.value_as_html, "grand, verocious, megalomane")
        self.assertEqual(subtitle.value_as_html, "kekjo")

    @unittest.skip("The implementation is wrong, which makes these tests fail")
    def test_broken_value_as_html(self):
        product = Product.objects.get(pk=4)
        # pylint: disable=unused-variable
        (
            additional_info,
            available,
            facets,
            hypothenusa,
            kind,
            releasedate,
            starttime,
            subkinds,
            subtitle,
        ) = product.attr.get_values().order_by("id")

        self.assertEqual(starttime.value_as_html, "2018-11-16T09:15:00+00:00")
        self.assertEqual(facets.value_as_html, "4")
        self.assertEqual(releasedate.value_as_html, "2018-11-16")
        self.assertEqual(hypothenusa.value_as_html, "2.4567")


class ProductAttributeQuerysetTest(TestCase):
    fixtures = ["productattributes.json"]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_query_multiple_producttypes(self):
        "We should be able to query over multiple product classes"
        result = Product.objects.filter_by_attributes(henkie="bah bah")
        self.assertEqual(result.count(), 2)
        result1, result2 = list(result)

        self.assertNotEqual(result1.product_class, result2.product_class)
        self.assertEqual(result1.attr.henkie, result2.attr.henkie)

    def test_further_filtering(self):
        "The returned queryset should be ready for further filtering"
        result = Product.objects.filter_by_attributes(henkie="bah bah")
        photo = result.filter(title__contains="Photo")
        self.assertEqual(photo.count(), 1)

    def test_empty_results(self):
        "Empty results are possible without errors"
        result = Product.objects.filter_by_attributes(doesnotexist=True)
        self.assertFalse(
            result.exists(), "querying with bulshit attributes should give no results"
        )
        result = Product.objects.filter_by_attributes(henkie="zulthoofd")
        self.assertFalse(
            result.exists(), "querying with non existing values should give no results"
        )
        result = Product.objects.filter_by_attributes(henkie=True)
        self.assertFalse(
            result.exists(), "querying with wring value type should give no results"
        )

    def test_text_value(self):
        result = Product.objects.filter_by_attributes(subtitle="superhenk")
        self.assertTrue(result.exists())
        result = Product.objects.filter_by_attributes(subtitle="kekjo")
        self.assertTrue(result.exists())
        result = Product.objects.filter_by_attributes(subtitle=True)
        self.assertFalse(result.exists())

    def test_formatted_text(self):
        html = '<p style="margin: 0px; font-stretch: normal; font-size: 12px; line-height: normal; font-family: Helvetica;">Vivamus auctor leo vel dui. Aliquam erat volutpat. Phasellus nibh. Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia Curae; Cras tempor. Morbi egestas, <em>urna</em> non consequat tempus, <strong>nunc</strong> arcu mollis enim, eu aliquam erat nulla non nibh. Duis consectetuer malesuada velit. Nam ante nulla, interdum vel, tristique ac, condimentum non, tellus. Proin ornare feugiat nisl. Suspendisse dolor nisl, ultrices at, eleifend vel, consequat at, dolor.</p>'  # noqa
        result = Product.objects.filter_by_attributes(additional_info=html)
        self.assertTrue(result.exists())

    def test_boolean(self):
        result = Product.objects.filter_by_attributes(available=True)
        self.assertTrue(result.exists())
        result = Product.objects.filter_by_attributes(available=0)
        self.assertTrue(result.exists())
        with self.assertRaises(ValidationError):
            result = Product.objects.filter_by_attributes(available="henk")

    def test_number(self):
        result = Product.objects.filter_by_attributes(facets=4)
        self.assertTrue(result.exists())
        with self.assertRaises(ValueError):
            result = Product.objects.filter_by_attributes(facets="four")

        result = Product.objects.filter_by_attributes(facets=1)
        self.assertFalse(result.exists())

    def test_float(self):
        result = Product.objects.filter_by_attributes(hypothenusa=1.25)
        self.assertTrue(result.exists())
        with self.assertRaises(ValueError):
            result = Product.objects.filter_by_attributes(facets="four")

        result = Product.objects.filter_by_attributes(hypothenusa=1)
        self.assertFalse(result.exists())

    def test_option(self):
        result = Product.objects.filter_by_attributes(kind="totalitarian")
        self.assertTrue(result.exists())
        result = Product.objects.filter_by_attributes(kind=True)
        self.assertFalse(result.exists())

        result = Product.objects.filter_by_attributes(kind="omnimous")
        self.assertFalse(result.exists())

    def test_multi_option(self):
        result = Product.objects.filter_by_attributes(subkinds="megalomane")
        self.assertTrue(result.exists())
        self.assertEqual(result.count(), 2)
        result = Product.objects.filter_by_attributes(subkinds=True)
        self.assertFalse(result.exists())

        result = Product.objects.filter_by_attributes(subkinds="omnimous")
        self.assertFalse(result.exists())

        result = Product.objects.filter_by_attributes(subkinds__contains="om")
        self.assertTrue(result.exists(), "megalomane conains om")
        self.assertEqual(result.count(), 2)

    def test_multiple_attributes(self):
        result = Product.objects.filter_by_attributes(
            subkinds="megalomane", available=True
        )
        self.assertTrue(result.exists())

        result = Product.objects.filter_by_attributes(
            kind="totalitarian",
            hypothenusa=1.25,
            facets=8,
            subtitle="superhenk",
            subkinds="megalomane",
            available=False,
        )
        self.assertTrue(result.exists())

    def test_lookups(self):
        result = Product.objects.filter_by_attributes(facets__lte=4)
        self.assertEqual(result.count(), 1)

        result = Product.objects.filter_by_attributes(facets__lte=8)
        self.assertEqual(result.count(), 2)

        result = Product.objects.filter_by_attributes(facets__lt=8)
        self.assertEqual(result.count(), 1)
