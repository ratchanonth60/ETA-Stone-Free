import factory
from factory.django import DjangoModelFactory
from oscar.core.compat import get_user_model
from oscar.core.loading import get_model

__all__ = ["ProductAlertFactory", "UserFactory"]


class ProductAlertFactory(DjangoModelFactory):
    class Meta:
        model = get_model("customer", "ProductAlert")

    product = factory.SubFactory("ecommerce.test.factories.ProductFactory")
    user = factory.SubFactory("ecommerce.test.factories.customer.UserFactory")
    status = Meta.model.ACTIVE


class UserFactory(DjangoModelFactory):
    username = factory.Sequence(lambda n: "the_j_meister nummer %d" % n)
    email = factory.Sequence(lambda n: f"example_{n}@example.com")
    first_name = factory.Sequence(lambda n: f"john{n}")
    last_name = factory.Sequence(lambda n: f"winterbottom{n}")
    password = factory.PostGenerationMethodCall("set_password", "skelebrain")
    is_active = True
    is_superuser = False
    is_staff = False

    class Meta:
        model = get_user_model()
