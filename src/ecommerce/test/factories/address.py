import random
import string

import exrex
import factory
from factory.django import DjangoModelFactory
from oscar.core.loading import get_model

__all__ = [
    "CountryFactory",
    "UserAddressFactory",
    "generate_postcode",
]


class CountryFactory(DjangoModelFactory):
    # Generates two random uppercase letters
    iso_3166_1_a2 = factory.LazyFunction(
        lambda: "".join(random.choices(string.ascii_uppercase, k=2))
    )
    # Generates three random uppercase letters
    iso_3166_1_a3 = factory.LazyFunction(
        lambda: "".join(random.choices(string.ascii_uppercase, k=3))
    )
    # Generates up to three digits, left-padded with zeros if less than 100
    iso_3166_1_numeric = factory.LazyFunction(
        lambda: "{:03}".format(random.randint(1, 999))
    )
    printable_name = factory.Faker("country")
    name = factory.Faker("country")
    display_order = factory.Sequence(lambda n: n)
    is_shipping_country = factory.Faker("pybool")

    class Meta:
        model = get_model("address", "Country")
        django_get_or_create = ("iso_3166_1_a2",)


class UserAddressFactory(DjangoModelFactory):
    title = factory.Iterator(["Dr", "Mr", "Ms"])
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    line1 = factory.Faker("street_address")
    line4 = factory.Faker("city")
    postcode = factory.LazyAttribute(
        lambda o: generate_postcode(o.country.iso_3166_1_a2)
    )
    phone_number = factory.Faker("phone_number")
    country = factory.SubFactory(CountryFactory)
    user = factory.SubFactory("ecommerce.test.factories.UserFactory")

    class Meta:
        model = get_model("address", "UserAddress")


def generate_postcode(country_iso_code):
    # Access POSTCODES_REGEX from the UserAddress model
    UserAddress = get_model("address", "UserAddress")
    if regex_pattern := getattr(UserAddress, "POSTCODES_REGEX", {}).get(
        country_iso_code
    ):
        return exrex.getone(regex_pattern)
    else:
        # Return a default postcode or raise an error if a pattern for the country is not defined
        return "00000"  # Example default postcode
