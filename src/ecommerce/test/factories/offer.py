import factory
from factory.django import DjangoModelFactory
from oscar.core.loading import get_model

from ecommerce.apps.offer.models import ConditionalOffer

__all__ = [
    "RangeFactory",
    "ConditionFactory",
    "BenefitFactory",
    "ConditionalOfferFactory",
]


class RangeFactory(DjangoModelFactory):
    name = factory.Sequence(lambda n: "Range %d" % n)
    slug = factory.Sequence(lambda n: "range-%d" % n)

    class Meta:
        model = get_model("offer", "Range")

    @factory.post_generation
    def products(self, create, extracted, **kwargs):
        if not create or not extracted:
            return

        RangeProduct = get_model("offer", "RangeProduct")

        for product in extracted:
            RangeProduct.objects.create(product=product, range=self)


class BenefitFactory(DjangoModelFactory):
    type = get_model("offer", "Benefit").PERCENTAGE
    value = 10
    max_affected_items = None
    range = factory.SubFactory(RangeFactory)

    class Meta:
        model = get_model("offer", "Benefit")


class ConditionFactory(DjangoModelFactory):
    type = get_model("offer", "Condition").COUNT
    value = 10
    range = factory.SubFactory(RangeFactory)

    class Meta:
        model = get_model("offer", "Condition")


class ConditionalOfferFactory(DjangoModelFactory):
    name = factory.Sequence(lambda n: "Test offer %d" % n)
    offer_type = ConditionalOffer.SITE
    benefit = factory.SubFactory(BenefitFactory)
    condition = factory.SubFactory(ConditionFactory)

    class Meta:
        model = get_model("offer", "ConditionalOffer")
