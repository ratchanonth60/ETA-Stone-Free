import contextlib
from decimal import Decimal as D

from oscar.core.loading import get_class

from ecommerce.test import factories

Default = get_class('partner.strategy', 'Default')


def add_product(basket, price=None, quantity=1, product=None):
    """
    Helper to add a product to the basket.
    """
    has_strategy = False
    with contextlib.suppress(RuntimeError):
        has_strategy = hasattr(basket, 'strategy')
    if not has_strategy:
        basket.strategy = Default()
    if price is None:
        price = D('1')
    if product and product.has_stockrecords:
        record = product.stockrecords.first()
    else:
        record = factories.create_stockrecord(
            product=product, price=price,
            num_in_stock=quantity + 1)
    basket.add_product(record.product, quantity)


def add_products(basket, args):
    """
    Helper to add a series of products to the passed basket
    """
    for price, quantity in args:
        add_product(basket, price, quantity)
