from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from ecommerce.test.factories import (
    CategoryFactory,
    ProductClassFactory,
    ProductFactory,
    UserFactory,
)
from ecommerce.test.testcases import APITestCase


class ProductViewSetTestCase(APITestCase):
    def setUp(self) -> None:
        super().setUp()
        self.user = UserFactory()  # ใช้ UserFactory ในการสร้าง user
        self.client = APIClient()
        self.client.force_authenticate(
            user=self.user
        )  # Authenticate the user for this session

    def test_list_products(self):
        ProductFactory.create_batch(5)
        url = reverse("product-list", kwargs={"version": "v1"})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 5)

    def test_retrieve_product(self):
        product = ProductFactory()
        url = reverse("product-detail", kwargs={"version": "v1", "pk": product.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], product.title)

    def test_create_product(self):
        product_class = ProductClassFactory()

        data = {
            "title": "New Product",
            "product_class": product_class.id,
            "structure": "standalone",
            "is_discountable": True,
            "is_public": True,
            "upc": "001",
            "slug": "test",
            "description": "test",
            "meta_title": "test",
            "meta_description": "test",
            "rating": 1,
            "date_created": "2023-08-27T15:42:03.293397",
            "date_updated": "2023-08-27T15:42:03.293421",
            "attributes": [],
            "product_options": [],
            "recommended_products": [],
            "categories": [],
        }
        url = reverse("product-list", kwargs={"version": "v1"})
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], "New Product")


class CategoryViewSetTestCase(APITestCase):
    def test_list_categories(self):
        # Use the CategoryFactory to create a sample category
        category = CategoryFactory()
        url = reverse("category-detail", kwargs={"version": "v1", "pk": category.id})
        # Get the list of categories from API
        response = self.client.get(url)

        # Check if the status code is 200 OK
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], category.name)
        self.assertEqual(response.data["path"], category.path)
