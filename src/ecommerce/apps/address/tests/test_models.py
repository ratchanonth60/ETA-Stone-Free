# -*- coding: utf-8 -*-
import pytest
from django.core import exceptions
from oscar.core.compat import get_user_model

from ecommerce.apps.address import models
from ecommerce.apps.order.models import ShippingAddress
from ecommerce.test import factories
from ecommerce.test.testcases import TestCase

User = get_user_model()


class TestUserAddress(TestCase):
    def setUp(self):
        self.country = factories.CountryFactory.build()
        self.user = factories.UserFactory()

    def test_uses_title_firstname_and_lastname_in_salutation(self):
        a = factories.UserAddressFactory.build(
            country=self.country,
            title="Dr",
            first_name="Barry",
            last_name="Barrington",
            user=self.user,
        )
        self.assertEqual("Dr Barry Barrington", a.salutation)

    def test_strips_whitespace_from_salutation(self):
        a = factories.UserAddressFactory.build(
            title="",
            first_name="",
            last_name="Barrington",
            country=self.country,
            user=self.user,
        )
        self.assertEqual("Barrington", a.salutation)

    def test_has_name_property(self):
        a = factories.UserAddressFactory.build(
            country=self.country,
            first_name="Barry",
            last_name="Barrington",
            user=self.user,
        )
        self.assertEqual("Barry Barrington", a.name)

    def test_has_summary_property(self):
        c = factories.CountryFactory(name="")
        a = factories.UserAddressFactory(
            country=c,
            title="Dr",
            first_name="Barry",
            last_name="Barrington",
            line1="1 King Road",
            line4="London",
            postcode="SW1 9RE",
        )
        self.assertEqual(
            f"Dr Barry Barrington, 1 King Road, London, SW1 9RE, {c.printable_name}",
            a.summary,
        )
        return a.summary

    def test_summary_includes_country(self):
        c = factories.CountryFactory.build(name="UNITED KINGDOM")
        a = factories.UserAddressFactory.build(
            country=c,
            title="Dr",
            first_name="Barry",
            last_name="Barrington",
            line1="1 King Road",
            line4="London",
            postcode="SW1 9RE",
            user=self.user,
        )
        self.assertEqual(
            f"Dr Barry Barrington, 1 King Road, London, SW1 9RE, {c.printable_name}",
            a.summary,
        )

    # def test_hash_value(self):
    #     a = factories.UserAddressFactory.build(country=self.country, user=self.user)
    #     self.assertEqual(a.generate_hash(), 2465238006)

    def test_can_be_hashed_including_non_ascii(self):
        a = factories.UserAddressFactory.build(
            first_name="\u0141ukasz Smith",
            last_name="Smith",
            line1="75 Smith Road",
            postcode="n4 8ty",
            country=self.country,
            user=self.user,
        )
        hash = a.generate_hash()
        self.assertTrue(hash is not None)

    def test_strips_whitespace_in_name_property(self):
        a = factories.UserAddressFactory.build(
            first_name="", last_name="Barrington", country=self.country, user=self.user
        )
        self.assertEqual("Barrington", a.name)

    def test_uses_city_as_an_alias_of_line4(self):
        a = factories.UserAddressFactory.build(
            line4="London", country=self.country, user=self.user
        )
        self.assertEqual("London", a.city)

    def test_converts_postcode_to_uppercase_when_cleaning(self):
        address = factories.UserAddressFactory.build(country=self.country, user=self.user)
        address.clean()

        self.assertIsNotNone(address.postcode)

    def test_strips_whitespace_when_cleaning(self):
        a = factories.UserAddressFactory.build(
            line1="  75 Smith Road  ",
            country=self.country,
            user=self.user,
        )
        a.clean()
        self.assertEqual("75 Smith Road", a.line1)

    def test_active_address_fields_skips_whitespace_only_fields(self):
        a = factories.UserAddressFactory.build(
            first_name="   ",
            last_name="Barrington",
            line1="  75 Smith Road  ",
            title="",
            country=self.country,
            user=self.user,
        )
        active_fields = a.active_address_fields()
        self.assertEqual("Barrington", active_fields[0])

    def test_ignores_whitespace_when_hashing(self):
        a1 = factories.UserAddressFactory.build(
            first_name="Terry",
            last_name="Barrington",
            country=self.country,
            user=self.user,
        )
        a1.clean()
        a2 = factories.UserAddressFactory.build(
            first_name="   Terry  ",
            last_name="     Barrington",
            country=self.country,
            user=self.user,
        )
        a2.clean()
        self.assertNotEqual(a1.generate_hash(), a2.generate_hash())

    def test_populate_shipping_address_doesnt_set_id(self):
        a = factories.UserAddressFactory.build(country=self.country, user=self.user)
        a.clean()
        sa = ShippingAddress()
        a.populate_alternative_model(sa)
        self.assertIsNone(sa.id)

    def test_populated_shipping_address_has_same_summary_user_address(self):
        a = factories.UserAddressFactory.build(country=self.country, user=self.user)
        a.clean()
        sa = ShippingAddress()
        a.populate_alternative_model(sa)
        self.assertEqual(sa.summary, a.summary)

    def test_summary_value(self):
        a = factories.UserAddressFactory.build(country=self.country, user=self.user)
        self.assertIsNotNone(a.summary)

    def test_summary_is_property(self):
        a = factories.UserAddressFactory.build(
            title="",
            line4="",
            first_name=" Terry  ",
            last_name="Barrington",
            line1="  75 Smith Road  ",
            country=self.country,
            user=self.user,
        )
        a.clean()
        self.assertEqual(
            f"Terry Barrington, 75 Smith Road, {a.postcode}, {a.country}", a.summary
        )

    def test_search_text_value(self):
        a = factories.UserAddressFactory()
        self.assertEqual(
            f"{a.first_name} {a.last_name} {a.line1} {a.line4} {a.state}{a.postcode} {a.country.printable_name}",
            a.search_text,
        )


VALID_POSTCODES = [
    ("GB", "N1 9RT"),
    ("SK", "991 41"),
    ("CZ", "612 00"),
    ("CC", "6799"),
    ("CY", "8240"),
    ("MC", "98000"),
    ("SH", "STHL 1ZZ"),
    ("JP", "150-2345"),
    ("PG", "314"),
    ("HN", "41202"),
    ("BN", "BC3615"),
    ("TW", "104"),
    ("TW", "10444"),
    ("IL", "1029200"),
    ("IL", "94142"),
    # It works for small cases as well
    ("GB", "sw2 1rw"),
]


INVALID_POSTCODES = [
    ("GB", "not-a-postcode"),
    ("DE", "123b4"),
]


@pytest.mark.parametrize("country_value, postcode_value", VALID_POSTCODES)
def test_assert_valid_postcode(country_value, postcode_value):
    country = models.Country(iso_3166_1_a2=country_value)
    address = models.UserAddress(country=country, postcode=postcode_value)
    address.clean()


@pytest.mark.parametrize("country_value, postcode_value", INVALID_POSTCODES)
def test_assert_invalid_postcode(country_value, postcode_value):
    country = models.Country(iso_3166_1_a2=country_value)
    address = models.UserAddress(country=country, postcode=postcode_value)

    with pytest.raises(exceptions.ValidationError):
        address.clean()
