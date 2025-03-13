import random
from datetime import date, timedelta

import factory
from factory.django import DjangoModelFactory
from oscar.core.loading import get_model

from .customer import UserFactory

__all__ = [
    "SourceTypeFactory",
    "SourceFactory",
    "TransactionFactory",
    "BankcardFactory",
]


class SourceTypeFactory(DjangoModelFactory):
    name = "Creditcard"
    code = "creditcard"

    class Meta:
        model = get_model("payment", "SourceType")


class SourceFactory(DjangoModelFactory):
    order = factory.SubFactory("ecommerce.test.factories.OrderFactory")
    source_type = factory.SubFactory(SourceTypeFactory)

    class Meta:
        model = get_model("payment", "Source")


class TransactionFactory(DjangoModelFactory):
    amount = factory.LazyAttribute(lambda obj: obj.source.order.total_incl_tax)
    reference = factory.LazyAttribute(lambda obj: obj.source.order.number)
    source = factory.SubFactory(SourceFactory)
    status = "authorised"

    class Meta:
        model = get_model("payment", "Transaction")


# class BankcardFactory(DjangoModelFactory):
#     class Meta:
#         model = get_model('payment', 'Bankcard')

#     user = factory.SubFactory(UserFactory)
#     card_type = factory.Iterator(["Visa", "MasterCard", "Amex"])
#     name = factory.Faker('name')
#     # Here we're just using Mastercard as an example. You can extend to other types.
#     number = factory.Faker('credit_card_number', card_type='mastercard')
#     expiry_date = factory.LazyFunction(lambda: date.today() + timedelta(days=365))  # Card expiry 1 year from now
#     partner_reference = factory.Faker('uuid4')
#     ccv = factory.Faker('credit_card_security_code', card_type='mastercard')


class BankcardFactory(DjangoModelFactory):
    class Meta:
        model = get_model("payment", "Bankcard")

    user = factory.SubFactory(UserFactory)
    stripe_card_id = factory.Sequence(lambda n: "stripe_card_%d" % n)
    stripe_customer_id = factory.Sequence(lambda n: "stripe_cust_%d" % n)
    card_type = factory.Iterator(["Visa", "MasterCard", "Amex"])
    last_4_digits = factory.LazyFunction(
        lambda: "{:04d}".format(random.randint(0, 9999))
    )
    expiry_date = factory.LazyFunction(
        lambda: date.today() + timedelta(days=365)
    )  # Card expiry 1 year from now
