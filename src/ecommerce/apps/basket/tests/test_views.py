import datetime
from decimal import Decimal as D
from http import client as http_client
from http.cookies import _unquote

import django
from django.contrib.messages import get_messages
from django.contrib.messages.storage import cookie
from django.core import signing
from django.test import override_settings
from django.urls import reverse
from django.utils.translation import gettext
from oscar.apps.basket import reports
from oscar.apps.partner import strategy
from oscar.core.compat import get_user_model

from ecommerce.apps.basket import models, views
from ecommerce.apps.basket.models import Basket
from ecommerce.apps.catalogue.models import AttributeOption, AttributeOptionGroup, Option
from ecommerce.apps.checkout.tests import CheckoutMixin
from ecommerce.test import factories
from ecommerce.test.basket import add_product
from ecommerce.test.factories import create_product
from ecommerce.test.fixtures import RequestFactory
from ecommerce.test.testcases import TestCase, WebTestCase

User = get_user_model()


class TestAddingToBasket(WebTestCase):
    def test_works_for_standalone_product(self):
        product = factories.ProductFactory()

        detail_page = self.get(product.get_absolute_url())
        response = detail_page.forms["add_to_basket_form"].submit()

        self.assertIsRedirect(response)
        baskets = models.Basket.objects.all()
        self.assertEqual(1, len(baskets))

        basket = baskets[0]
        self.assertEqual(1, basket.num_items)

    def test_works_for_child_product(self):
        parent = factories.ProductFactory(structure="parent", stockrecords=[])
        for x in range(3):
            variant = factories.ProductFactory(parent=parent, structure="child")

            detail_page = self.get(variant.get_absolute_url())
            form = detail_page.forms["add_to_basket_form"]
            response = form.submit()

            self.assertIsRedirect(response)

        baskets = models.Basket.objects.all()
        self.assertEqual(1, len(baskets))

        basket = baskets[0]
        self.assertEqual(3, basket.num_items)

    def test_validation_errors_in_form(self):
        product = factories.ProductFactory()
        product_class = product.get_product_class()
        group = AttributeOptionGroup.objects.create(name="checkbox options")
        AttributeOption.objects.create(group=group, option="1")
        AttributeOption.objects.create(group=group, option="2")

        option = Option.objects.create(
            type=Option.CHECKBOX,
            required=True,
            name="Required checkbox",
            option_group=group,
        )
        text_option = Option.objects.create(
            type=Option.TEXT, required=False, name="Open tekst"
        )

        product_class.options.add(option)
        product_class.options.add(text_option)
        product_class.save()

        detail_page = self.get(product.get_absolute_url())
        detail_page.forms["add_to_basket_form"]["open-tekst"] = "test harrie"
        response = detail_page.forms["add_to_basket_form"].submit().follow()

        self.assertEqual(
            response.forms["add_to_basket_form"]["open-tekst"].value, "test harrie"
        )
        baskets = models.Basket.objects.all()
        self.assertEqual(1, len(baskets))

        basket = baskets[0]
        self.assertEqual(0, basket.lines.count())


class TestVoucherAddView(TestCase):
    def test_get(self):
        request = RequestFactory().get("/")

        view = views.VoucherAddView.as_view()
        response = view(request)

        self.assertEqual(response.status_code, 302)

    def _get_voucher_message(self, request):
        return "\n".join(str(m.message) for m in get_messages(request))

    def test_post_valid(self):
        voucher = factories.VoucherFactory()
        self.assertTrue(voucher.is_active())

        data = {"code": voucher.code}
        request = RequestFactory().post("/", data=data)
        request.basket.save()

        view = views.VoucherAddView.as_view()
        response = view(request)
        self.assertEqual(response.status_code, 302)

        voucher = voucher.__class__.objects.get(pk=voucher.pk)
        self.assertEqual(
            voucher.num_basket_additions, 1, msg=self._get_voucher_message(request)
        )

    def test_post_valid_from_set(self):
        voucherset = factories.VoucherSetFactory()
        voucher = voucherset.vouchers.first()

        self.assertTrue(voucher.is_active())

        data = {"code": voucher.code}
        request = RequestFactory().post("/", data=data)
        request.basket.save()

        view = views.VoucherAddView.as_view()
        response = view(request)
        self.assertEqual(response.status_code, 302)

        voucher = voucher.__class__.objects.get(pk=voucher.pk)
        self.assertEqual(
            voucher.num_basket_additions, 1, msg=self._get_voucher_message(request)
        )

        self.assertEqual(voucherset.num_basket_additions, 1)


class TestVoucherRemoveView(TestCase):
    def test_post_valid(self):
        voucher = factories.VoucherFactory(num_basket_additions=5)

        data = {"code": voucher.code}
        request = RequestFactory().post("/", data=data)
        request.basket.save()
        request.basket.vouchers.add(voucher)

        view = views.VoucherRemoveView.as_view()
        response = view(request, pk=voucher.pk)
        self.assertEqual(response.status_code, 302)

        voucher = voucher.__class__.objects.get(pk=voucher.pk)
        self.assertEqual(voucher.num_basket_additions, 4)

    def test_post_with_missing_voucher(self):
        """If the voucher is missing, verify the view queues a message and redirects."""
        pk = "12345"
        view = views.VoucherRemoveView.as_view()
        request = RequestFactory().post("/")
        request.basket.save()
        response = view(request, pk=pk)

        self.assertEqual(response.status_code, 302)

        actual = list(get_messages(request))[-1].message
        expected = "No voucher found with id '{}'".format(pk)
        self.assertEqual(actual, expected)


class TestBasketSummaryView(TestCase):
    def setUp(self):
        self.url = reverse("basket:summary")
        self.country = factories.CountryFactory()
        self.user = factories.UserFactory()

    def test_default_shipping_address(self):
        user_address = factories.UserAddressFactory(
            country=self.country, user=self.user, is_default_for_shipping=True
        )
        request = RequestFactory().get(self.url, user=self.user)
        view = views.BasketView(request=request)
        self.assertEqual(view.get_default_shipping_address(), user_address)

    def test_default_shipping_address_for_anonymous_user(self):
        request = RequestFactory().get(self.url)
        view = views.BasketView(request=request)
        self.assertIsNone(view.get_default_shipping_address())


class TestVoucherViews(CheckoutMixin, WebTestCase):
    csrf_checks = False

    def setUp(self):
        super().setUp()
        self.voucher = factories.create_voucher()

    def test_add_voucher(self):
        """
        Checks that voucher can be added to basket through appropriate view.
        """
        self.add_product_to_basket()

        assert self.voucher.basket_set.count() == 0

        response = self.post(
            reverse("basket:vouchers-add"), params={"code": self.voucher.code}
        )
        self.assertRedirectsTo(response, "basket:summary")
        assert self.voucher.basket_set.count() == 1

    def test_remove_voucher(self):
        """
        Checks that voucher can be removed from basket through appropriate view.
        """
        self.add_product_to_basket()
        self.add_voucher_to_basket(voucher=self.voucher)

        assert self.voucher.basket_set.count() == 1

        response = self.post(
            reverse("basket:vouchers-remove", kwargs={"pk": self.voucher.id})
        )
        self.assertRedirectsTo(response, "basket:summary")
        assert self.voucher.basket_set.count() == 0


class TestOptionAddToBasketView(TestCase):
    def setUp(self):
        super().setUp()

    def setup_options(self, required):
        self.product = factories.create_product(num_in_stock=1)
        group = factories.AttributeOptionGroupFactory(name="minte")
        factories.AttributeOptionFactory(option="henk", group=group)
        factories.AttributeOptionFactory(option="klaas", group=group)
        self.select = factories.OptionFactory(
            required=required,
            code=Option.SELECT,
            type=Option.SELECT,
            option_group=group,
        )
        self.radio = factories.OptionFactory(
            required=required, code=Option.RADIO, type=Option.RADIO, option_group=group
        )
        self.multi_select = factories.OptionFactory(
            required=required,
            code=Option.MULTI_SELECT,
            type=Option.MULTI_SELECT,
            option_group=group,
        )
        self.checkbox = factories.OptionFactory(
            required=required,
            code=Option.CHECKBOX,
            type=Option.CHECKBOX,
            option_group=group,
        )

        self.product.product_class.options.add(self.select)
        self.product.product_class.options.add(self.radio)
        self.product.product_class.options.add(self.multi_select)
        self.product.product_class.options.add(self.checkbox)

    def test_option_visible_required(self):
        self.setup_options(True)
        url = reverse("catalogue:detail", args=(self.product.slug, self.product.pk))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, Option.SELECT)
        self.assertContains(response, Option.RADIO)
        self.assertContains(response, Option.MULTI_SELECT)
        self.assertContains(response, Option.CHECKBOX)

    def test_option_visible_not_required(self):
        self.setup_options(False)
        url = reverse("catalogue:detail", args=(self.product.slug, self.product.pk))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, Option.SELECT)
        self.assertContains(response, Option.RADIO)
        self.assertContains(response, Option.MULTI_SELECT)
        self.assertContains(response, Option.CHECKBOX)

    def test_add_to_basket_with_options_required(self):
        self.setup_options(True)
        url = reverse("basket:add", kwargs={"pk": self.product.pk})
        post_params = {
            "product_id": self.product.id,
            Option.SELECT: "klaas",
            Option.RADIO: "henk",
            Option.MULTI_SELECT: ["henk", "klaas"],
            Option.CHECKBOX: ["henk"],
            "action": "add",
            "quantity": 1,
        }
        response = self.client.post(url, post_params, follow=True)
        basket = response.context["basket"]

        self.assertEqual(
            basket.all_lines().count(),
            1,
            "One line should have been added to the basket",
        )
        (line,) = basket.all_lines()

        self.assertEqual(
            line.attributes.count(),
            4,
            "One lineattribute shoould have been added to the basket",
        )
        checkbox, multi_select, radio, select = line.attributes.order_by("option__code")

        self.assertEqual(
            checkbox.value, ["henk"], "The lineattribute should be saved as json"
        )
        self.assertEqual(
            checkbox.option,
            self.checkbox,
            "The lineattribute's option should be the option created by the factory",
        )

        self.assertListEqual(
            multi_select.value,
            ["henk", "klaas"],
            "The lineattribute should be saved as json",
        )
        self.assertEqual(
            multi_select.option,
            self.multi_select,
            "The lineattribute's option should be the option created by the factory",
        )

        self.assertEqual(
            radio.value, "henk", "The lineattribute should be saved as json"
        )
        self.assertEqual(
            radio.option,
            self.radio,
            "The lineattribute's option should be the option created by the factory",
        )

        self.assertEqual(
            select.value, "klaas", "The lineattribute should be saved as json"
        )
        self.assertEqual(
            select.option,
            self.select,
            "The lineattribute's option should be the option created by the factory",
        )

    def test_add_to_basket_with_options_not_required(self):
        self.setup_options(False)
        url = reverse("basket:add", kwargs={"pk": self.product.pk})
        post_params = {
            "product_id": self.product.id,
            Option.SELECT: "klaas",
            Option.RADIO: "henk",
            Option.MULTI_SELECT: [],
            Option.CHECKBOX: ["henk"],
            "action": "add",
            "quantity": 1,
        }
        response = self.client.post(url, post_params, follow=True)
        basket = response.context["basket"]

        self.assertEqual(
            basket.all_lines().count(),
            1,
            "One line should have been added to the basket",
        )
        (line,) = basket.all_lines()

        self.assertEqual(
            line.attributes.count(),
            3,
            "One lineattribute shoould have been added to the basket",
        )
        checkbox, radio, select = line.attributes.order_by("option__code")

        self.assertEqual(
            checkbox.value, ["henk"], "The lineattribute should be saved as json"
        )
        self.assertEqual(
            checkbox.option,
            self.checkbox,
            "The lineattribute's option should be the option created by the factory",
        )

        self.assertEqual(
            radio.value, "henk", "The lineattribute should be saved as json"
        )
        self.assertEqual(
            radio.option,
            self.radio,
            "The lineattribute's option should be the option created by the factory",
        )

        self.assertEqual(
            select.value, "klaas", "The lineattribute should be saved as json"
        )
        self.assertEqual(
            select.option,
            self.select,
            "The lineattribute's option should be the option created by the factory",
        )


class TestBasketMerging(TestCase):
    def setUp(self):
        self.product = create_product(num_in_stock=10)
        self.user_basket = Basket()
        self.user_basket.strategy = strategy.Default()
        add_product(self.user_basket, product=self.product)
        self.cookie_basket = Basket()
        self.cookie_basket.strategy = strategy.Default()
        add_product(self.cookie_basket, quantity=2, product=self.product)
        self.user_basket.merge(self.cookie_basket, add_quantities=False)

    def test_cookie_basket_has_status_set(self):
        self.assertEqual(Basket.MERGED, self.cookie_basket.status)

    def test_lines_are_moved_across(self):
        self.assertEqual(1, self.user_basket.lines.all().count())

    def test_merge_line_takes_max_quantity(self):
        line = self.user_basket.lines.get(product=self.product)
        self.assertEqual(2, line.quantity)


class AnonAddToBasketViewTests(WebTestCase):
    csrf_checks = False

    def setUp(self):
        self.product = create_product(price=D("10.00"), num_in_stock=10)
        url = reverse("basket:add", kwargs={"pk": self.product.pk})
        post_params = {"product_id": self.product.id, "action": "add", "quantity": 1}
        self.response = self.app.post(url, params=post_params)

    def test_cookie_is_created(self):
        self.assertTrue("oscar_open_basket" in self.response.test_app.cookies)

    def test_price_is_recorded(self):
        oscar_open_basket_cookie = _unquote(
            self.response.test_app.cookies["oscar_open_basket"]
        )
        basket_id = oscar_open_basket_cookie.split(":")[0]
        basket = Basket.objects.get(id=basket_id)
        line = basket.lines.get(product=self.product)
        stockrecord = self.product.stockrecords.all()[0]
        self.assertEqual(stockrecord.price, line.price_excl_tax)


class BasketSummaryViewTests(WebTestCase):
    def setUp(self):
        url = reverse("basket:summary")
        self.response = self.app.get(url)

    def test_shipping_method_in_context(self):
        self.assertTrue("shipping_method" in self.response.context)

    def test_order_total_in_context(self):
        self.assertTrue("order_total" in self.response.context)

    def test_view_does_not_error(self):
        self.assertEqual(http_client.OK, self.response.status_code)

    def test_basket_in_context(self):
        self.assertTrue("basket" in self.response.context)

    def test_basket_is_empty(self):
        basket = self.response.context["basket"]
        self.assertEqual(0, basket.num_lines)


class BasketThresholdTest(WebTestCase):
    csrf_checks = False

    @override_settings(OSCAR_MAX_BASKET_QUANTITY_THRESHOLD=3)
    def test_adding_more_than_threshold_raises(self):
        dummy_product = create_product(price=D("10.00"), num_in_stock=10)
        url = reverse("basket:add", kwargs={"pk": dummy_product.pk})
        post_params = {"product_id": dummy_product.id, "action": "add", "quantity": 2}
        response = self.app.post(url, params=post_params)
        self.assertIn("oscar_open_basket", response.test_app.cookies)
        post_params = {"product_id": dummy_product.id, "action": "add", "quantity": 2}
        response = self.app.post(url, params=post_params)
        expected = gettext(
            "Due to technical limitations we are not able to ship more "
            "than %(threshold)d items in one order. Your basket currently "
            "has %(basket)d items."
        ) % ({"threshold": 3, "basket": 2})
        if django.VERSION < (3, 2):
            self.assertIn(expected, response.test_app.cookies["messages"])
        else:
            signer = signing.get_cookie_signer(salt="django.contrib.messages")
            message_strings = [
                m.message
                for m in signer.unsign_object(
                    response.test_app.cookies["messages"],
                    serializer=cookie.MessageSerializer,
                )
            ]
            self.assertIn(expected, message_strings)


class BasketReportTests(TestCase):
    def test_open_report_doesnt_error(self):
        data = {
            "start_date": datetime.date(2012, 5, 1),
            "end_date": datetime.date(2012, 5, 17),
            "formatter": "CSV",
        }
        generator = reports.OpenBasketReportGenerator(**data)
        generator.generate()

    def test_submitted_report_doesnt_error(self):
        data = {
            "start_date": datetime.date(2012, 5, 1),
            "end_date": datetime.date(2012, 5, 17),
            "formatter": "CSV",
        }
        generator = reports.SubmittedBasketReportGenerator(**data)
        generator.generate()


class SavedBasketTests(WebTestCase):
    csrf_checks = False

    def test_moving_to_saved_basket_creates_new(self):
        self.user = factories.UserFactory()
        product = factories.ProductFactory()
        basket = factories.BasketFactory(owner=self.user)
        basket.add_product(product)

        response = self.get(reverse("basket:summary"))
        formset = response.context["formset"]
        form = formset.forms[0]

        data = {
            formset.add_prefix("INITIAL_FORMS"): 1,
            formset.add_prefix("TOTAL_FORMS"): 1,
            formset.add_prefix("MIN_FORMS"): 0,
            formset.add_prefix("MAX_NUM_FORMS"): 1,
            form.add_prefix("id"): form.instance.pk,
            form.add_prefix("quantity"): form.initial["quantity"],
            form.add_prefix("save_for_later"): True,
        }
        response = self.post(reverse("basket:summary"), params=data)

        self.assertRedirects(response, reverse("basket:summary"))
        self.assertFalse(Basket.open.get(pk=basket.pk).lines.exists())
        self.assertEqual(
            Basket.saved.get(owner=self.user).lines.get(product=product).quantity, 1
        )

    def test_moving_to_saved_basket_updates_existing(self):
        self.user = factories.UserFactory()
        product = factories.ProductFactory()

        basket = factories.BasketFactory(owner=self.user)
        basket.add_product(product)

        saved_basket = factories.BasketFactory(owner=self.user, status=Basket.SAVED)
        saved_basket.add_product(product)

        response = self.get(reverse("basket:summary"))
        formset = response.context["formset"]
        form = formset.forms[0]

        data = {
            formset.add_prefix("INITIAL_FORMS"): 1,
            formset.add_prefix("TOTAL_FORMS"): 1,
            formset.add_prefix("MIN_FORMS"): 0,
            formset.add_prefix("MAX_NUM_FORMS"): 1,
            form.add_prefix("id"): form.instance.pk,
            form.add_prefix("quantity"): form.initial["quantity"],
            form.add_prefix("save_for_later"): True,
        }
        response = self.post(reverse("basket:summary"), params=data)

        self.assertRedirects(response, reverse("basket:summary"))
        self.assertFalse(Basket.open.get(pk=basket.pk).lines.exists())
        self.assertEqual(
            Basket.saved.get(pk=saved_basket.pk).lines.get(product=product).quantity, 2
        )

    def test_moving_from_saved_basket(self):
        self.user = User.objects.create_user(
            username="test", password="pass", email="test@example.com"
        )
        product = create_product(price=D("10.00"), num_in_stock=2)
        basket = factories.create_basket(empty=True)
        basket.owner = self.user
        basket.save()
        add_product(basket, product=product)

        saved_basket, created = Basket.saved.get_or_create(owner=self.user)
        saved_basket.strategy = basket.strategy
        add_product(saved_basket, product=product)

        response = self.get(reverse("basket:summary"))
        saved_formset = response.context["saved_formset"]
        saved_form = saved_formset.forms[0]

        data = {
            saved_formset.add_prefix("INITIAL_FORMS"): 1,
            saved_formset.add_prefix("MAX_NUM_FORMS"): 1,
            saved_formset.add_prefix("TOTAL_FORMS"): 1,
            saved_form.add_prefix("id"): saved_form.initial["id"],
            saved_form.add_prefix("move_to_basket"): True,
        }
        response = self.post(reverse("basket:saved"), params=data)
        self.assertEqual(
            Basket.open.get(id=basket.id).lines.get(product=product).quantity, 2
        )
        self.assertRedirects(response, reverse("basket:summary"))

    def test_moving_from_saved_basket_more_than_stocklevel_raises(self):
        self.user = User.objects.create_user(
            username="test", password="pass", email="test@example.com"
        )
        product = create_product(price=D("10.00"), num_in_stock=1)
        basket, created = Basket.open.get_or_create(owner=self.user)
        add_product(basket, product=product)

        saved_basket, created = Basket.saved.get_or_create(owner=self.user)
        add_product(saved_basket, product=product)

        response = self.get(reverse("basket:summary"))
        saved_formset = response.context["saved_formset"]
        saved_form = saved_formset.forms[0]

        data = {
            saved_formset.add_prefix("INITIAL_FORMS"): 1,
            saved_formset.add_prefix("MAX_NUM_FORMS"): 1,
            saved_formset.add_prefix("TOTAL_FORMS"): 1,
            saved_form.add_prefix("id"): saved_form.initial["id"],
            saved_form.add_prefix("move_to_basket"): True,
        }
        response = self.post(reverse("basket:saved"), params=data)
        # we can't add more than stock level into basket
        self.assertEqual(
            Basket.open.get(id=basket.id).lines.get(product=product).quantity, 1
        )
        self.assertRedirects(response, reverse("basket:summary"))


class BasketFormSetTests(WebTestCase):
    csrf_checks = False

    def test_formset_with_removed_line(self):
        products = [create_product() for i in range(3)]
        basket = factories.create_basket(empty=True)
        basket.owner = self.user
        basket.save()

        add_product(basket, product=products[0])
        add_product(basket, product=products[1])
        add_product(basket, product=products[2])
        response = self.get(reverse("basket:summary"))
        formset = response.context["formset"]
        self.assertEqual(len(formset.forms), 3)

        basket.lines.filter(product=products[0]).delete()

        management_form = formset.management_form
        data = {
            formset.add_prefix("INITIAL_FORMS"): management_form.initial[
                "INITIAL_FORMS"
            ],
            formset.add_prefix("MAX_NUM_FORMS"): management_form.initial[
                "MAX_NUM_FORMS"
            ],
            formset.add_prefix("TOTAL_FORMS"): management_form.initial["TOTAL_FORMS"],
            "form-0-quantity": 1,
            "form-0-id": formset.forms[0].instance.id,
            "form-1-quantity": 2,
            "form-1-id": formset.forms[1].instance.id,
            "form-2-quantity": 2,
            "form-2-id": formset.forms[2].instance.id,
        }
        response = self.post(reverse("basket:summary"), params=data)
        self.assertEqual(response.status_code, 302)
        formset = response.follow().context["formset"]
        self.assertEqual(len(formset.forms), 2)
        self.assertEqual(len(formset.forms_with_instances), 2)
        self.assertEqual(basket.lines.all()[0].quantity, 2)
        self.assertEqual(basket.lines.all()[1].quantity, 2)

    def test_invalid_formset_with_removed_line(self):
        products = [create_product() for i in range(3)]
        basket = factories.create_basket(empty=True)
        basket.owner = self.user
        basket.save()

        add_product(basket, product=products[0])
        add_product(basket, product=products[1])
        add_product(basket, product=products[2])
        response = self.get(reverse("basket:summary"))
        formset = response.context["formset"]
        self.assertEqual(len(formset.forms), 3)

        basket.lines.filter(product=products[0]).delete()

        stockrecord = products[1].stockrecords.first()
        stockrecord.num_in_stock = 0
        stockrecord.save()

        management_form = formset.management_form
        data = {
            formset.add_prefix("INITIAL_FORMS"): management_form.initial[
                "INITIAL_FORMS"
            ],
            formset.add_prefix("MIN_NUM_FORMS"): management_form.initial[
                "MIN_NUM_FORMS"
            ],
            formset.add_prefix("MAX_NUM_FORMS"): management_form.initial[
                "MAX_NUM_FORMS"
            ],
            formset.add_prefix("TOTAL_FORMS"): management_form.initial["TOTAL_FORMS"],
            "form-0-quantity": 1,
            "form-0-id": formset.forms[0].instance.id,
            "form-1-quantity": 2,
            "form-1-id": formset.forms[1].instance.id,
            "form-2-quantity": 2,
            "form-2-id": formset.forms[2].instance.id,
        }
        response = self.post(reverse("basket:summary"), params=data)
        self.assertEqual(response.status_code, 200)
        formset = response.context["formset"]
        self.assertEqual(len(formset.forms), 2)
        self.assertEqual(len(formset.forms_with_instances), 2)
        self.assertEqual(basket.lines.all()[0].quantity, 1)
        self.assertEqual(basket.lines.all()[1].quantity, 1)

    def test_deleting_valid_line_with_other_valid_line(self):
        product_1 = create_product()
        product_2 = create_product()

        basket = factories.create_basket(empty=True)
        basket.owner = self.user
        basket.save()
        add_product(basket, product=product_1)
        add_product(basket, product=product_2)

        response = self.get(reverse("basket:summary"))
        formset = response.context["formset"]
        self.assertEqual(len(formset.forms), 2)

        data = {
            formset.add_prefix("TOTAL_FORMS"): formset.management_form.initial[
                "TOTAL_FORMS"
            ],
            formset.add_prefix("INITIAL_FORMS"): formset.management_form.initial[
                "INITIAL_FORMS"
            ],
            formset.add_prefix("MIN_NUM_FORMS"): formset.management_form.initial[
                "MIN_NUM_FORMS"
            ],
            formset.add_prefix("MAX_NUM_FORMS"): formset.management_form.initial[
                "MAX_NUM_FORMS"
            ],
            formset.forms[0].add_prefix("id"): formset.forms[0].instance.pk,
            formset.forms[0].add_prefix("quantity"): formset.forms[0].instance.quantity,
            formset.forms[0].add_prefix("DELETE"): "on",
            formset.forms[1].add_prefix("id"): formset.forms[1].instance.pk,
            formset.forms[1].add_prefix("quantity"): formset.forms[1].instance.quantity,
        }
        response = self.post(reverse("basket:summary"), params=data, xhr=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["formset"].forms), 1)
        self.assertFalse(
            response.context["formset"].is_bound
        )  # new formset is rendered
        self.assertEqual(basket.lines.count(), 1)
        self.assertEqual(basket.lines.all()[0].quantity, 1)

    def test_deleting_valid_line_with_other_invalid_line(self):
        product_1 = create_product()
        product_2 = create_product()

        basket = factories.create_basket(empty=True)
        basket.owner = self.user
        basket.save()
        add_product(basket, product=product_1)
        add_product(basket, product=product_2)

        response = self.get(reverse("basket:summary"))
        formset = response.context["formset"]
        self.assertEqual(len(formset.forms), 2)

        # Render product for other line out of stock
        product_2.stockrecords.update(num_in_stock=0)

        data = {
            formset.add_prefix("TOTAL_FORMS"): formset.management_form.initial[
                "TOTAL_FORMS"
            ],
            formset.add_prefix("INITIAL_FORMS"): formset.management_form.initial[
                "INITIAL_FORMS"
            ],
            formset.add_prefix("MIN_NUM_FORMS"): formset.management_form.initial[
                "MIN_NUM_FORMS"
            ],
            formset.add_prefix("MAX_NUM_FORMS"): formset.management_form.initial[
                "MAX_NUM_FORMS"
            ],
            formset.forms[0].add_prefix("id"): formset.forms[0].instance.pk,
            formset.forms[0].add_prefix("quantity"): formset.forms[0].instance.quantity,
            formset.forms[0].add_prefix("DELETE"): "on",
            formset.forms[1].add_prefix("id"): formset.forms[1].instance.pk,
            formset.forms[1].add_prefix("quantity"): formset.forms[1].instance.quantity,
        }
        response = self.post(reverse("basket:summary"), params=data, xhr=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["formset"].forms), 1)
        self.assertTrue(
            response.context["formset"].is_bound
        )  # formset with errors is rendered
        self.assertFalse(response.context["formset"].forms[0].is_valid())
        self.assertEqual(basket.lines.count(), 1)
        self.assertEqual(basket.lines.all()[0].quantity, 1)

    def test_deleting_invalid_line_with_other_valid_line(self):
        product_1 = create_product()
        product_2 = create_product()

        basket = factories.create_basket(empty=True)
        basket.owner = self.user
        basket.save()
        add_product(basket, product=product_1)
        add_product(basket, product=product_2)

        response = self.get(reverse("basket:summary"))
        formset = response.context["formset"]
        self.assertEqual(len(formset.forms), 2)

        # Render product for to-be-deleted line out of stock
        product_1.stockrecords.update(num_in_stock=0)

        data = {
            formset.add_prefix("TOTAL_FORMS"): formset.management_form.initial[
                "TOTAL_FORMS"
            ],
            formset.add_prefix("INITIAL_FORMS"): formset.management_form.initial[
                "INITIAL_FORMS"
            ],
            formset.add_prefix("MIN_NUM_FORMS"): formset.management_form.initial[
                "MIN_NUM_FORMS"
            ],
            formset.add_prefix("MAX_NUM_FORMS"): formset.management_form.initial[
                "MAX_NUM_FORMS"
            ],
            formset.forms[0].add_prefix("id"): formset.forms[0].instance.pk,
            formset.forms[0].add_prefix("quantity"): formset.forms[0].instance.quantity,
            formset.forms[0].add_prefix("DELETE"): "on",
            formset.forms[1].add_prefix("id"): formset.forms[1].instance.pk,
            formset.forms[1].add_prefix("quantity"): formset.forms[1].instance.quantity,
        }
        response = self.post(reverse("basket:summary"), params=data, xhr=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["formset"].forms), 1)
        self.assertFalse(
            response.context["formset"].is_bound
        )  # new formset is rendered
        self.assertEqual(basket.lines.count(), 1)
        self.assertEqual(basket.lines.all()[0].quantity, 1)

    def test_deleting_invalid_line_with_other_invalid_line(self):
        product_1 = create_product()
        product_2 = create_product()

        basket = factories.create_basket(empty=True)
        basket.owner = self.user
        basket.save()
        add_product(basket, product=product_1)
        add_product(basket, product=product_2)

        response = self.get(reverse("basket:summary"))
        formset = response.context["formset"]
        self.assertEqual(len(formset.forms), 2)

        # Render products for both lines out of stock
        product_1.stockrecords.update(num_in_stock=0)
        product_2.stockrecords.update(num_in_stock=0)

        data = {
            formset.add_prefix("TOTAL_FORMS"): formset.management_form.initial[
                "TOTAL_FORMS"
            ],
            formset.add_prefix("INITIAL_FORMS"): formset.management_form.initial[
                "INITIAL_FORMS"
            ],
            formset.add_prefix("MIN_NUM_FORMS"): formset.management_form.initial[
                "MIN_NUM_FORMS"
            ],
            formset.add_prefix("MAX_NUM_FORMS"): formset.management_form.initial[
                "MAX_NUM_FORMS"
            ],
            formset.forms[0].add_prefix("id"): formset.forms[0].instance.pk,
            formset.forms[0].add_prefix("quantity"): formset.forms[0].instance.quantity,
            formset.forms[0].add_prefix("DELETE"): "on",
            formset.forms[1].add_prefix("id"): formset.forms[1].instance.pk,
            formset.forms[1].add_prefix("quantity"): formset.forms[1].instance.quantity,
        }
        response = self.post(reverse("basket:summary"), params=data, xhr=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["formset"].forms), 1)
        self.assertTrue(
            response.context["formset"].is_bound
        )  # formset with errors is rendered
        self.assertFalse(response.context["formset"].forms[0].is_valid())
        self.assertEqual(basket.lines.count(), 1)
        self.assertEqual(basket.lines.all()[0].quantity, 1)
