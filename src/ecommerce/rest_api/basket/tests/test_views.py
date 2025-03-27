from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from ecommerce.test.factories import BasketFactory, UserFactory
from ecommerce.test.testcases import APITestCase


class BasketViewSetTestCase(APITestCase):
    def setUp(self) -> None:
        super().setUp()
        self.user = UserFactory()
        self.client = APIClient()
        self.client.force_authenticate(
            user=self.user
        )  # Authenticate the user for this session
        self.basket = BasketFactory()

    def test_get_basket(self):
        url = reverse("basket-detail", kwargs={"version": "v1", "pk": self.basket.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], self.basket.status)
