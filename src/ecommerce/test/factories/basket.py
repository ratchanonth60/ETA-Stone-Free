import factory
from factory.django import DjangoModelFactory
from oscar.core.loading import get_model

from ecommerce.apps.partner.strategy import Selector

__all__ = ["BasketFactory", "BasketLineAttributeFactory"]


class BasketFactory(DjangoModelFactory):
    @factory.post_generation
    def set_strategy(self, create, extracted, **kwargs):
        # Load default strategy (without a user/request)
        self.strategy = Selector().strategy()

    class Meta:
        model = get_model("basket", "Basket")


class BasketLineAttributeFactory(DjangoModelFactory):
    option = factory.SubFactory("ecommerce.test.factories.OptionFactory")

    class Meta:
        model = get_model("basket", "LineAttribute")
