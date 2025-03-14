import unittest

from django.contrib.auth import authenticate
from django.core import mail
from oscar.core.compat import get_user_model

from ecommerce.core.auth_backends import EmailBackend
from ecommerce.test.factories import UserFactory
from ecommerce.test.testcases import TestCase

User = get_user_model()


class AuthBackendTestCase(TestCase):

    def setUp(self):
        self.user = UserFactory(email='foo@example.com', is_staff=True)
        self.user.set_password('letmein')
        self.user.save()
        self.backend = EmailBackend()

    def test_authentication_method_signature_post_django_1_11(self):
        auth_result = self.backend.authenticate(None, 'foo@example.com', 'letmein')
        self.assertEqual(auth_result, self.user)

    def test_inactive_users_cannot_authenticate(self):
        self.user.is_active = False
        self.user.save()

        auth_result = self.backend.authenticate(None, 'foo@example.com', 'letmein')
        self.assertIsNone(auth_result)


class TestEmailAuthBackend(TestCase):

    def test_authenticates_multiple_users(self):
        password = 'lookmanohands'
        users = [
            User.objects.create_user(email, email, password=password)
            for email in ['user1@example.com', 'user2@example.com']]
        for created_user in users:
            user = authenticate(username=created_user.email, password=password)
            self.assertEqual(user, created_user)

    def test_authenticates_different_email_spelling(self):
        email = password = 'person@example.com'
        created_user = User.objects.create_user(
            'user1', email, password=password)

        for email_variation in [
            'Person@example.com', 'Person@EXAMPLE.COM', 'person@Example.com'
        ]:
            user = authenticate(username=email_variation, password=password)
            self.assertEqual(user, created_user)


# Skip these tests for now as they only make sense when there isn't a unique
# index on the user class.  The test suite currently uses a custom model that
# *does* have a unique index on email.  When I figure out how to swap the user
# model per test, we can re-enable this testcase.
@unittest.skip
class TestEmailAuthBackendWhenUsersShareAnEmail(TestCase):

    def test_authenticates_when_passwords_are_different(self):
        # Create two users with the same email address
        email = 'person@example.com'
        for username in ['user1', 'user2']:
            User.objects.create_user(username, email, password=username)

        user = authenticate(username=email, password='user1')
        self.assertTrue(user is not None)

    def test_rejects_when_passwords_match(self):
        # Create two users with the same email address
        email = 'person@example.com'
        for username in ['user1', 'user2']:
            User.objects.create_user(username, email, password='password')

        user = authenticate(username=email, password='password')
        self.assertTrue(user is None)

    def test_mails_admins_when_passwords_match(self):
        # Create two users with the same email address
        email = 'person@example.com'
        for username in ['user1', 'user2']:
            User.objects.create_user(username, email, password='password')

        authenticate(username=email, password='password')
        self.assertEqual(1, len(mail.outbox))
