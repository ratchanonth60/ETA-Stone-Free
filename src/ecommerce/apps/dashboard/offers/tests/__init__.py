import pytest
from oscar.core.loading import get_model

from ecommerce.test.factories.catalogue import ProductFactory
from ecommerce.test.factories.offer import ConditionalOfferFactory, RangeFactory

Range = get_model('offer', 'Range')


@pytest.fixture
def many_ranges():
    for _ in range(30):
        RangeFactory()
    return Range.objects.all()


@pytest.fixture
def many_offers():
    for i in range(30):
        ConditionalOfferFactory(
            name='Test offer %d' % i
        )


@pytest.fixture
def range_with_products():
    productrange = RangeFactory()
    for _ in range(30):
        product = ProductFactory()
        productrange.add_product(product)
    return productrange
