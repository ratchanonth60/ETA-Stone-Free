import datetime
from decimal import ROUND_DOWN
from decimal import Decimal as D
from unittest import mock

from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.timezone import now
from oscar.apps.offer import applicator, custom, results, utils
from oscar.core.loading import get_model

from ecommerce.apps.catalogue import models as catalogue_models
from ecommerce.apps.offer import models, reports
from ecommerce.apps.partner.strategy import Selector
from ecommerce.test import factories
from ecommerce.test.basket import add_product, add_products
from ecommerce.test.model_tests_app.models import CustomBenefitModel, CustomConditionModel
from ecommerce.test.testcases import TestCase

from oscar.apps.offer.benefits import *  # noqa isort:skip


Voucher = get_model("voucher", "Voucher")


class TestOffersWithCountCondition(TestCase):
    def setUp(self):
        super().setUp()

        self.basket = factories.create_basket(empty=True)

        # Create range and add one product to it.
        rng = factories.RangeFactory(name="All products", includes_all_products=True)
        self.product = factories.ProductFactory()
        rng.add_product(self.product)

        # Create a non-exclusive offer #1.
        condition1 = factories.ConditionFactory(range=rng, value=D("1"))
        benefit1 = factories.BenefitFactory(range=rng, value=D("10"))
        self.offer1 = factories.ConditionalOfferFactory(
            condition=condition1,
            benefit=benefit1,
            start_datetime=now(),
            name="Test offer #1",
            exclusive=False,
        )

        # Create a non-exclusive offer #2.
        condition2 = factories.ConditionFactory(range=rng, value=D("1"))
        benefit2 = factories.BenefitFactory(range=rng, value=D("5"))
        self.offer2 = factories.ConditionalOfferFactory(
            condition=condition2,
            benefit=benefit2,
            start_datetime=now(),
            name="Test offer #2",
            exclusive=False,
        )

    def add_product(self):
        self.basket.add_product(self.product)
        self.basket.strategy = Selector().strategy()
        applicator.Applicator().apply(self.basket)

    def assertOffersApplied(self, offers):
        applied_offers = self.basket.applied_offers()
        self.assertEqual(len(offers), len(applied_offers))
        for offer in offers:
            self.assertIn(offer.id, applied_offers, msg=offer)

    def test_both_non_exclusive_offers_are_applied(self):
        self.add_product()
        self.assertOffersApplied([self.offer1, self.offer2])


class TestConditionalOfferDelete(TestCase):
    def test_benefits_and_conditions_deleted(self):
        offer = factories.ConditionalOfferFactory()

        benefit_id = offer.benefit.id
        condition_id = offer.condition.id

        offer.delete()

        self.assertFalse(models.Condition.objects.filter(id=condition_id).exists())
        self.assertFalse(models.Benefit.objects.filter(id=benefit_id).exists())

    def test_for_multiple_offers_benefits_and_conditions_not_deleted(self):
        condition = factories.ConditionFactory()
        condition_id = condition.id
        benefit = factories.BenefitFactory()
        benefit_id = benefit.id

        offer1 = factories.create_offer(name="First test offer", condition=condition)
        offer2 = factories.create_offer(
            name="Second test offer", condition=condition, benefit=benefit
        )
        offer3 = factories.create_offer(name="Third test offer", benefit=benefit)

        offer1.delete()
        self.assertTrue(models.Condition.objects.filter(id=condition_id).exists())

        offer2.delete()
        self.assertFalse(models.Condition.objects.filter(id=condition_id).exists())
        self.assertTrue(models.Benefit.objects.filter(id=benefit_id).exists())

        offer3.delete()
        self.assertFalse(models.Benefit.objects.filter(id=benefit_id).exists())

    def test_custom_benefits_and_conditions_not_deleted(self):
        condition = custom.create_condition(CustomConditionModel)
        condition_id = condition.id

        benefit = custom.create_benefit(CustomBenefitModel)
        benefit_id = benefit.id

        offer = factories.create_offer(benefit=benefit, condition=condition)
        offer.delete()

        self.assertTrue(models.Condition.objects.filter(id=condition_id).exists())
        self.assertTrue(models.Benefit.objects.filter(id=benefit_id).exists())


class TestBenefit(TestCase):
    def test_default_rounding(self):
        benefit = models.Benefit()

        decimal = D(10.0570)

        self.assertEqual(
            benefit.round(decimal), decimal.quantize(D("0.01"), ROUND_DOWN)
        )


class TestWholeSiteRange(TestCase):
    def setUp(self):
        self.range = models.Range.objects.create(
            name="All products", includes_all_products=True
        )
        self.prod = factories.create_product()

    def test_all_products_range(self):
        self.assertTrue(self.range.contains_product(self.prod))
        self.assertIn(self.range, models.Range.objects.contains_product(self.prod))

    def test_all_products_includes_child_products(self):
        child_product = factories.create_product(structure="child", parent=self.prod)
        self.assertTrue(child_product in self.range.all_products())

    def test_whitelisting(self):
        self.range.add_product(self.prod)
        self.assertTrue(self.range.contains_product(self.prod))
        self.assertIn(self.prod, self.range.all_products())

    def test_blacklisting(self):
        self.range.excluded_products.add(self.prod)
        self.assertFalse(self.range.contains_product(self.prod))
        self.assertNotIn(self.prod, self.range.all_products())


class TestChildRange(TestCase):
    def setUp(self):
        self.range = models.Range.objects.create(
            name="Child-specific range", includes_all_products=False
        )
        self.parent = factories.create_product(structure="parent")
        self.child1 = factories.create_product(structure="child", parent=self.parent)
        self.child2 = factories.create_product(structure="child", parent=self.parent)
        self.range.add_product(self.child1)

    def test_includes_child(self):
        self.assertTrue(self.range.contains_product(self.child1))

    def test_does_not_include_parent(self):
        self.assertFalse(self.range.contains_product(self.parent))

    def test_does_not_include_sibling(self):
        self.assertFalse(self.range.contains_product(self.child2))

    def test_parent_with_child_exception(self):
        self.range.add_product(self.parent)
        self.range.remove_product(self.child1)
        self.assertTrue(self.range.contains_product(self.parent))
        self.assertTrue(self.range.contains_product(self.child2))
        self.assertFalse(self.range.contains_product(self.child1))


class TestParentRange(TestCase):
    def setUp(self):
        self.range = models.Range.objects.create(
            name="Parent-specific range", includes_all_products=False
        )
        self.parent = factories.create_product(structure="parent")
        self.child1 = factories.create_product(structure="child", parent=self.parent)
        self.child2 = factories.create_product(structure="child", parent=self.parent)

    def test_includes_all_children_when_parent_in_included_products(self):
        self.range.add_product(self.parent)
        self.assertTrue(self.range.contains_product(self.child1))
        self.assertTrue(self.range.contains_product(self.child2))

    def test_includes_all_children_when_parent_in_categories(self):
        included_category = catalogue_models.Category.add_root(name="root")
        self.range.included_categories.add(included_category)
        self.parent.categories.add(included_category)
        self.assertTrue(self.range.contains_product(self.child1))
        self.assertTrue(self.range.contains_product(self.child2))


class TestPartialRange(TestCase):
    def setUp(self):
        self.range = models.Range.objects.create(
            name="All products", includes_all_products=False
        )
        self.parent = factories.create_product(structure="parent")
        self.child = factories.create_product(structure="child", parent=self.parent)

    def test_empty_list(self):
        self.assertFalse(self.range.contains_product(self.parent))
        self.assertFalse(self.range.contains_product(self.child))

    def test_included_classes(self):
        self.range.classes.add(self.parent.get_product_class())
        self.assertTrue(self.range.contains_product(self.parent))
        self.assertTrue(self.range.contains_product(self.child))

    def test_includes(self):
        self.range.add_product(self.parent)
        self.assertTrue(self.range.contains_product(self.parent))
        self.assertTrue(self.range.contains_product(self.child))

    def test_included_class_with_exception(self):
        self.range.classes.add(self.parent.get_product_class())
        self.range.excluded_products.add(self.parent)
        self.assertFalse(self.range.contains_product(self.parent))
        self.assertFalse(self.range.contains_product(self.child))

    def test_included_excluded_products_in_all_products(self):
        count = 5
        included_products = [factories.create_product() for _ in range(count)]
        excluded_products = [factories.create_product() for _ in range(count)]

        for product in included_products:
            models.RangeProduct.objects.create(product=product, range=self.range)

        self.range.excluded_products.add(*excluded_products)

        all_products = self.range.all_products()
        self.assertEqual(all_products.count(), count)
        self.assertEqual(self.range.num_products(), count)

        for product in included_products:
            self.assertTrue(product in all_products)

        for product in excluded_products:
            self.assertTrue(product not in all_products)

    def test_product_classes_in_all_products(self):
        product_in_included_class = factories.create_product(product_class="123")
        included_product_class = product_in_included_class.product_class
        excluded_product_in_included_class = factories.create_product(
            product_class=included_product_class.name
        )

        self.range.classes.add(included_product_class)
        self.range.excluded_products.add(excluded_product_in_included_class)

        all_products = self.range.all_products()
        self.assertTrue(product_in_included_class in all_products)
        self.assertTrue(excluded_product_in_included_class not in all_products)

        self.assertEqual(self.range.num_products(), 1)

    def test_categories_in_all_products(self):
        included_category = catalogue_models.Category.add_root(name="root")
        product_in_included_category = factories.create_product()
        excluded_product_in_included_category = factories.create_product()

        catalogue_models.ProductCategory.objects.create(
            product=product_in_included_category, category=included_category
        )
        catalogue_models.ProductCategory.objects.create(
            product=excluded_product_in_included_category, category=included_category
        )

        self.range.included_categories.add(included_category)
        self.range.excluded_products.add(excluded_product_in_included_category)

        all_products = self.range.all_products()
        self.assertTrue(product_in_included_category in all_products)
        self.assertTrue(excluded_product_in_included_category not in all_products)

        self.assertEqual(self.range.num_products(), 1)

    def test_descendant_categories_in_all_products(self):
        parent_category = catalogue_models.Category.add_root(name="parent")
        child_category = parent_category.add_child(name="child")
        grand_child_category = child_category.add_child(name="grand-child")

        c_product = factories.create_product()
        gc_product = factories.create_product()

        catalogue_models.ProductCategory.objects.create(
            product=c_product, category=child_category
        )
        catalogue_models.ProductCategory.objects.create(
            product=gc_product, category=grand_child_category
        )

        self.range.included_categories.add(parent_category)

        all_products = self.range.all_products()
        self.assertTrue(c_product in all_products)
        self.assertTrue(gc_product in all_products)

        self.assertEqual(self.range.num_products(), 2)

    def test_product_duplicated_in_all_products(self):
        """Making sure product is not duplicated in range products
        it has multiple categories assigned."""

        included_category1 = catalogue_models.Category.add_root(name="cat1")
        included_category2 = catalogue_models.Category.add_root(name="cat2")
        product = factories.create_product()
        catalogue_models.ProductCategory.objects.create(
            product=product, category=included_category1
        )
        catalogue_models.ProductCategory.objects.create(
            product=product, category=included_category2
        )

        self.range.included_categories.add(included_category1)
        self.range.included_categories.add(included_category2)
        self.range.add_product(product)

        all_product_ids = list(self.range.all_products().values_list("id", flat=True))
        product_occurances_in_range = all_product_ids.count(product.id)
        self.assertEqual(product_occurances_in_range, 1)

    def test_product_remove_from_range(self):
        included_category = catalogue_models.Category.add_root(name="root")
        product = factories.create_product()
        catalogue_models.ProductCategory.objects.create(
            product=product, category=included_category
        )

        self.range.included_categories.add(included_category)
        self.range.add_product(product)

        all_products = self.range.all_products()
        self.assertTrue(product in all_products)

        self.range.remove_product(product)

        all_products = self.range.all_products()
        self.assertFalse(product in all_products)

        # Re-adding product should return it to the products range
        self.range.add_product(product)

        all_products = self.range.all_products()
        self.assertTrue(product in all_products)

    def test_range_is_reordable(self):
        product = factories.create_product()
        self.range.add_product(product)
        self.assertTrue(self.range.is_reorderable)

        included_category = catalogue_models.Category.add_root(name="root")
        catalogue_models.ProductCategory.objects.create(
            product=product, category=included_category
        )
        self.range.included_categories.add(included_category)

        self.range.invalidate_cached_queryset()
        self.assertFalse(self.range.is_reorderable)

        self.range.included_categories.remove(included_category)
        self.range.invalidate_cached_queryset()
        self.assertTrue(self.range.is_reorderable)


class TestRangeModel(TestCase):
    def test_ensures_unique_slugs_are_used(self):
        first_range = models.Range.objects.create(name="Foo")
        first_range.name = "Bar"
        first_range.save()
        models.Range.objects.create(name="Foo")


class TestRangeQuerySet(TestCase):
    def setUp(self):
        self.prod = factories.create_product()
        self.excludedprod = factories.create_product()
        self.parent = factories.create_product(structure="parent")
        self.child1 = factories.create_product(structure="child", parent=self.parent)
        self.child2 = factories.create_product(structure="child", parent=self.parent)

        self.range = models.Range.objects.create(
            name="All products", includes_all_products=True
        )
        self.range.excluded_products.add(self.excludedprod)
        self.range.excluded_products.add(self.child2)

        self.childrange = models.Range.objects.create(
            name="Child-specific range", includes_all_products=False
        )
        self.childrange.add_product(self.child1)
        self.childrange.add_product(self.prod)

    def test_contains_product(self):
        ranges = models.Range.objects.contains_product(self.prod)
        self.assertEqual(ranges.count(), 2, "Both ranges should contain the product")

    def test_excluded_product(self):
        ranges = models.Range.objects.contains_product(self.excludedprod)
        self.assertEqual(
            ranges.count(), 0, "No ranges should contain the excluded product"
        )

    def test_contains_child(self):
        ranges = models.Range.objects.contains_product(self.child1)
        self.assertEqual(
            ranges.count(), 2, "Both ranges should contain the child product"
        )

    def test_contains_parent(self):
        ranges = models.Range.objects.contains_product(self.parent)
        self.assertEqual(
            ranges.count(), 1, "One range should contain the parent product"
        )

    def test_exclude_child(self):
        ranges = models.Range.objects.contains_product(self.child2)
        self.assertEqual(
            ranges.count(),
            0,
            "None of the ranges should contain the second child, because it"
            " was excluded in the range that contains the parent.",
        )

    def test_category(self):
        parent_category = catalogue_models.Category.add_root(name="parent")
        child_category = parent_category.add_child(name="child")
        grand_child_category = child_category.add_child(name="grand-child")
        catalogue_models.ProductCategory.objects.create(
            product=self.parent, category=grand_child_category
        )

        cat_range = models.Range.objects.create(
            name="category range", includes_all_products=False
        )
        cat_range.included_categories.add(parent_category)
        ranges = models.Range.objects.contains_product(self.parent)
        self.assertEqual(
            ranges.count(),
            2,
            "Since the parent category is part of the range, There should be 2 "
            "ranges containing the parent product, which is in a subcategory",
        )
        self.assertIn(
            cat_range,
            ranges,
            "The range containing the parent category of the parent product, should be selected",
        )

        ranges = models.Range.objects.contains_product(self.child2)
        self.assertEqual(
            ranges.count(),
            1,
            "Since the parent category is part of the range, There should be 1 "
            "range containing the child2 product, whose parent is in a subcategory",
        )

        ranges = models.Range.objects.contains_product(self.child1)
        self.assertEqual(
            ranges.count(),
            3,
            "Since the parent category is part of the range, There should be 3 "
            "ranges containing the child1 product, whose parent is in a subcategory",
        )
        cat_range.excluded_products.add(self.child2)
        ranges = models.Range.objects.contains_product(self.child2)
        self.assertEqual(
            ranges.count(),
            0,
            "No ranges should contain child2 after explicitly removing it from the only range that contained it",
        )


class TestOfferReportGenerator(TestCase):
    def test_generate_csv_no_filter(self):
        generator = reports.OfferReportGenerator(formatter="CSV")
        generator.generate()

    def test_generate_csv_start_and_end_date(self):
        start_date = now() - datetime.timedelta(days=28)
        end_date = now() + datetime.timedelta(days=28)

        generator = reports.OfferReportGenerator(
            start_date=start_date, end_date=end_date, formatter="CSV"
        )
        generator.generate()


class TestAPercentageDiscountAppliedWithCountCondition(TestCase):
    def setUp(self):
        range = models.Range.objects.create(
            name="All products", includes_all_products=True
        )
        self.condition = models.CountConditionModify(
            range=range, type=models.Condition.COUNT, value=2
        )
        self.benefit = models.PercentageDiscountBenefitModify(
            range=range, type=models.Benefit.PERCENTAGE, value=20
        )
        self.offer = models.ConditionalOffer(
            offer_type=models.ConditionalOffer.SITE,
            condition=self.condition,
            benefit=self.benefit,
        )
        self.basket = factories.create_basket(empty=True)

    def test_applies_correctly_to_empty_basket(self):
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(D("0.00"), result.discount)
        self.assertEqual(0, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_basket_with_no_discountable_products(self):
        product = factories.create_product(is_discountable=False)
        add_product(self.basket, D("12.00"), 2, product=product)
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(D("0.00"), result.discount)
        self.assertEqual(0, self.basket.num_items_with_discount)
        self.assertEqual(2, self.basket.num_items_without_discount)

    def test_applies_correctly_to_basket_which_matches_condition(self):
        add_product(self.basket, D("12.00"), 2)
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(2 * D("12.00") * D("0.2"), result.discount)
        self.assertEqual(2, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_basket_which_exceeds_condition(self):
        add_product(self.basket, D("12.00"), 3)
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(3 * D("12.00") * D("0.2"), result.discount)
        self.assertEqual(3, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)


class TestAPercentageDiscountWithMaxItemsSetAppliedWithCountCondition(TestCase):
    def setUp(self):
        range = models.Range.objects.create(
            name="All products", includes_all_products=True
        )
        self.condition = models.CountConditionModify(
            range=range, type=models.Condition.COUNT, value=2
        )
        self.benefit = models.PercentageDiscountBenefitModify(
            range=range, type=models.Benefit.PERCENTAGE, value=20, max_affected_items=1
        )
        self.offer = models.ConditionalOffer(
            offer_type=models.ConditionalOffer.SITE,
            condition=self.condition,
            benefit=self.benefit,
        )
        self.basket = factories.create_basket(empty=True)

    def test_applies_correctly_to_empty_basket(self):
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(D("0.00"), result.discount)
        self.assertEqual(0, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_basket_which_matches_condition(self):
        add_product(self.basket, D("12.00"), 2)
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(1 * D("12.00") * D("0.2"), result.discount)
        self.assertEqual(1, self.basket.num_items_with_discount)
        self.assertEqual(1, self.basket.num_items_without_discount)

    def test_applies_correctly_to_basket_which_exceeds_condition(self):
        add_products(self.basket, [(D("12.00"), 2), (D("20.00"), 2)])
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(1 * D("12.00") * D("0.2"), result.discount)
        # Should only consume the condition products
        self.assertEqual(1, self.basket.num_items_with_discount)
        self.assertEqual(3, self.basket.num_items_without_discount)


class TestAPercentageDiscountAppliedWithValueCondition(TestCase):
    def setUp(self):
        range = models.Range.objects.create(
            name="All products", includes_all_products=True
        )
        self.condition = models.ValueConditionModify.objects.create(
            range=range, type=models.Condition.VALUE, value=D("10.00")
        )
        self.benefit = models.PercentageDiscountBenefitModify.objects.create(
            range=range, type=models.Benefit.PERCENTAGE, value=20
        )
        self.offer = models.ConditionalOffer(
            offer_type=models.ConditionalOffer.SITE,
            condition=self.condition,
            benefit=self.benefit,
        )

        self.basket = factories.create_basket(empty=True)

    def test_applies_correctly_to_empty_basket(self):
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(D("0.00"), result.discount)
        self.assertEqual(0, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_basket_which_matches_condition(self):
        add_product(self.basket, D("5.00"), 2)
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(2 * D("5.00") * D("0.2"), result.discount)
        self.assertEqual(2, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_basket_which_exceeds_condition_but_matches_on_boundary(
        self,
    ):
        add_product(self.basket, D("5.00"), 3)
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(3 * D("5.00") * D("0.2"), result.discount)
        self.assertEqual(3, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_basket_which_exceeds_condition(self):
        add_product(self.basket, D("4.00"), 3)
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(3 * D("4.00") * D("0.2"), result.discount)
        self.assertEqual(3, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)


class TestAPercentageDiscountWithMaxItemsSetAppliedWithValueCondition(TestCase):
    def setUp(self):
        range = models.Range.objects.create(
            name="All products", includes_all_products=True
        )
        self.condition = models.ValueConditionModify.objects.create(
            range=range, type=models.Condition.VALUE, value=D("10.00")
        )
        self.benefit = models.PercentageDiscountBenefitModify.objects.create(
            range=range, type=models.Benefit.PERCENTAGE, value=20, max_affected_items=1
        )
        self.offer = models.ConditionalOffer(
            offer_type=models.ConditionalOffer.SITE,
            condition=self.condition,
            benefit=self.benefit,
        )
        self.basket = factories.create_basket(empty=True)

    def test_applies_correctly_to_empty_basket(self):
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(D("0.00"), result.discount)
        self.assertEqual(0, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_basket_which_matches_condition(self):
        add_product(self.basket, D("5.00"), 2)
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(1 * D("5.00") * D("0.2"), result.discount)
        self.assertEqual(1, self.basket.num_items_with_discount)
        self.assertEqual(1, self.basket.num_items_without_discount)

    def test_applies_correctly_to_basket_which_exceeds_condition_but_matches_on_boundary(
        self,
    ):
        add_product(self.basket, D("5.00"), 3)
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(1 * D("5.00") * D("0.2"), result.discount)
        self.assertEqual(1, self.basket.num_items_with_discount)
        self.assertEqual(2, self.basket.num_items_without_discount)

    def test_applies_correctly_to_basket_which_exceeds_condition(self):
        add_product(self.basket, D("4.00"), 3)
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(1 * D("4.00") * D("0.2"), result.discount)
        self.assertEqual(1, self.basket.num_items_with_discount)
        self.assertEqual(2, self.basket.num_items_without_discount)


class TestAPercentageDiscountBenefit(TestCase):
    def test_requires_a_benefit_value(self):
        rng = models.Range.objects.create(name="", includes_all_products=True)
        benefit = models.Benefit(type=models.Benefit.PERCENTAGE, range=rng)
        with self.assertRaises(ValidationError):
            benefit.clean()

    def test_requires_a_range(self):
        benefit = models.Benefit(type=models.Benefit.PERCENTAGE, value=40)
        with self.assertRaises(ValidationError):
            benefit.clean()


class TestAFixedPriceDiscountAppliedWithCountCondition(TestCase):
    def setUp(self):
        range = models.Range.objects.create(
            name="All products", includes_all_products=True
        )
        self.condition = models.CountConditionModify.objects.create(
            range=range, type=models.Condition.COUNT, value=3
        )
        self.benefit = models.FixedPriceBenefitModify.objects.create(
            range=range, type=models.Benefit.FIXED_PRICE, value=D("20.00")
        )
        self.offer = mock.Mock()
        self.basket = factories.create_basket(empty=True)

    def test_applies_correctly_to_empty_basket(self):
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(D("0.00"), result.discount)
        self.assertEqual(0, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)

    def test_applies_correctly_to_basket_which_is_worth_less_than_value(self):
        add_product(self.basket, D("6.00"), 3)
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(D("0.00"), result.discount)
        self.assertEqual(0, self.basket.num_items_with_discount)
        self.assertEqual(3, self.basket.num_items_without_discount)

    def test_applies_correctly_to_basket_which_is_worth_the_same_as_value(self):
        add_product(self.basket, D("5.00"), 4)
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(D("0.00"), result.discount)
        self.assertEqual(0, self.basket.num_items_with_discount)
        self.assertEqual(4, self.basket.num_items_without_discount)

    def test_applies_correctly_to_basket_which_is_more_than_value(self):
        add_product(self.basket, D("8.00"), 4)
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(D("4.00"), result.discount)
        self.assertEqual(3, self.basket.num_items_with_discount)
        self.assertEqual(1, self.basket.num_items_without_discount)

    def test_rounding_error_for_multiple_products(self):
        add_products(self.basket, [(D("7.00"), 1), (D("7.00"), 1), (D("7.00"), 1)])
        result = self.benefit.apply(self.basket, self.condition, self.offer)
        self.assertEqual(D("1.00"), result.discount)
        # Make sure discount together is the same as final discount
        # Rounding error would return 0.99 instead 1.00
        cumulative_discount = sum(
            line.discount_value for line in self.basket.all_lines()
        )
        self.assertEqual(result.discount, cumulative_discount)
        self.assertEqual(3, self.basket.num_items_with_discount)
        self.assertEqual(0, self.basket.num_items_without_discount)


class TestACountConditionWithPercentageDiscount(TestCase):
    def setUp(self):
        range = models.Range.objects.create(
            name="All products", includes_all_products=True
        )
        condition = models.CountConditionModify.objects.create(
            range=range, type=models.Condition.COUNT, value=3
        )
        benefit = models.PercentageDiscountBenefitModify.objects.create(
            range=range, type=models.Benefit.PERCENTAGE, value=20, max_affected_items=1
        )
        self.offer = models.ConditionalOffer(
            name="Test",
            offer_type=models.ConditionalOffer.SITE,
            condition=condition,
            benefit=benefit,
        )

    def test_consumes_correct_number_of_products_for_3_product_basket(self):
        basket = factories.create_basket(empty=True)
        add_product(basket, D("1"), 3)

        self.assertTrue(self.offer.is_condition_satisfied(basket))
        discount = self.offer.apply_benefit(basket)
        self.assertTrue(discount.discount > 0)
        self.assertEqual(1, basket.num_items_with_discount)
        self.assertEqual(2, basket.num_items_without_discount)
        self.assertFalse(self.offer.is_condition_satisfied(basket))

    def test_consumes_correct_number_of_products_for_4_product_basket(self):
        basket = factories.create_basket(empty=True)
        add_products(basket, [(D("1"), 2), (D("1"), 2)])

        self.assertTrue(self.offer.is_condition_satisfied(basket))
        discount = self.offer.apply_benefit(basket)
        self.assertTrue(discount.discount > 0)
        self.assertEqual(1, basket.num_items_with_discount)
        self.assertEqual(3, basket.num_items_without_discount)
        self.assertTrue(self.offer.is_condition_satisfied(basket))

    def test_consumes_correct_number_of_products_for_6_product_basket(self):
        basket = factories.create_basket(empty=True)
        add_products(basket, [(D("1"), 3), (D("1"), 3)])
        self.assertTrue(self.offer.is_condition_satisfied(basket))
        # First application
        discount = self.offer.apply_benefit(basket)
        self.assertTrue(discount.discount > 0)
        self.assertEqual(1, basket.num_items_with_discount)
        self.assertEqual(5, basket.num_items_without_discount)

        # Second application (no additional discounts)
        discount = self.offer.apply_benefit(basket)
        self.assertFalse(discount.discount > 0)
        self.assertEqual(1, basket.num_items_with_discount)
        self.assertEqual(5, basket.num_items_without_discount)


class TestPriorityOffers(TestCase):
    def test_site_offers_are_ordered(self):
        factories.create_offer(name="A", priority=0)
        factories.create_offer(name="B", priority=7)
        factories.create_offer(name="C", priority=5)
        factories.create_offer(name="D", priority=7)
        factories.create_offer(name="E", priority=1)

        offers = utils.Applicator().get_site_offers()
        ordered_names = [offer.name for offer in offers]
        self.assertEqual(["B", "D", "C", "E", "A"], ordered_names)

    def test_basket_offers_are_ordered(self):
        voucher = Voucher.objects.create(
            name="Test voucher",
            code="test",
            usage=Voucher.MULTI_USE,
            start_datetime=timezone.now(),
            end_datetime=timezone.now() + datetime.timedelta(days=12),
        )

        voucher.offers.set(
            [
                factories.create_offer(name="A", priority=0),
                factories.create_offer(name="B", priority=7),
                factories.create_offer(name="C", priority=5),
                factories.create_offer(name="D", priority=7),
                factories.create_offer(name="E", priority=1),
            ]
        )

        basket = factories.create_basket()
        user = mock.Mock()

        # Apply voucher to basket
        basket.vouchers.add(voucher)

        offers = utils.Applicator().get_basket_offers(basket, user)
        ordered_names = [offer.name for offer in offers]
        self.assertEqual(["B", "D", "C", "E", "A"], ordered_names)


class TestOfferApplicationsObject(TestCase):
    def setUp(self):
        self.applications = results.OfferApplications()
        self.offer = models.ConditionalOffer()

    def test_is_countable(self):
        self.assertEqual(0, len(self.applications))

    def test_can_filter_shipping_discounts(self):
        result = models.ShippingDiscount()
        self.applications.add(self.offer, result)
        self.assertEqual(1, len(self.applications.shipping_discounts))

    def test_can_filter_offer_discounts(self):
        result = models.BasketDiscount(D("2.00"))
        self.applications.add(self.offer, result)
        self.assertEqual(1, len(self.applications.offer_discounts))

    def test_can_filter_post_order_actions(self):
        result = models.PostOrderAction("Something will happen")
        self.applications.add(self.offer, result)
        self.assertEqual(1, len(self.applications.post_order_actions))

    def test_grouped_voucher_discounts(self):
        voucher = factories.VoucherFactory()
        offer1 = factories.ConditionalOfferFactory(name="offer1")
        offer1.set_voucher(voucher)
        result1 = models.BasketDiscount(D("2.00"))

        offer2 = factories.ConditionalOfferFactory(name="offer2")
        offer2.set_voucher(voucher)
        result2 = models.BasketDiscount(D("1.00"))

        self.applications.add(offer1, result1)
        self.applications.add(offer2, result2)

        assert len(self.applications) == 2

        discounts = self.applications.grouped_voucher_discounts
        discounts = [x for x in discounts]
        assert len(discounts) == 1
        assert discounts[0]["voucher"] == voucher
        assert discounts[0]["discount"] == D("3.00")


class TestAnOfferChangesStatusWhen(TestCase):
    def setUp(self):
        ConditionalOffer = get_model("offer", "ConditionalOffer")
        self.offer = factories.ConditionalOfferFactory(offer_type=ConditionalOffer.SITE)

    def test_the_max_discount_is_exceeded(self):
        self.offer.max_discount = D("10.00")
        self.assertTrue(self.offer.is_open)

        # Now bump the total discount and save to see if the status is
        # automatically updated.
        self.offer.total_discount += D("20.00")
        self.offer.save()
        self.assertFalse(self.offer.is_open)

    def test_the_max_global_applications_is_exceeded(self):
        self.offer.max_global_applications = 5
        self.assertTrue(self.offer.is_open)

        self.offer.num_applications += 10
        self.offer.save()
        self.assertFalse(self.offer.is_open)
