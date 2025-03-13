import datetime
import io
import os
from http import client as http_client

from django.conf import settings
from django.contrib.messages import ERROR
from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import gettext
from oscar.apps.catalogue.categories import create_from_breadcrumbs
from oscar.core.compat import get_user_model
from oscar.core.loading import get_class
from PIL import Image
from webtest import Upload

from ecommerce.apps.catalogue.models import (
    AttributeOption,
    AttributeOptionGroup,
    Category,
    Option,
    Product,
    ProductAttribute,
    ProductCategory,
    ProductClass,
    ProductImage,
)
from ecommerce.apps.dashboard.catalogue.views import ProductListView
from ecommerce.apps.partner.models import StockRecord
from ecommerce.test import factories
from ecommerce.test.factories import (
    AttributeOptionFactory,
    AttributeOptionGroupFactory,
    CategoryFactory,
    OptionFactory,
    PartnerFactory,
    ProductAttributeFactory,
    ProductClassFactory,
    ProductFactory,
    UserFactory,
    create_product,
)
from ecommerce.test.testcases import (
    ListViewMixin,
    PopUpObjectCreateMixin,
    PopUpObjectDeleteMixin,
    PopUpObjectUpdateMixin,
    TestCase,
    WebTestCase,
    add_permissions,
)
from ecommerce.test.utils import RequestFactory

User = get_user_model()


AttributeOptionGroupForm = get_class(
    "dashboard.catalogue.forms", "AttributeOptionGroupForm", "ecommerce.apps"
)
AttributeOptionFormSet = get_class(
    "dashboard.catalogue.formsets", "AttributeOptionFormSet", "ecommerce.apps"
)
RelatedFieldWidgetWrapper = get_class(
    "dashboard.widgets", "RelatedFieldWidgetWrapper", "ecommerce.apps"
)
OptionForm = get_class("dashboard.catalogue.forms", "OptionForm", "ecommerce.apps")


def generate_test_image():
    tempfile = io.BytesIO()
    image = Image.new("RGBA", size=(50, 50), color=(256, 0, 0))
    image.save(tempfile, "PNG")
    tempfile.seek(0)
    return tempfile.read()


def media_file_path(path):
    return os.path.join(settings.MEDIA_ROOT, "fast_test", path)


class ProductWebTest(WebTestCase):
    is_staff = True

    def setUp(self):
        super().setUp()
        self.user = User.objects.get(username=self.username)
        self.user.is_staff = self.is_staff
        self.user.save()

    def get(self, url, **kwargs):
        kwargs["user"] = self.user
        return self.app.get(url, **kwargs)


class TestGatewayPage(ProductWebTest):
    is_staff = True

    def test_redirects_to_list_page_when_no_query_param(self):
        url = reverse("dashboard:catalogue-product-create")
        response = self.get(url)
        self.assertRedirects(response, reverse("dashboard:catalogue-product-list"))

    def test_redirects_to_list_page_when_invalid_query_param(self):
        url = reverse("dashboard:catalogue-product-create")
        response = self.get(f"{url}?product_class=bad")
        self.assertRedirects(response, reverse("dashboard:catalogue-product-list"))

    def test_redirects_to_form_page_when_valid_query_param(self):
        pclass = ProductClassFactory(name="Books", slug="books")
        url = reverse("dashboard:catalogue-product-create")
        response = self.get(f"{url}?product_class={pclass.pk}")
        expected_url = reverse(
            "dashboard:catalogue-product-create",
            kwargs={"product_class_slug": pclass.slug},
        )
        self.assertRedirects(response, expected_url)


class TestCreateParentProduct(ProductWebTest):
    is_staff = True

    def setUp(self):
        super().setUp()
        self.pclass = ProductClassFactory(name="Books", slug="books")

    def submit(self, title=None, category=None, upc=None):
        url = reverse(
            "dashboard:catalogue-product-create",
            kwargs={"product_class_slug": self.pclass.slug},
        )

        product_form = self.get(url).form

        product_form["title"] = title
        product_form["upc"] = upc
        product_form["structure"] = "parent"

        if category:
            product_form["productcategory_set-0-category"] = category.id

        return product_form.submit()

    def test_title_is_required(self):
        response = self.submit(title="")

        self.assertContains(response, "must have a title")
        self.assertEqual(Product.objects.count(), 0)

    def test_requires_a_category(self):
        response = self.submit(title="Nice T-Shirt")
        self.assertContains(response, "must have at least one category")
        self.assertEqual(Product.objects.count(), 0)

    def test_for_smoke(self):
        category = CategoryFactory()
        response = self.submit(title="testing", category=category)
        self.assertIsRedirect(response)
        self.assertEqual(Product.objects.count(), 1)

    def test_doesnt_allow_duplicate_upc(self):
        ProductFactory(parent=None, upc="12345")
        category = CategoryFactory()
        self.assertTrue(Product.objects.get(upc="12345"))

        response = self.submit(title="Nice T-Shirt", category=category, upc="12345")

        self.assertEqual(Product.objects.count(), 1)
        self.assertNotEqual(Product.objects.get(upc="12345").title, "Nice T-Shirt")
        self.assertContains(response, "Product with this UPC already exists.")


class TestCreateChildProduct(ProductWebTest):
    is_staff = True

    def setUp(self):
        super().setUp()
        self.pclass = ProductClassFactory(name="Books", slug="books")
        self.parent = ProductFactory(structure="parent", stockrecords=[])

    def test_categories_are_not_required(self):
        url = reverse(
            "dashboard:catalogue-product-create-child",
            kwargs={"parent_pk": self.parent.pk},
        )
        page = self.get(url)

        product_form = page.form
        product_form["title"] = expected_title = "Nice T-Shirt"
        product_form.submit()

        try:
            product = Product.objects.get(title=expected_title)
        except Product.DoesNotExist:
            self.fail("creating a child product did not work")

        self.assertEqual(product.parent, self.parent)


class TestProductUpdate(ProductWebTest):
    def test_product_update_form(self):
        self.product = factories.ProductFactory()
        url = reverse("dashboard:catalogue-product", kwargs={"pk": self.product.id})

        page = self.get(url)
        product_form = page.form
        product_form["title"] = expected_title = "Nice T-Shirt"
        page = product_form.submit()

        product = Product.objects.get(id=self.product.id)

        self.assertEqual(page.context["product"], self.product)
        self.assertEqual(product.title, expected_title)


class TestProductClass(ProductWebTest):
    def setUp(self):
        super().setUp()
        self.pclass = ProductClassFactory(name="T-Shirts", slug="tshirts")

        for attribute_type, __ in ProductAttribute.TYPE_CHOICES:
            values = {
                "type": attribute_type,
                "code": attribute_type,
                "product_class": self.pclass,
                "name": attribute_type,
            }
            if attribute_type == ProductAttribute.OPTION:
                option_group = factories.AttributeOptionGroupFactory()
                self.option = factories.AttributeOptionFactory(group=option_group)
                values["option_group"] = option_group
            elif attribute_type == ProductAttribute.MULTI_OPTION:
                option_group = factories.AttributeOptionGroupFactory()
                self.multi_option = factories.AttributeOptionFactory(group=option_group)
                values["option_group"] = option_group
            ProductAttributeFactory(**values)
        self.product = factories.ProductFactory(product_class=self.pclass)
        self.url = reverse(
            "dashboard:catalogue-product", kwargs={"pk": self.product.id}
        )

    def test_product_update_attribute_values(self):
        page = self.get(self.url)
        product_form = page.form
        # Send string field values due to an error
        # in the Webtest during multipart form encode.
        product_form["attr_text"] = "test1"
        product_form["attr_integer"] = "1"
        product_form["attr_float"] = "1.2"
        product_form["attr_boolean"] = "yes"
        product_form["attr_richtext"] = "longread"
        product_form["attr_date"] = "2016-10-12"

        file1 = Upload("file1.txt", b"test-1", "text/plain")
        image1 = Upload("image1.png", generate_test_image(), "image/png")
        product_form["attr_file"] = file1
        product_form["attr_image"] = image1
        product_form.submit()

        # Reloading model instance to re-initiate ProductAttributeContainer
        # with new attributes.
        self.product = Product.objects.get(pk=self.product.id)
        self.assertEqual(self.product.attr.text, "test1")
        self.assertEqual(self.product.attr.integer, 1)
        self.assertEqual(self.product.attr.float, 1.2)
        self.assertTrue(self.product.attr.boolean)
        self.assertEqual(self.product.attr.richtext, "longread")
        self.assertEqual(self.product.attr.date, datetime.date(2016, 10, 12))

        file1_path = media_file_path(self.product.attr.file.name)
        self.assertTrue(os.path.isfile(file1_path))
        with open(file1_path) as file1_file:
            self.assertEqual(file1_file.read(), "test-1")

        image1_path = media_file_path(self.product.attr.image.name)
        self.assertTrue(os.path.isfile(image1_path))
        with open(image1_path, "rb") as image1_file:
            self.assertEqual(image1_file.read(), image1.content)

        page = self.get(self.url)
        product_form = page.form
        product_form["attr_text"] = "test2"
        product_form["attr_integer"] = "2"
        product_form["attr_float"] = "5.2"
        product_form["attr_boolean"] = ""
        product_form["attr_richtext"] = "article"
        product_form["attr_date"] = "2016-10-10"
        file2 = Upload("file2.txt", b"test-2", "text/plain")
        image2 = Upload("image2.png", generate_test_image(), "image/png")
        product_form["attr_file"] = file2
        product_form["attr_image"] = image2
        product_form.submit()

        self.product = Product.objects.get(pk=self.product.id)
        self.assertEqual(self.product.attr.text, "test2")
        self.assertEqual(self.product.attr.integer, 2)
        self.assertEqual(self.product.attr.float, 5.2)
        self.assertFalse(self.product.attr.boolean)
        self.assertEqual(self.product.attr.richtext, "article")
        self.assertEqual(self.product.attr.date, datetime.date(2016, 10, 10))

        file2_path = media_file_path(self.product.attr.file.name)
        self.assertTrue(os.path.isfile(file2_path))
        with open(file2_path) as file2_file:
            self.assertEqual(file2_file.read(), "test-2")

        image2_path = media_file_path(self.product.attr.image.name)
        self.assertTrue(os.path.isfile(image2_path))
        with open(image2_path, "rb") as image2_file:
            self.assertEqual(image2_file.read(), image2.content)


class TestProductImages(ProductWebTest):
    def setUp(self):
        super().setUp()
        self.product = factories.ProductFactory()
        self.url = reverse(
            "dashboard:catalogue-product", kwargs={"pk": self.product.id}
        )

    def test_product_images_upload(self):
        page = self.get(self.url)
        product_form = page.form
        image1 = Upload("image1.png", generate_test_image(), "image/png")
        image2 = Upload("image2.png", generate_test_image(), "image/png")
        image3 = Upload("image3.png", generate_test_image(), "image/png")

        product_form["images-0-original"] = image1
        product_form["images-1-original"] = image2
        product_form.submit(name="action", value="continue").follow()
        self.product = Product.objects.get(pk=self.product.id)
        self.assertEqual(self.product.images.count(), 2)
        page = self.get(self.url)
        product_form = page.form
        product_form["images-2-original"] = image3
        product_form.submit()
        self.product = Product.objects.get(pk=self.product.id)
        self.assertEqual(self.product.images.count(), 3)
        images = self.product.images.all()

        self.assertEqual(images[0].display_order, 0)
        image1_path = media_file_path(images[0].original.name)
        self.assertTrue(os.path.isfile(image1_path))
        with open(image1_path, "rb") as image1_file:
            self.assertEqual(image1_file.read(), image1.content)

        self.assertEqual(images[1].display_order, 1)
        image2_path = media_file_path(images[1].original.name)
        self.assertTrue(os.path.isfile(image2_path))
        with open(image2_path, "rb") as image2_file:
            self.assertEqual(image2_file.read(), image2.content)

        self.assertEqual(images[2].display_order, 2)
        image3_path = media_file_path(images[2].original.name)
        self.assertTrue(os.path.isfile(image3_path))
        with open(image3_path, "rb") as image3_file:
            self.assertEqual(image3_file.read(), image3.content)

    def test_product_images_reordering(self):
        im1 = factories.ProductImageFactory(product=self.product, display_order=1)
        im2 = factories.ProductImageFactory(product=self.product, display_order=2)
        im3 = factories.ProductImageFactory(product=self.product, display_order=3)

        self.assertEqual(
            list(ProductImage.objects.all().order_by("display_order")), [im1, im2, im3]
        )

        page = self.get(self.url)
        product_form = page.form
        product_form["images-1-display_order"] = "3"  # 1 is im2
        product_form["images-2-display_order"] = "4"  # 2 is im3
        product_form["images-0-display_order"] = "5"  # 0 is im1
        product_form.submit()

        self.assertEqual(
            list(ProductImage.objects.all().order_by("display_order")), [im2, im3, im1]
        )


class TestCategoryDashboard(WebTestCase):
    def setUp(self):
        self.staff = UserFactory(is_staff=True)
        create_from_breadcrumbs("A > B > C")

    def test_redirects_to_main_dashboard_after_creating_top_level_category(self):
        a = Category.objects.get(name="A")
        category_add = self.app.get(
            reverse("dashboard:catalogue-category-create"), user=self.staff
        )
        form = category_add.form
        form["name"] = "Top-level category"
        form["_position"] = "right"
        form["_ref_node_id"] = a.id
        response = form.submit()
        self.assertRedirects(response, reverse("dashboard:catalogue-category-list"))

    def test_redirects_to_parent_list_after_creating_child_category(self):
        b = Category.objects.get(name="B")
        c = Category.objects.get(name="C")
        category_add = self.app.get(
            reverse("dashboard:catalogue-category-create"), user=self.staff
        )
        form = category_add.form
        form["name"] = "Child category"
        form["_position"] = "left"
        form["_ref_node_id"] = c.id
        response = form.submit()
        self.assertRedirects(
            response, reverse("dashboard:catalogue-category-detail-list", args=(b.pk,))
        )

    def test_handles_invalid_form_gracefully(self):
        dashboard_index = self.app.get(reverse("dashboard:index"), user=self.staff)
        category_index = dashboard_index.click("Categories")
        category_add = category_index.click("Create new category")
        response = category_add.form.submit()
        self.assertEqual(200, response.status_code)


class TestAttributeOptionGroupListView(ListViewMixin, WebTestCase):
    is_staff = True
    url_name = "dashboard:catalogue-attribute-option-group-list"

    def _create_object(self, idx):
        attribute_option_group_name = "Test Attribute Option Group #%d"
        AttributeOptionGroupFactory(name=attribute_option_group_name % idx)


class TestAttributeOptionGroupCreateView(PopUpObjectCreateMixin, WebTestCase):
    is_staff = True
    model = AttributeOptionGroup
    form = AttributeOptionGroupForm
    page_title = gettext("Add a new Attribute Option Group")
    url_name = "dashboard:catalogue-attribute-option-group-create"
    template_name = "eta/dashboard/catalogue/attribute_option_group_form.html"
    success_message = gettext("Attribute Option Group created successfully")
    success_url_name = "dashboard:catalogue-attribute-option-group-list"
    create_check_attr = "name"
    object_check_str = "Test Attribute Option"
    attribute_option_option = "Test Attribute Option Group"

    def setUp(self):
        super().setUp()
        AttributeOptionGroup.objects.all().delete()

    def _test_display_create_form_response(self):
        super()._test_display_create_form_response()
        response = self.response
        self.assertInContext(response, "attribute_option_formset")
        self.assertIsInstance(
            response.context["attribute_option_formset"], AttributeOptionFormSet
        )
        self.assertTrue(
            response.context["attribute_option_formset"].instance._state.adding
        )

    def _test_creation_of_objects(self):
        super()._test_creation_of_objects()
        # Test the creation of the attribute option
        self.assertEqual(1, AttributeOption.objects.all().count())
        attribute_option = AttributeOption.objects.first()
        self.assertEqual(attribute_option.group, self.obj)
        self.assertEqual(attribute_option.option, self.attribute_option_option)

    def _get_create_obj_response(self):
        form = self.get(self._get_url()).form
        form["name"] = self.object_check_str
        form["options-0-option"] = self.attribute_option_option
        return form.submit()


class TestAttributeOptionGroupUpdateView(PopUpObjectUpdateMixin, WebTestCase):
    is_staff = True
    model = AttributeOptionGroup
    form = AttributeOptionGroupForm
    page_title = None
    url_name = "dashboard:catalogue-attribute-option-group-update"
    template_name = "eta/dashboard/catalogue/attribute_option_group_form.html"
    success_message = gettext("Attribute Option Group updated successfully")
    success_url_name = "dashboard:catalogue-attribute-option-group-list"
    create_check_attr = "name"
    object_check_str = "Test Attribute Option"
    attribute_option_option = "Test Attribute Option Group"

    def _create_object_factory(self):
        obj = AttributeOptionGroupFactory()
        AttributeOptionFactory(group=obj)
        return obj

    def _get_page_title(self):
        return gettext("Update Attribute Option Group '%s'") % self.obj.name

    def _get_update_obj_response(self):
        form = self.get(self._get_url()).form
        form["name"] = self.object_check_str
        form["options-0-option"] = self.attribute_option_option
        return form.submit()

    def _test_display_update_form_response(self):
        super()._test_display_update_form_response()
        response = self.response

        self.assertInContext(response, "attribute_option_formset")
        self.assertIsInstance(
            response.context["attribute_option_formset"], AttributeOptionFormSet
        )
        self.assertEqual(
            response.context["attribute_option_formset"].initial_forms[0].instance,
            self.obj.options.first(),
        )

    # def _test_update_of_objects(self):
    #     super()._test_update_of_objects()
    #     # Test the update of the attribute option
    #     self.assertEqual(
    #         self.obj.options.first().option,
    #         self.attribute_option_option
    #     )


class TestAttributeOptionGroupDeleteView(PopUpObjectDeleteMixin, WebTestCase):
    is_staff = True
    model = AttributeOptionGroup
    page_title = None
    url_name = "dashboard:catalogue-attribute-option-group-delete"
    template_name = "eta/dashboard/catalogue/attribute_option_group_delete.html"
    success_message = gettext("Attribute Option Group deleted successfully")
    success_url_name = "dashboard:catalogue-attribute-option-group-list"
    delete_dissalowed_possible = True

    def _create_object_factory(self):
        obj = AttributeOptionGroupFactory()
        AttributeOptionFactory(group=obj)
        return obj

    def _get_page_title(self):
        if getattr(self, "is_disallowed_test", None):
            return gettext("Unable to delete '%s'") % self.obj.name
        return gettext("Delete Attribute Option Group '%s'") % self.obj.name

    def _get_delete_obj_response(self):
        form = self.get(self._get_url()).form
        return form.submit()

    def _create_dissalowed_object_factory(self):
        ProductAttributeFactory(
            type="multi_option", name="Sizes", code="sizes", option_group=self.obj
        )

    # def _test_deletion_of_objects(self):
    #     # Test the deletion of the attribute option
    #     attribute_option_exists = AttributeOption.objects.exists()
    #     self.assertFalse(attribute_option_exists)

    def _test_display_delete_disallowed_response(self):
        super()._test_display_delete_disallowed_response()
        response = self.response
        messages = list(response.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].level, ERROR)
        self.assertEqual(
            messages[0].message,
            gettext(
                "1 product attributes are still assigned to this attribute option group"
            ),
        )


class TestOptionListView(ListViewMixin, WebTestCase):
    is_staff = True
    url_name = "dashboard:catalogue-option-list"

    def _create_object(self, idx):
        option_name = "Test Option #%d"
        name = option_name % idx
        OptionFactory(name=name, code=slugify(name))


class TestOptionCreateView(PopUpObjectCreateMixin, WebTestCase):
    is_staff = True
    model = Option
    form = OptionForm
    page_title = gettext("Add a new Option")
    url_name = "dashboard:catalogue-option-create"
    template_name = "eta/dashboard/catalogue/option_form.html"
    success_message = gettext("Option created successfully")
    success_url_name = "dashboard:catalogue-option-list"
    create_check_attr = "name"
    object_check_str = "Test Option"

    def _get_create_obj_response(self):
        form = self.get(self._get_url()).form
        form["name"] = self.object_check_str
        return form.submit()


class TestOptionUpdateView(PopUpObjectUpdateMixin, WebTestCase):
    is_staff = True
    model = Option
    form = OptionForm
    page_title = None
    url_name = "dashboard:catalogue-option-update"
    template_name = "eta/dashboard/catalogue/option_form.html"
    success_message = gettext("Option updated successfully")
    success_url_name = "dashboard:catalogue-option-list"
    create_check_attr = "name"
    object_check_str = "Test Option"

    def _create_object_factory(self):
        return OptionFactory()

    def _get_page_title(self):
        return gettext("Update Option '%s'") % self.obj.name

    def _get_update_obj_response(self):
        form = self.get(self._get_url()).form
        form["name"] = self.object_check_str
        return form.submit()


class TestOptionDeleteView(PopUpObjectDeleteMixin, WebTestCase):
    is_staff = True
    model = Option
    page_title = None
    url_name = "dashboard:catalogue-option-delete"
    template_name = "eta/dashboard/catalogue/option_delete.html"
    success_message = gettext("Option deleted successfully")
    success_url_name = "dashboard:catalogue-option-list"
    delete_dissalowed_possible = True

    def _create_object_factory(self):
        return OptionFactory()

    def _get_page_title(self):
        if getattr(self, "is_disallowed_test", None):
            return gettext("Unable to delete '%s'") % self.obj.name
        return gettext("Delete Option '%s'") % self.obj.name

    def _get_delete_obj_response(self):
        form = self.get(self._get_url()).form
        return form.submit()

    def _create_dissalowed_object_factory(self):
        product_class = ProductClassFactory()
        product = create_product(product_class=product_class)
        product_class.options.add(self.obj)
        product.product_options.add(self.obj)

    def _test_display_delete_disallowed_response(self):
        super()._test_display_delete_disallowed_response()
        response = self.response
        messages = list(response.context["messages"])
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0].level, ERROR)
        self.assertEqual(messages[1].level, ERROR)
        self.assertEqual(
            messages[0].message, "1 products are still assigned to this option"
        )
        self.assertEqual(
            messages[1].message, "1 product classes are still assigned to this option"
        )


class TestCatalogueViews(WebTestCase):
    is_staff = True

    def test_exist(self):
        urls = [
            reverse("dashboard:catalogue-product-list"),
            reverse("dashboard:catalogue-category-list"),
            reverse("dashboard:stock-alert-list"),
            reverse("dashboard:catalogue-product-lookup"),
        ]
        for url in urls:
            self.assertIsOk(self.get(url))

    def test_upc_filter(self):
        product1 = create_product(upc="123")
        product2 = create_product(upc="12")
        product3 = create_product(upc="1")

        # no value for upc, all results
        page = self.get("%s?upc=" % reverse("dashboard:catalogue-product-list"))
        products_on_page = [
            row.record for row in page.context["products"].page.object_list
        ]
        self.assertIn(product1, products_on_page)
        self.assertIn(product2, products_on_page)
        self.assertIn(product3, products_on_page)

        # filter by upc, one result
        page = self.get("%s?upc=123" % reverse("dashboard:catalogue-product-list"))
        products_on_page = [
            row.record for row in page.context["products"].page.object_list
        ]
        self.assertIn(product1, products_on_page)
        self.assertNotIn(product2, products_on_page)
        self.assertNotIn(product3, products_on_page)

        # exact match, one result, no multiple
        page = self.get("%s?upc=12" % reverse("dashboard:catalogue-product-list"))
        products_on_page = [
            row.record for row in page.context["products"].page.object_list
        ]
        self.assertNotIn(product1, products_on_page)
        self.assertIn(product2, products_on_page)
        self.assertNotIn(product3, products_on_page)

        # part of the upc, one result
        page = self.get("%s?upc=3" % reverse("dashboard:catalogue-product-list"))
        products_on_page = [
            row.record for row in page.context["products"].page.object_list
        ]
        self.assertIn(product1, products_on_page)
        self.assertNotIn(product2, products_on_page)
        self.assertNotIn(product3, products_on_page)

        # part of the upc, two results
        page = self.get("%s?upc=2" % reverse("dashboard:catalogue-product-list"))
        products_on_page = [
            row.record for row in page.context["products"].page.object_list
        ]
        self.assertIn(product1, products_on_page)
        self.assertIn(product2, products_on_page)
        self.assertNotIn(product3, products_on_page)

    def test_is_public(self):
        # Can I still find non-public products in dashboard?
        product = create_product(is_public=False, upc="kleine-bats")
        page = self.get(
            "%s?upc=%s" % (reverse("dashboard:catalogue-product-list"), product.upc)
        )
        products_on_page = [
            row.record for row in page.context["products"].page.object_list
        ]
        self.assertEqual(products_on_page, [product])


class TestAStaffUser(WebTestCase):
    is_staff = True

    def setUp(self):
        super().setUp()
        self.partner = PartnerFactory()

    def test_can_create_a_product_without_stockrecord(self):
        category = CategoryFactory()
        product_class = ProductClass.objects.create(name="Book")
        page = self.get(
            reverse("dashboard:catalogue-product-create", args=(product_class.slug,))
        )
        form = page.form
        form["upc"] = "123456"
        form["title"] = "new product"
        form["productcategory_set-0-category"] = category.id
        form.submit()

        self.assertEqual(Product.objects.count(), 1)

    def test_can_create_and_continue_editing_a_product(self):
        category = CategoryFactory()
        product_class = ProductClass.objects.create(name="Book")
        page = self.get(
            reverse("dashboard:catalogue-product-create", args=(product_class.slug,))
        )
        form = page.form
        form["upc"] = "123456"
        form["title"] = "new product"
        form["productcategory_set-0-category"] = category.id
        form["stockrecords-0-partner"] = self.partner.id
        form["stockrecords-0-partner_sku"] = "14"
        form["stockrecords-0-num_in_stock"] = "555"
        form["stockrecords-0-price"] = "13.99"
        page = form.submit(name="action", value="continue")

        self.assertEqual(Product.objects.count(), 1)
        product = Product.objects.all()[0]
        self.assertEqual(product.stockrecords.all()[0].partner, self.partner)
        self.assertRedirects(
            page, reverse("dashboard:catalogue-product", kwargs={"pk": product.id})
        )

    def test_can_update_a_product_without_stockrecord(self):
        new_title = "foobar"
        category = CategoryFactory()
        product = ProductFactory(stockrecords=[])

        page = self.get(
            reverse("dashboard:catalogue-product", kwargs={"pk": product.id})
        )
        form = page.forms[0]
        form["productcategory_set-0-category"] = category.id
        self.assertNotEqual(form["title"].value, new_title)
        form["title"] = new_title
        form.submit()

        try:
            product = Product.objects.get(pk=product.pk)
        except Product.DoesNotExist:
            pass
        else:
            self.assertTrue(product.title == new_title)
            if product.has_stockrecords:
                self.fail("Product has stock records but should not")

    def test_can_create_product_with_required_attributes(self):
        category = CategoryFactory()
        attribute = ProductAttributeFactory(required=True)
        product_class = attribute.product_class
        page = self.get(
            reverse("dashboard:catalogue-product-create", args=(product_class.slug,))
        )
        form = page.form
        form["upc"] = "123456"
        form["title"] = "new product"
        form["attr_weight"] = "5"
        form["productcategory_set-0-category"] = category.id
        form.submit()

        self.assertEqual(Product.objects.count(), 1)

    def test_can_delete_a_standalone_product(self):
        product = create_product(partner_users=[self.user])
        category = Category.add_root(name="Test Category")
        ProductCategory.objects.create(category=category, product=product)

        page = self.get(
            reverse("dashboard:catalogue-product-delete", args=(product.id,))
        ).form.submit()

        self.assertRedirects(page, reverse("dashboard:catalogue-product-list"))
        self.assertEqual(Product.objects.count(), 0)
        self.assertEqual(StockRecord.objects.count(), 0)
        self.assertEqual(Category.objects.count(), 1)
        self.assertEqual(ProductCategory.objects.count(), 0)

    def test_can_delete_a_parent_product(self):
        parent_product = create_product(structure="parent")
        create_product(parent=parent_product)

        url = reverse("dashboard:catalogue-product-delete", args=(parent_product.id,))
        page = self.get(url).form.submit()

        self.assertRedirects(page, reverse("dashboard:catalogue-product-list"))
        self.assertEqual(Product.objects.count(), 0)

    def test_can_delete_a_child_product(self):
        parent_product = create_product(structure="parent")
        child_product = create_product(parent=parent_product)

        url = reverse("dashboard:catalogue-product-delete", args=(child_product.id,))
        page = self.get(url).form.submit()

        expected_url = reverse(
            "dashboard:catalogue-product", kwargs={"pk": parent_product.pk}
        )
        self.assertRedirects(page, expected_url)
        self.assertEqual(Product.objects.count(), 1)

    def test_can_list_her_products(self):
        product1 = create_product(
            partner_users=[
                self.user,
            ]
        )
        product2 = create_product(partner_name="sneaky", partner_users=[])
        page = self.get(reverse("dashboard:catalogue-product-list"))
        products_on_page = [
            row.record for row in page.context["products"].page.object_list
        ]
        self.assertIn(product1, products_on_page)
        self.assertIn(product2, products_on_page)

    def test_can_create_a_child_product(self):
        parent_product = create_product(structure="parent")
        url = reverse(
            "dashboard:catalogue-product-create-child",
            kwargs={"parent_pk": parent_product.pk},
        )
        form = self.get(url).form
        form.submit()

        self.assertEqual(Product.objects.count(), 2)

    def test_cant_create_child_product_for_invalid_parents(self):
        # Creates a product with stockrecords.
        invalid_parent = create_product(partner_users=[self.user])
        self.assertFalse(invalid_parent.can_be_parent())
        url = reverse(
            "dashboard:catalogue-product-create-child",
            kwargs={"parent_pk": invalid_parent.pk},
        )
        self.assertRedirects(self.get(url), reverse("dashboard:catalogue-product-list"))


class TestANonStaffUser(TestAStaffUser):
    is_staff = False
    is_anonymous = False
    permissions = [
        "partner.dashboard_access",
    ]

    def setUp(self):
        super().setUp()
        add_permissions(self.user, self.permissions)
        self.partner.users.add(self.user)

    def test_can_list_her_products(self):
        product1 = create_product(partner_name="A", partner_users=[self.user])
        product2 = create_product(partner_name="B", partner_users=[])
        page = self.get(reverse("dashboard:catalogue-product-list"))
        products_on_page = [
            row.record for row in page.context["products"].page.object_list
        ]
        self.assertIn(product1, products_on_page)
        self.assertNotIn(product2, products_on_page)

    def test_cant_create_a_child_product(self):
        parent_product = create_product(structure="parent")
        url = reverse(
            "dashboard:catalogue-product-create-child",
            kwargs={"parent_pk": parent_product.pk},
        )
        response = self.get(url, status="*")
        self.assertEqual(http_client.FORBIDDEN, response.status_code)

    # Tests below can't work because they don't create a stockrecord

    def test_can_create_a_product_without_stockrecord(self):
        pass

    def test_can_update_a_product_without_stockrecord(self):
        pass

    def test_can_create_product_with_required_attributes(self):
        pass

    # Tests below can't work because child products aren't supported with the
    # permission-based dashboard

    def test_can_delete_a_child_product(self):
        pass

    def test_can_delete_a_parent_product(self):
        pass

    def test_can_create_a_child_product(self):
        pass

    def test_cant_create_child_product_for_invalid_parents(self):
        pass


class ProductListViewTestCase(TestCase):
    def test_searching_child_product_by_title_returns_parent_product(self):
        self.parent_product = create_product(
            structure=Product.PARENT, title="Parent", upc="PARENT_UPC"
        )
        create_product(
            structure=Product.CHILD,
            title="Child",
            parent=self.parent_product,
            upc="CHILD_UPC",
        )
        view = ProductListView(request=RequestFactory().get("/?title=Child"))
        assert list(view.get_queryset()) == [self.parent_product]

    def test_searching_child_product_by_title_returns_1_parent_product_if_title_is_partially_shared(
        self,
    ):
        self.parent_product = create_product(
            structure=Product.PARENT, title="Shared", upc="PARENT_UPC"
        )
        create_product(
            structure=Product.CHILD,
            title="Shared",
            parent=self.parent_product,
            upc="CHILD_UPC",
        )
        create_product(
            structure=Product.CHILD,
            title="Shared1",
            parent=self.parent_product,
            upc="CHILD_UPC1",
        )
        view = ProductListView(request=RequestFactory().get("/?title=Shared"))
        assert list(view.get_queryset()) == [self.parent_product]

    def test_searching_child_product_by_upc_returns_parent_product(self):
        self.parent_product = create_product(
            structure=Product.PARENT, title="Parent", upc="PARENT_UPC"
        )
        create_product(
            structure=Product.CHILD,
            title="Child",
            parent=self.parent_product,
            upc="CHILD_UPC",
        )
        view = ProductListView(request=RequestFactory().get("/?upc=CHILD_UPC"))
        assert list(view.get_queryset()) == [self.parent_product]

    def test_searching_child_product_by_upc_returns_1_parent_product_if_upc_is_partially_shared(
        self,
    ):
        self.parent_product = create_product(
            structure=Product.PARENT, title="Parent", upc="PARENT_UPC"
        )
        create_product(
            structure=Product.CHILD,
            title="Child",
            parent=self.parent_product,
            upc="CHILD_UPC",
        )
        create_product(
            structure=Product.CHILD,
            title="Child1",
            parent=self.parent_product,
            upc="CHILD_UPC1",
        )
        view = ProductListView(request=RequestFactory().get("/?upc=CHILD"))
        assert list(view.get_queryset()) == [self.parent_product]
