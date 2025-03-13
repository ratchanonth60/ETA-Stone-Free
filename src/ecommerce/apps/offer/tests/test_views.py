from oscar.apps.offer.views import RangeDetailView

from ecommerce.test.factories import create_product
from ecommerce.test.factories.offer import ConditionalOfferFactory
from ecommerce.test.testcases import TestCase, WebTestCase


class TestTheOfferListPage(WebTestCase):

    def test_exists(self):
        response = self.app.get('/offers/')
        self.assertEqual(200, response.status_code)


class TestOffer(TestCase):

    def setUp(self):
        self.offer = ConditionalOfferFactory()
        self.non_public_product = create_product(is_public=False)
        self.offer.condition.range.add_product(self.non_public_product)

    def test_non_public_product_not_in_offer(self):
        self.assertFalse(self.non_public_product in self.offer.products())

    def test_non_public_product_not_in_range_detail_view(self):
        view = RangeDetailView()
        view.range = self.offer.condition.range
        self.assertFalse(self.non_public_product in view.get_queryset())
