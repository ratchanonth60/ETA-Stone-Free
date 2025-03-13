from datetime import date, datetime
from unittest import mock

import pytz
from django.conf import settings
from django.core import mail
from django.core.exceptions import ValidationError
from django.test import override_settings

from ecommerce.apps.customer.forms import (
    EmailUserCreationForm,
    OrderSearchForm,
    PasswordResetForm,
)
from ecommerce.apps.users.models import User
from ecommerce.test.factories import UserFactory
from ecommerce.test.testcases import TestCase


class TestEmailUserCreationForm(TestCase):
    def setUp(self) -> None:
        UserFactory(username="mike123", email="user@example.com", password="password")

    def test_valid_data_creates_user(self):
        form_data = {
            "email": "newuser@example.com",
            "password1": "complex_password",
            "password2": "complex_password",
        }
        form = EmailUserCreationForm(data=form_data)
        self.assertTrue(form.is_valid())

        user = form.save()
        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(user.email, "newuser@example.com")

    def test_duplicate_email_raises_error(self):
        form_data = {
            "email": "user@example.com",
            "password1": "another_password",
            "password2": "another_password",
        }
        form = EmailUserCreationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error("email"))

    def test_non_matching_passwords(self):
        form_data = {
            "email": "user@example.com",
            "password1": "password123",
            "password2": "differentpassword",
        }
        form = EmailUserCreationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("password2", form.errors)

    def test_duplicate_email(self):
        UserFactory(email="existing@example.com", password="password")
        form_data = {
            "email": "existing@example.com",
            "password1": "newpassword",
            "password2": "newpassword",
        }
        form = EmailUserCreationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    @mock.patch("ecommerce.apps.customer.forms.validate_password")
    def test_validator_passed_populated_user(self, mocked_validate):
        mocked_validate.side_effect = ValidationError("That password is rubbish")

        form = EmailUserCreationForm(
            data={"email": "terry@boom.com", "password1": "terry", "password2": "terry"}
        )
        self.assertFalse(form.is_valid())

        mocked_validate.assert_called_once_with("terry", form.instance)
        self.assertEqual(mocked_validate.call_args[0][1].email, "terry@boom.com")
        self.assertEqual(form.errors["password2"], ["That password is rubbish"])


class TestPasswordResetForm(TestCase):
    def setUp(self):
        UserFactory(username="mike123", email="mike@example.org")
        UserFactory(username="mike456", email="mıke@example.org")

    def test_user_email_unicode_collision(self):
        # Regression test for CVE-2019-19844, which Oscar's PasswordResetForm
        # was vulnerable to because it had overridden the save() method.

        form = PasswordResetForm({"email": "mıke@example.org"})
        self.assertTrue(form.is_valid())
        form.save()
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["mıke@example.org"])

    def test_no_email_sent_for_invalid_user(self):
        # Test that no email is sent for a non-existent user
        form_data = {"email": "nonexistent@example.com"}
        form = PasswordResetForm(data=form_data)
        self.assertTrue(form.is_valid())

        form.save(request=None)
        self.assertEqual(len(mail.outbox), 0)

    def test_email_content(self):
        user = UserFactory(username="user", email="user@example.com")
        form_data = {"email": "user@example.com"}
        form = PasswordResetForm(data=form_data)
        self.assertTrue(form.is_valid())

        form.save(request=None)
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertIn(user.email, email.to)
        self.assertIn("Resetting", email.subject)

    def test_invalid_email_format(self):
        form_data = {"email": "invalidemail"}
        form = PasswordResetForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)


class TestOrderSearchForm(TestCase):
    @override_settings(TIME_ZONE="Africa/Nairobi")
    def test_get_filters(self):
        form = OrderSearchForm(
            data={
                "date_from": date(2021, 1, 1),
                "date_to": date(2021, 1, 10),
                "order_number": "100",
            }
        )
        self.assertTrue(form.is_valid())

        filters = form.get_filters()
        nbi = pytz.timezone(settings.TIME_ZONE)
        self.assertEqual(
            filters,
            {
                "date_placed__gte": nbi.localize(datetime(2021, 1, 1)),
                "date_placed__lte": nbi.localize(
                    datetime(2021, 1, 10, 23, 59, 59, 999999)
                ),
                "number__contains": "100",
            },
        )

    def test_get_filters_no_date(self):
        form = OrderSearchForm(data={"order_number": "100"})
        self.assertTrue(form.is_valid())

        filters = form.get_filters()
        self.assertEqual(filters, {"number__contains": "100"})
