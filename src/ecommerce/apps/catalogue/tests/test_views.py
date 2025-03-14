from http import client as http_client

from django.conf import settings
from django.urls import reverse
from django.utils.translation import gettext

from ecommerce.apps.catalogue.models import Category
from ecommerce.test.factories import create_product
from ecommerce.test.testcases import WebTestCase


class TestProductDetailView(WebTestCase):
    def test_enforces_canonical_url(self):
        p = create_product()
        kwargs = {"product_slug": "1_wrong-but-valid-slug_1", "pk": p.id}
        wrong_url = reverse("catalogue:detail", kwargs=kwargs)

        response = self.app.get(wrong_url)
        self.assertEqual(http_client.MOVED_PERMANENTLY, response.status_code)
        self.assertTrue(p.get_absolute_url() in response.location)

    def test_is_public_on(self):
        product = create_product(upc="kleine-bats", is_public=True)

        kwargs = {"product_slug": product.slug, "pk": product.id}
        url = reverse("catalogue:detail", kwargs=kwargs)
        response = self.app.get(url)

        self.assertEqual(response.status_code, http_client.OK)

    def test_is_public_off(self):
        product = create_product(upc="kleine-bats", is_public=False)

        kwargs = {"product_slug": product.slug, "pk": product.id}
        url = reverse("catalogue:detail", kwargs=kwargs)
        response = self.app.get(url, expect_errors=True)

        self.assertEqual(response.status_code, http_client.NOT_FOUND)


class TestProductListView(WebTestCase):
    def setUp(self):
        super().setUp()

    def test_shows_add_to_basket_button_for_available_product(self):
        # sourcery skip: class-extract-method
        product = create_product(num_in_stock=1)
        page = self.app.get(reverse("catalogue:index"))
        self.assertContains(page, product.title)
        self.assertContains(page, gettext("Add to basket"))

    def test_shows_not_available_for_out_of_stock_product(self):
        product = create_product(num_in_stock=0)

        page = self.app.get(reverse("catalogue:index"))

        self.assertContains(page, product.title)
        self.assertContains(page, "Unavailable")

    def test_shows_pagination_navigation_for_multiple_pages(self):
        per_page = settings.OSCAR_PRODUCTS_PER_PAGE
        title = "Product #%d"
        for idx in range(int(1.5 * per_page)):
            create_product(title=title % idx)

        page = self.app.get(reverse("catalogue:index"))

        self.assertContains(page, "Page 1 of 2")

    def test_is_public_on(self):
        product = create_product(upc="grote-bats", is_public=True)
        page = self.app.get(reverse("catalogue:index"))
        products_on_page = list(page.context["products"].all())
        self.assertEqual(products_on_page, [product])

    def test_is_public_off(self):
        create_product(upc="kleine-bats", is_public=False)
        page = self.app.get(reverse("catalogue:index"))
        products_on_page = list(page.context["products"].all())
        self.assertEqual(products_on_page, [])

    def test_invalid_page_redirects_to_index(self):
        create_product()
        products_list_url = reverse("catalogue:index")
        response = self.app.get(f"{products_list_url}?page=200")
        self.assertEqual(response.status_code, 302)
        self.assertRedirectsTo(response, "catalogue:index")


class TestProductCategoryView(WebTestCase):
    def setUp(self):
        self.category = Category.add_root(name="Products")

    def test_browsing_works(self):
        correct_url = self.category.get_absolute_url()
        response = self.app.get(correct_url)
        self.assertEqual(http_client.OK, response.status_code)

    def test_enforces_canonical_url(self):
        kwargs = {"category_slug": "1_wrong-but-valid-slug_1", "pk": self.category.pk}
        wrong_url = reverse("catalogue:category", kwargs=kwargs)

        response = self.app.get(wrong_url)
        self.assertEqual(http_client.MOVED_PERMANENTLY, response.status_code)
        self.assertTrue(self.category.get_absolute_url() in response.location)

    def test_is_public_off(self):
        category = Category.add_root(name="Foobars", is_public=False)
        response = self.app.get(category.get_absolute_url(), expect_errors=True)
        self.assertEqual(http_client.NOT_FOUND, response.status_code)
        return category

    def test_is_public_on(self):
        category = Category.add_root(name="Barfoos", is_public=True)
        response = self.app.get(category.get_absolute_url())
        self.assertEqual(http_client.OK, response.status_code)
        return category

    def test_browsable_contains_public_child(self):
        "If the parent is public the child should be in browsable if it is public as well"
        cat = self.test_is_public_on()
        child = cat.add_child(name="Koe", is_public=True)
        self.assertTrue(child in Category.objects.all().browsable())

        child.is_public = False
        child.save()
        self.assertTrue(child not in Category.objects.all().browsable())

    def test_browsable_hides_public_child(self):
        "If the parent is not public the child should not be in browsable evn if it is public"
        cat = self.test_is_public_off()
        child = cat.add_child(name="Koe", is_public=True)
        self.assertTrue(child not in Category.objects.all().browsable())

    def test_is_public_child(self):
        cat = self.test_is_public_off()
        child = cat.add_child(name="Koe", is_public=True)
        response = self.app.get(child.get_absolute_url())
        self.assertEqual(http_client.OK, response.status_code)

        child.is_public = False
        child.save()
        response = self.app.get(child.get_absolute_url(), expect_errors=True)
        self.assertEqual(http_client.NOT_FOUND, response.status_code)
