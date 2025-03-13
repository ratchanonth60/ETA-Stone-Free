from decimal import Decimal as D
from unittest import mock

import pytest

from ecommerce.apps.offer import models
from ecommerce.test import factories
from ecommerce.test.basket import add_product


@pytest.fixture
def products_some():
    return [factories.create_product(), factories.create_product()]


@pytest.fixture()
def range():
    return factories.RangeFactory()


@pytest.fixture
def range_all():
    return factories.RangeFactory(
        name="All products range", includes_all_products=True
    )


@pytest.fixture
def range_some(products_some):
    return factories.RangeFactory(
        name="Some products", products=products_some
    )


@pytest.fixture
def count_condition(range_all):
    return models.CountCondition(range=range_all, type="Count", value=2)


@pytest.fixture
def value_condition(range_all):
    return models.ValueCondition(range=range_all, type="Value", value=D("10.00"))


@pytest.fixture
def coverage_condition(range_some):
    return models.CoverageCondition(range=range_some, type="Coverage", value=2)


@pytest.fixture
def empty_basket():
    return factories.create_basket(empty=True)


@pytest.fixture
def partial_basket(empty_basket):
    basket = empty_basket
    add_product(basket)
    return basket


@pytest.fixture
def mock_offer():
    return mock.Mock()
