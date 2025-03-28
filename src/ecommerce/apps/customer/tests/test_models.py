from oscar.core.compat import existing_user_fields

from ecommerce.apps.customer.forms import ProfileForm
from ecommerce.apps.users.models import User
from ecommerce.test.factories import ProductAlertFactory, UserFactory
from ecommerce.test.testcases import TestCase


class TestACustomUserModel(TestCase):
    def setUp(self):
        self.user_klass = User

    def test_can_be_created_without_error(self):
        try:
            self.user_klass.objects.create_user("_", "a@a.com", "pa55w0rd")
        except Exception as e:
            self.fail("Unable to create user model: %s" % e)

    def test_extra_field_is_accessible(self):
        self.assertTrue("extra_field" in existing_user_fields(["extra_field"]))
        self.assertTrue(hasattr(self.user_klass(), "extra_field"))

    def test_profile_form_doesnt_expose_extra_field(self):
        form = ProfileForm(self.user_klass())
        expected_fields = set(["first_name", "last_name", "email"])
        self.assertTrue(expected_fields == set(form.fields))

    def test_migrate_alerts_to_user(self):
        user = UserFactory(email="a@a.com")
        ProductAlertFactory(email=user.email)
        user._migrate_alerts_to_user()
        assert user.alerts.count() == 1
