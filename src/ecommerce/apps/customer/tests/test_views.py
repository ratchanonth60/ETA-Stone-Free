import re
from decimal import Decimal as D
from http.cookies import _unquote
from unittest.mock import Mock, patch

from django.conf import settings
from django.contrib.sites.models import Site
from django.core import mail
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpRequest
from django.test import Client, override_settings
from django.urls import reverse
from oscar.apps.customer.history import CustomerHistoryManager
from oscar.apps.partner import strategy
from oscar.templatetags.history_tags import get_back_button

from ecommerce.apps.basket.models import Basket
from ecommerce.apps.customer.alerts.utils import AlertsDispatcher
from ecommerce.apps.customer.forms import EmailAuthenticationForm
from ecommerce.apps.customer.utils import CustomerDispatcher
from ecommerce.apps.order.models import Order
from ecommerce.apps.users.models import User
from ecommerce.core.celery.tasks.email import send_password_changed_email_for_user
from ecommerce.test import factories
from ecommerce.test.factories import (
    ProductAlertFactory,
    UserFactory,
    create_order,
    create_product,
)
from ecommerce.test.testcases import TestCase, WebTestCase
from ecommerce.test.utils import EmailsMixin

COOKIE_NAME = settings.OSCAR_RECENTLY_VIEWED_COOKIE_NAME


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class TestAUserWhoseForgottenHerPassword(WebTestCase):
    def setUp(self) -> None:
        super().setUp()
        username, email, password = "lucy", "lucy@example.com", "password"
        self.email = email
        self.user = User.objects.create(
            username=username, email=email, password=password
        )
        self.user.save()

    def test_can_reset_her_password(self):
        # Fill in password reset form
        page = self.app.get(reverse("password-reset"))
        form = page.forms["password_reset_form"]
        form["email"] = self.email
        response = form.submit()
        # Response should be a redirect and an email should have been sent
        self.assertEqual(302, response.status_code)
        self.assertEqual(1, len(mail.outbox))

        # Extract URL from email
        email_body = mail.outbox[0].body
        url_finder = re.compile(r"http://example.com(?P<path>[-A-Za-z0-9\/\._]+)")
        matches = url_finder.search(email_body, re.MULTILINE)
        self.assertTrue("path" in matches.groupdict())
        path = matches.groupdict()["path"]

        # Reset password and check we get redirected
        reset_page_redirect = self.app.get(path)
        # The link in the email will redirect us to the password reset view
        reset_page = self.app.get(reset_page_redirect.location)
        form = reset_page.forms["password_reset_form"]
        form["new_password1"] = "crazymonkey"
        form["new_password2"] = "crazymonkey"
        response = form.submit()
        self.assertEqual(302, response.status_code)

        # Now attempt to login with new password
        url = reverse("customer:login")
        form = self.app.get(url).forms["login_form"]
        form["login-username"] = self.email
        form["login-password"] = "crazymonkey"
        response = form.submit("login_submit")
        self.assertEqual(302, response.status_code)


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class TestAnAuthenticatedUser(WebTestCase):
    is_anonymous = False

    def test_receives_an_email_when_their_password_is_changed(self):
        page = self.get(reverse("customer:change-password"))
        form = page.forms["change_password_form"]
        form["old_password"] = self.password
        form["new_password1"] = "anotherfancypassword"
        form["new_password2"] = "anotherfancypassword"
        page = form.submit()

        send_password_changed_email_for_user(user_id=self.user.id)
        self.assertEqual(len(mail.outbox), 2)
        self.assertIn("your password has been changed", mail.outbox[0].body)

    def test_cannot_access_reset_password_page(self):
        response = self.get(reverse("password-reset"), status=403)
        self.assertEqual(403, response.status_code)

    def test_does_not_receive_an_email_when_their_profile_is_updated_but_email_address_not_changed(
        self,
    ):
        page = self.get(reverse("customer:profile-update"))
        form = page.forms["profile_form"]
        form["first_name"] = "Terry"
        form.submit()
        self.assertEqual(len(mail.outbox), 0)

    def test_receives_an_email_when_their_email_address_is_changed(self):
        page = self.get(reverse("customer:profile-update"))
        form = page.forms["profile_form"]

        new_email = "a.new.email@user.com"
        form["email"] = new_email
        page = form.submit()

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to[0], self.email)
        self.assertEqual(User.objects.get(id=self.user.id).email, new_email)
        self.assertIn("your email address has been changed", mail.outbox[0].body)


class TestAnAnonymousUser(WebTestCase):
    is_anonymous = True

    def test_can_login(self):
        email, password = "d@d.com", "mypassword"
        User.objects.create_user("_", email, password)
        url = reverse("customer:login")
        form = self.app.get(url).forms["login_form"]
        form["login-username"] = email
        form["login-password"] = password
        response = form.submit("login_submit")
        self.assertEqual(response.status_code, 302)
        response = response.follow()
        self.assertEqual(response.status_code, 200)

    def test_can_login_with_email_containing_capitals_in_local_part(self):
        email, password = "Andrew.Smith@test.com", "mypassword"
        User.objects.create_user("_", email, password)
        url = reverse("customer:login")
        form = self.app.get(url).forms["login_form"]
        form["login-username"] = email
        form["login-password"] = password
        response = form.submit("login_submit")
        self.assertEqual(response.status_code, 302)
        response = response.follow()
        self.assertEqual(response.status_code, 200)

    def test_can_login_with_email_containing_capitals_in_host(self):
        email, password = "Andrew.Smith@teSt.com", "mypassword"
        User.objects.create_user("_", email, password)
        url = reverse("customer:login")
        form = self.app.get(url).forms["login_form"]
        form["login-username"] = email
        form["login-password"] = password
        response = form.submit("login_submit").follow()
        self.assertEqual(response.status_code, 200)

    def test_can_register(self):
        url = reverse("customer:register")
        form = self.app.get(url).forms["register_form"]
        form["email"] = "terry@boom.com"
        form["password1"] = form["password2"] = "hedgehog"
        response = form.submit()
        self.assertEqual(response.status_code, 200)


class TestAStaffUser(WebTestCase):
    is_anonymous = True
    password = "testing"

    def setUp(self):
        self.staff = factories.UserFactory.create(password=self.password, is_staff=True)
        super().setUp()

    def test_gets_redirected_to_the_dashboard_when_they_login(self):
        page = self.get(reverse("customer:login"))
        form = page.forms["login_form"]
        form["login-username"] = self.staff.email
        form["login-password"] = self.password
        response = form.submit("login_submit").follow()
        self.assertEqual(response.status_code, 200)


class TestCustomerConcreteEmailsSending(EmailsMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.dispatcher = CustomerDispatcher()

    def test_send_registration_email_for_user(self, additional_context=None):
        extra_context = {"user": self.user}
        if additional_context:
            extra_context |= additional_context

        self.dispatcher.send_registration_email_for_user(self.user, extra_context)

        self._test_common_part()
        self.assertEqual("Thank you for registering.", mail.outbox[0].subject)
        self.assertIn("Thank you for registering.", mail.outbox[0].body)

    @override_settings(SITE_ID=None, ALLOWED_HOSTS=["example.com"])
    def test_send_registration_email_for_user_multisite(self):
        with self.assertRaises(
            ImproperlyConfigured, msg=self.DJANGO_IMPROPERLY_CONFIGURED_MSG
        ):
            self.test_send_registration_email_for_user()

        additional_context = {"request": self.request}
        self.test_send_registration_email_for_user(
            additional_context=additional_context
        )

    def test_send_password_reset_email_for_user(self, additional_context=None):
        extra_context = {
            "user": self.user,
            "reset_url": "/django/django-noob",
        }

        request = None
        if additional_context:
            request = additional_context.get("request")
            extra_context |= additional_context

        self.dispatcher.send_password_reset_email_for_user(self.user, extra_context)

        self._test_common_part()
        expected_subject = (
            f"Resetting your password at {Site.objects.get_current(request)}."
        )
        self.assertEqual(expected_subject, mail.outbox[0].subject)
        self.assertIn(
            "Please go to the following page and choose a new password:",
            mail.outbox[0].body,
        )
        self.assertIn("http://example.com/django/django-noob", mail.outbox[0].body)

    @override_settings(SITE_ID=None, ALLOWED_HOSTS=["example.com"])
    def test_send_password_reset_email_for_user_multisite(self):
        with self.assertRaises(
            ImproperlyConfigured, msg=self.DJANGO_IMPROPERLY_CONFIGURED_MSG
        ):
            self.test_send_password_reset_email_for_user()

        additional_context = {"request": self.request}
        self.test_send_password_reset_email_for_user(
            additional_context=additional_context
        )

    def test_send_password_changed_email_for_user(self, additional_context=None):
        extra_context = {
            "user": self.user,
            "reset_url": "/django-oscar/django-oscar",
        }

        request = None
        if additional_context:
            request = additional_context.get("request")
            extra_context |= additional_context

        self.dispatcher.send_password_changed_email_for_user(self.user, extra_context)

        self._test_common_part()
        expected_subject = (
            f"Your password changed at {Site.objects.get_current(request)}."
        )
        self.assertEqual(expected_subject, mail.outbox[0].subject)
        self.assertIn("your password has been changed", mail.outbox[0].body)
        self.assertIn(
            "http://example.com/django-oscar/django-oscar", mail.outbox[0].body
        )

    @override_settings(SITE_ID=None, ALLOWED_HOSTS=["example.com"])
    def test_send_password_changed_email_for_user_multisite(self):
        with self.assertRaises(
            ImproperlyConfigured, msg=self.DJANGO_IMPROPERLY_CONFIGURED_MSG
        ):
            self.test_send_password_changed_email_for_user()

        additional_context = {"request": self.request}
        self.test_send_password_changed_email_for_user(
            additional_context=additional_context
        )

    def test_send_email_changed_email_for_user(self, additional_context=None):
        extra_context = {
            "user": self.user,
            "reset_url": "/django-oscar/django-oscar",
            "new_email": "some_new@mail.com",
        }

        request = None
        if additional_context:
            request = additional_context.get("request")
            extra_context |= additional_context

        self.dispatcher.send_email_changed_email_for_user(self.user, extra_context)

        self._test_common_part()
        expected_subject = (
            f"Your email address has changed at {Site.objects.get_current(request)}."
        )
        self.assertEqual(expected_subject, mail.outbox[0].subject)
        self.assertIn("your email address has been changed", mail.outbox[0].body)
        self.assertIn(
            "http://example.com/django-oscar/django-oscar", mail.outbox[0].body
        )
        self.assertIn("some_new@mail.com", mail.outbox[0].body)

    @override_settings(SITE_ID=None, ALLOWED_HOSTS=["example.com"])
    def test_send_email_changed_email_for_user_multisite(self):
        with self.assertRaises(
            ImproperlyConfigured, msg=self.DJANGO_IMPROPERLY_CONFIGURED_MSG
        ):
            self.test_send_email_changed_email_for_user()

        additional_context = {"request": self.request}
        self.test_send_email_changed_email_for_user(
            additional_context=additional_context
        )


class TestAlertsConcreteEmailsSending(EmailsMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.dispatcher = AlertsDispatcher()

    def test_send_product_alert_email_for_user(self):
        product = create_product(num_in_stock=5)
        ProductAlertFactory(product=product, user=self.user)

        self.dispatcher.send_product_alert_email_for_user(product)

        self._test_common_part()
        expected_subject = f"{product.title} is back in stock"
        self.assertEqual(expected_subject, mail.outbox[0].subject)
        self.assertIn(
            "We are happy to inform you that our product", mail.outbox[0].body
        )
        # No `hurry_mode`
        self.assertNotIn(
            "Beware that the amount of items in stock is limited.", mail.outbox[0].body
        )

    def test_send_product_alert_email_for_user_with_hurry_mode(self):
        another_user = UserFactory(email="another_user@mail.com")
        product = create_product(num_in_stock=1)
        ProductAlertFactory(product=product, user=self.user, email=self.user.email)
        ProductAlertFactory(
            product=product, user=another_user, email=another_user.email
        )

        self.dispatcher.send_product_alert_email_for_user(product)
        self.assertEqual(len(mail.outbox), 2)  # Separate email for each user
        expected_subject = f"{product.title} is back in stock"
        self.assertEqual(expected_subject, mail.outbox[0].subject)
        for outboxed_email in mail.outbox:
            self.assertEqual(expected_subject, outboxed_email.subject)
            self.assertIn(
                "We are happy to inform you that our product", outboxed_email.body
            )
            self.assertIn(
                "Beware that the amount of items in stock is limited.",
                outboxed_email.body,
            )

    def test_send_product_alert_confirmation_email_for_user(self):
        product = create_product(num_in_stock=5)
        alert = ProductAlertFactory(
            product=product, user=self.user, email=self.user.email, key="key00042"
        )

        self.dispatcher.send_product_alert_confirmation_email_for_user(alert)

        self._test_common_part()
        self.assertEqual(
            "Confirmation required for stock alert", mail.outbox[0].subject
        )
        self.assertIn(
            "Somebody (hopefully you) has requested an email alert", mail.outbox[0].body
        )
        self.assertIn(alert.get_confirm_url(), mail.outbox[0].body)
        self.assertIn(alert.get_cancel_url(), mail.outbox[0].body)


class HistoryHelpersTest(WebTestCase):
    def setUp(self):
        self.product = create_product()

    def test_viewing_product_creates_cookie(self):
        response = self.app.get(self.product.get_absolute_url())
        self.assertTrue(COOKIE_NAME in response.test_app.cookies)

    def test_id_gets_added_to_cookie(self):
        response = self.app.get(self.product.get_absolute_url())
        request = HttpRequest()
        request.COOKIES[COOKIE_NAME] = _unquote(response.test_app.cookies[COOKIE_NAME])
        self.assertTrue(self.product.id in CustomerHistoryManager.extract(request))

    def test_get_back_button(self):
        request = HttpRequest()

        request.META["SERVER_NAME"] = "test"
        request.META["SERVER_PORT"] = 8000
        request.META["HTTP_REFERER"] = "http://www.google.com"
        backbutton = get_back_button({"request": request})
        self.assertEqual(backbutton, None)

        request.META["HTTP_REFERER"] = "http://test:8000/search/"
        backbutton = get_back_button({"request": request})
        self.assertTrue(backbutton)
        self.assertEqual(backbutton["title"], "Back to search results")


class TestAUserWhoLogsOut(WebTestCase):
    username = "customer"
    password = "cheeseshop"
    email = "customer@example.com"

    def setUp(self):
        self.product = create_product()
        self.user = User.objects.create_user(
            username=self.username, email=self.email, password=self.password
        )

    def test_has_their_cookies_deleted_on_logout(self):
        response = self.get(self.product.get_absolute_url())
        self.assertTrue(COOKIE_NAME in response.test_app.cookies)

        response = self.get(reverse("customer:logout"))
        self.assertTrue(
            (COOKIE_NAME not in response.test_app.cookies)
            or not self.app.cookies.get("oscar_recently_viewed_products", None)
        )


class TestASignedInUser(WebTestCase):
    email = "customer@example.com"
    password = "cheeseshop"

    def setUp(self):
        self.user = User.objects.create_user("_", self.email, self.password)
        self.order = create_order(user=self.user)

    def test_can_view_their_profile(self):
        response = self.app.get(reverse("customer:profile-view"), user=self.user)
        self.assertEqual(200, response.status_code)
        self.assertTrue(self.email in response.content.decode("utf8"))

    def test_can_delete_their_profile(self):
        user_id = self.user.id
        order_id = self.order.id

        profile = self.app.get(reverse("customer:profile-view"), user=self.user)
        delete_confirm = profile.click(linkid="delete_profile")
        form = delete_confirm.forms["delete_profile_form"]
        form["password"] = self.password
        form.submit()

        # Ensure user is deleted
        users = User.objects.filter(id=user_id)
        self.assertEqual(0, len(users))

        # Ensure order isn't deleted
        users = User.objects.filter(id=user_id)
        orders = Order.objects.filter(id=order_id)
        self.assertEqual(1, len(orders))

    def test_can_update_their_name(self):
        profile_form_page = self.app.get(
            reverse("customer:profile-update"), user=self.user
        )
        self.assertEqual(200, profile_form_page.status_code)
        form = profile_form_page.forms["profile_form"]
        form["first_name"] = "Barry"
        form["last_name"] = "Chuckle"
        response = form.submit().follow()
        self.assertEqual(response.status_code, 200)

    def test_can_update_their_email_address_and_name(self):
        profile_form_page = self.app.get(
            reverse("customer:profile-update"), user=self.user
        )
        self.assertEqual(200, profile_form_page.status_code)
        form = profile_form_page.forms["profile_form"]
        form["email"] = "new@example.com"
        form["first_name"] = "Barry"
        form["last_name"] = "Chuckle"
        response = form.submit().follow()
        self.assertEqual(response.status_code, 200)

        user = User.objects.get(id=self.user.id)
        self.assertEqual("new@example.com", user.email)
        self.assertEqual("Barry", user.first_name)
        self.assertEqual("Chuckle", user.last_name)

    def test_cant_update_their_email_address_if_it_already_exists(self):
        # create a user to "block" new@example.com
        User.objects.create_user(
            username="testuser", email="new@example.com", password="somerandompassword"
        )
        self.assertEqual(User.objects.count(), 2)

        for email in ["new@example.com", "New@Example.com"]:
            profile_form_page = self.app.get(
                reverse("customer:profile-update"), user=self.user
            )
            form = profile_form_page.forms["profile_form"]
            form["email"] = email
            form["first_name"] = "Barry"
            form["last_name"] = "Chuckle"
            response = form.submit()

            # assert that the original user's email address is unchanged
            user = User.objects.get(id=self.user.id)
            self.assertEqual(self.email, user.email)
            self.assertEqual(
                User.objects.filter(email__iexact="new@example.com").count(), 1
            )
            self.assertContains(
                response, "A user with this email address already exists"
            )

    def test_can_change_their_password(self):
        new_password = "bubblesgopop"
        password_form_page = self.app.get(
            reverse("customer:change-password"), user=self.user
        )
        self.assertEqual(200, password_form_page.status_code)
        form = password_form_page.forms["change_password_form"]
        form["old_password"] = self.password
        form["new_password1"] = form["new_password2"] = new_password
        response = form.submit().follow()
        self.assertEqual(response.status_code, 200)
        updated_user = User.objects.get(pk=self.user.pk)
        self.assertTrue(updated_user.check_password(new_password))

    def test_can_reorder_a_previous_order(self):
        order_history_page = self.app.get(
            reverse("customer:order", args=[self.order.number]), user=self.user
        )
        form = order_history_page.forms["order_form_%d" % self.order.id]
        form.submit()

        basket = Basket.open.get(owner=self.user)
        basket.strategy = strategy.Default()
        self.assertEqual(1, basket.all_lines().count())

    def test_can_reorder_a_previous_order_line(self):
        order_history_page = self.app.get(
            reverse("customer:order", kwargs={"order_number": self.order.number}),
            user=self.user,
        )
        line = self.order.lines.all()[0]
        form = order_history_page.forms["line_form_%d" % line.id]
        form.submit()

        basket = Basket.open.get(owner=self.user)
        basket.strategy = strategy.Default()
        self.assertEqual(1, basket.all_lines().count())

    def test_cannot_reorder_an_out_of_stock_product(self):
        line = self.order.lines.all()[0]
        line.stockrecord.num_in_stock = 0
        line.stockrecord.save()

        order_history_page = self.app.get(
            reverse("customer:order", args=[self.order.number]), user=self.user
        )
        form = order_history_page.forms["order_form_%d" % self.order.id]
        form.submit()

        basket = Basket.open.get(owner=self.user)
        self.assertEqual(0, basket.all_lines().count())


class TestReorderingOrderLines(WebTestCase):
    # TODO - rework this as a webtest
    @patch("django.conf.settings.OSCAR_MAX_BASKET_QUANTITY_THRESHOLD", 1)
    def test_cannot_reorder_when_basket_maximum_exceeded(self):
        order = create_order(user=self.user)
        line = order.lines.all()[0]

        product = create_product(price=D("12.00"))
        product_page = self.get(line.product.get_absolute_url())
        product_page.forms["add_to_basket_form"].submit()

        basket = Basket.objects.all()[0]
        basket.strategy = strategy.Default()
        self.assertEqual(len(basket.all_lines()), 1)

        # Try to reorder the whole order
        order_page = self.get(reverse("customer:order", args=(order.number,)))
        order_page.forms[f"order_form_{order.id}"].submit()

        self.assertEqual(len(basket.all_lines()), 1)
        self.assertNotEqual(line.product.pk, product.pk)

    @patch("django.conf.settings.OSCAR_MAX_BASKET_QUANTITY_THRESHOLD", 1)
    def test_cannot_reorder_line_when_basket_maximum_exceeded(self):
        order = create_order(user=self.user)
        line = order.lines.all()[0]

        product = create_product(price=D("12.00"))
        product_page = self.get(line.product.get_absolute_url())
        product_page.forms["add_to_basket_form"].submit()

        basket = Basket.objects.all()[0]
        basket.strategy = strategy.Default()
        self.assertEqual(len(basket.all_lines()), 1)

        # Try to reorder a line
        order_page = self.get(reverse("customer:order", args=(order.number,)))
        order_page.forms[f"line_form_{line.id}"].submit()

        self.assertEqual(len(basket.all_lines()), 1)
        self.assertNotEqual(line.product.pk, product.pk)


class PaymentManagementListViewTests(WebTestCase):
    def setUp(self):
        self.user = UserFactory()  # Create a test user using factory
        self.url = reverse(
            "customer:payment-list"
        )  # replace with your actual reverse name

    def test_redirect_if_not_logged_in(self):
        response = self.app.get(self.url).follow()
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        page = self.app.get(self.url, user=self.user)
        self.assertEqual(page.status_code, 200)
        self.assertTemplateUsed(
            page, "eta/customer/payment/payment_management_list.html"
        )

    # def test_only_user_payments_are_displayed(self):
    #     other_user = UserFactory()
    #     factories.BankcardFactory(user=self.user)  # Card for the logged in user
    #     factories.BankcardFactory(user=other_user)  # Card for some other user
    #     page = self.app.get(self.url, user=self.user)
    #     self.assertEqual(len(page.context['payments']), 1)


class PaymentManagementCreateViewTests(WebTestCase):
    def setUp(self):
        self.user = UserFactory()
        self.url = reverse(
            "customer:payment-create"
        )  # replace with your actual reverse name

    def test_redirect_if_not_logged_in(self):
        response = self.app.get(self.url).follow()
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        page = self.app.get(self.url, user=self.user)
        self.assertEqual(page.status_code, 200)
        self.assertTemplateUsed(
            page, "eta/customer/payment/payment_management_form.html"
        )

    # def test_add_payment(self):
    #     page = self.app.get(self.url, user=self.user)
    #     form = page.forms[1]
    #     form['number'] = "4111111111111111"
    #     form['expiry_month_0'] = 11
    #     form['expiry_month_1'] = 2032
    #     form['ccv'] = 123
    #     response = form.submit().follow()
    #     self.assertEqual(response.status_code, 200)
    #     self.assertEqual(Bankcard.objects.count(), 1)
    #     self.assertEqual(Bankcard.objects.first().user, self.user)


class TestAccountAuthView(TestCase):
    def setUp(self):
        self.client = Client()

    def test_request_is_passed_to_form(self):
        form_class = Mock(wraps=EmailAuthenticationForm)
        data = {"login_submit": ["1"]}
        initial = {"redirect_url": ""}
        with patch(
            "ecommerce.apps.customer.views.AccountAuthView.login_form_class",
            new=form_class,
        ):
            response = self.client.post(reverse("customer:login"), data=data)
            assert form_class.called
            form_class.assert_called_with(
                data=data,
                files={},
                host="testserver",
                initial=initial,
                prefix="login",
                request=response.wsgi_request,
            )
