from smtplib import SMTPException
from unittest.mock import Mock, patch

from django.core import mail

from ecommerce.apps.users.models import User
from ecommerce.core.celery.tasks.email import (
    send_password_changed_email_for_user,
    send_password_reset_email_for_user,
    send_registration_email_for_user,
)
from ecommerce.test.testcases import TestCase


class EmailTaskTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(id=1, email="test123@gmail.com")

    def test_send_registration_email_for_user(self):
        # Call the task without delay to perform it immediately
        send_registration_email_for_user(user_id=1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.user.email])

    def test_send_password_reset_email_for_user(self):
        # Call the task without delay to perform it immediately
        send_password_reset_email_for_user(user_id=1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.user.email])

    def test_send_registration_email_success(self):
        with patch(
            "ecommerce.apps.users.models.User.objects.get"
        ) as mock_get_user, patch(
            "ecommerce.core.celery.tasks.email.CustomerDispatcher"
        ) as mock_dispatcher:
            # Set up the mock user object
            mock_user = Mock(spec=User)
            mock_user.id = 1
            mock_user.email = "test123@gmail.com"
            mock_get_user.return_value = mock_user

            # Set up the mock for the CustomerDispatcher method
            mock_dispatcher_instance = mock_dispatcher.return_value
            mock_dispatcher_instance.send_registration_email_for_user.return_value = (
                None
            )

            # Call the task without delay to perform it immediately
            send_registration_email_for_user(user_id=1)

            # Assertions to check if the User was fetched and the email was sent
            mock_get_user.assert_called_once_with(id=1)
            mock_dispatcher_instance.send_registration_email_for_user.assert_called_once_with(
                mock_user, {"user": mock_user}
            )

    def test_send_registration_email_non_existent_user(self):
        with patch(
            "ecommerce.apps.users.models.User.objects.get"
        ) as mock_get_user, patch(
            "ecommerce.core.celery.tasks.email.CustomerDispatcher"
        ) as mock_dispatcher:
            # Configure the mock to raise DoesNotExist when trying to get a user
            mock_get_user.side_effect = User.DoesNotExist

            # Call the task and expect it to raise User.DoesNotExist
            with self.assertRaises(User.DoesNotExist):
                send_registration_email_for_user(
                    user_id=999
                )  # Assuming 999 is a non-existent user

            # Assert the email sending method was not called
            mock_dispatcher_instance = mock_dispatcher.return_value
            mock_dispatcher_instance.send_registration_email_for_user.assert_not_called()

    def test_send_password_reset_email_non_existent_user(self):
        with patch(
            "ecommerce.apps.users.models.User.objects.get"
        ) as mock_get_user, patch(
            "ecommerce.core.celery.tasks.email.CustomerDispatcher"
        ) as mock_dispatcher:
            """
            This test ensures that the task behaves correctly
            if it is called with a user ID that does not exist in the database.
            """
            # Configure mock to raise DoesNotExist for a non-existent user
            mock_get_user.side_effect = User.DoesNotExist

            # Expect DoesNotExist to be raised for a non-existent user
            with self.assertRaises(User.DoesNotExist):
                send_password_reset_email_for_user(
                    user_id=999
                )  # Assume 999 does not exist

            # Email sending method should not be called
            mock_dispatcher_instance = mock_dispatcher.return_value
            mock_dispatcher_instance.send_password_reset_email_for_user.assert_not_called()

    @patch("ecommerce.apps.users.models.User.objects.get")
    @patch("ecommerce.core.celery.tasks.email.CustomerDispatcher")
    def test_send_password_reset_email_success(self, mock_dispatcher, mock_get_user):
        """
        This test ensures that the password reset email is sent
        correctly when the task is executed with a valid user ID.
        """
        # Set up the mock user
        mock_user = Mock(spec=User)
        mock_user.id = 1
        mock_user.email = "test123@gmail.com"
        mock_get_user.return_value = mock_user

        # Mock the dispatcher's password reset method
        mock_dispatcher_instance = mock_dispatcher.return_value
        mock_dispatcher_instance.send_password_reset_email_for_user.return_value = None

        # Execute the task
        send_password_reset_email_for_user(user_id=1)

        # Assertions
        mock_get_user.assert_called_once_with(id=1)
        mock_dispatcher_instance.send_password_reset_email_for_user.assert_called_once_with(
            mock_user, {"user": mock_user}
        )

    @patch(
        "ecommerce.core.celery.tasks.email.send_password_reset_email_for_user.retry",
        side_effect=SMTPException,
    )
    def test_send_password_reset_email_with_retry(self, mock_retry):
        with patch(
            "ecommerce.apps.users.models.User.objects.get"
        ) as mock_get_user, patch(
            "ecommerce.core.celery.tasks.email.CustomerDispatcher"
        ) as mock_dispatcher:
            """
            This test checks the retry logic if an SMTPException is raised
            during the password reset email sending process.
            """
            # Set up mock user and SMTPException on email send
            mock_user = Mock(spec=User)
            mock_user.id = 1
            mock_user.email = "test123@gmail.com"
            mock_get_user.return_value = mock_user

            mock_dispatcher_instance = mock_dispatcher.return_value
            mock_dispatcher_instance.send_password_reset_email_for_user.side_effect = (
                SMTPException
            )

            # Expect SMTPException and a retry attempt
            with self.assertRaises(SMTPException):
                send_password_reset_email_for_user(user_id=1)

            # Verify retry was called
            mock_retry.assert_called_once()

    @patch(
        "ecommerce.core.celery.tasks.email.send_registration_email_for_user.retry",
        side_effect=SMTPException,
    )
    def test_send_registration_email_with_retry(self, mock_retry):
        with patch(
            "ecommerce.apps.users.models.User.objects.get"
        ) as mock_get_user, patch(
            "ecommerce.core.celery.tasks.email.CustomerDispatcher"
        ) as mock_dispatcher:
            # Set up the mock user object and dispatcher to raise SMTPException
            mock_user = Mock(spec=User)
            mock_user.id = 1
            mock_user.email = "test123@gmail.com"
            mock_get_user.return_value = mock_user

            mock_dispatcher_instance = mock_dispatcher.return_value
            mock_dispatcher_instance.send_registration_email_for_user.side_effect = (
                SMTPException
            )

            # Call the task expecting it to raise SMTPException and trigger a retry
            with self.assertRaises(SMTPException):
                send_registration_email_for_user(user_id=1)

            # Assert the retry was called
            mock_retry.assert_called_once()

    @patch("ecommerce.apps.users.models.User.objects.get")
    @patch("ecommerce.core.celery.tasks.email.CustomerDispatcher")
    def test_mock_send_registration_email_for_user(
        self, mock_dispatcher, mock_get_user
    ):
        # Set up the mock user object
        mock_user = Mock(spec=User)
        mock_user.id = 1
        mock_user.email = "test123@gmail.com"
        mock_get_user.return_value = mock_user

        # Set up the mock for the CustomerDispatcher method
        mock_dispatcher_instance = mock_dispatcher.return_value
        mock_dispatcher_instance.send_registration_email_for_user.return_value = None

        # Call the task without delay to perform it immediately
        send_registration_email_for_user(user_id=1)

        # Assertions to check if the User was fetched and the email was sent
        mock_get_user.assert_called_once_with(id=1)
        mock_dispatcher_instance.send_registration_email_for_user.assert_called_once_with(
            mock_user, {"user": mock_user}
        )

    @patch(
        "ecommerce.core.celery.tasks.email.send_registration_email_for_user.retry",
        side_effect=SMTPException,
    )
    @patch("ecommerce.apps.users.models.User.objects.get")
    @patch("ecommerce.core.celery.tasks.email.CustomerDispatcher")
    def test_mock_send_registration_email_failure(
        self, mock_dispatcher, mock_get_user, mock_retry
    ):
        # Set up the mock user object
        mock_user = Mock(spec=User)
        mock_user.id = 1
        mock_user.email = "test123@gmail.com"
        mock_get_user.return_value = mock_user

        # Simulate an SMTPException when sending an email
        mock_dispatcher_instance = mock_dispatcher.return_value
        mock_dispatcher_instance.send_registration_email_for_user.side_effect = (
            SMTPException
        )

        # Attempt to send the email, which we expect to fail
        with self.assertRaises(SMTPException):
            send_registration_email_for_user(user_id=1)

        # Check if the task tried to retry the operation
        mock_retry.assert_called_once()

    @patch(
        "ecommerce.core.celery.tasks.email.send_password_changed_email_for_user.retry",
        side_effect=SMTPException,
    )
    def test_send_change_password_email_with_retry(self, mock_retry):
        with patch(
            "ecommerce.apps.users.models.User.objects.get"
        ) as mock_get_user, patch(
            "ecommerce.core.celery.tasks.email.CustomerDispatcher"
        ) as mock_dispatcher:
            # Set up the mock user object and dispatcher to raise SMTPException
            mock_user = Mock(spec=User)
            mock_user.id = 1
            mock_user.email = "test123@gmail.com"
            mock_get_user.return_value = mock_user

            mock_dispatcher_instance = mock_dispatcher.return_value
            mock_dispatcher_instance.send_password_changed_email_for_user.side_effect = (
                SMTPException
            )

            # Call the task expecting it to raise SMTPException and trigger a retry
            with self.assertRaises(SMTPException):
                send_password_changed_email_for_user(user_id=1)

            # Assert the retry was called
            mock_retry.assert_called_once()

    @patch("ecommerce.apps.users.models.User.objects.get")
    @patch("ecommerce.core.celery.tasks.email.CustomerDispatcher")
    def test_send_change_password_email_for_user(self, mock_dispatcher, mock_get_user):
        # Set up the mock user object
        mock_user = Mock(spec=User)
        mock_user.id = 1
        mock_user.email = "test123@gmail.com"
        mock_get_user.return_value = mock_user

        # Set up the mock for the CustomerDispatcher method
        mock_dispatcher_instance = mock_dispatcher.return_value
        mock_dispatcher_instance.send_password_changed_email_for_user.return_value = (
            None
        )

        # Call the task without delay to perform it immediately
        send_password_changed_email_for_user(user_id=1)

        # Assertions to check if the User was fetched and the email was sent
        mock_get_user.assert_called_once_with(id=1)
        mock_dispatcher_instance.send_password_changed_email_for_user.assert_called_once_with(
            mock_user, {"user": mock_user}
        )

    @patch(
        "ecommerce.core.celery.tasks.email.send_password_changed_email_for_user.retry",
        side_effect=SMTPException,
    )
    @patch("ecommerce.apps.users.models.User.objects.get")
    @patch("ecommerce.core.celery.tasks.email.CustomerDispatcher")
    def test_send_change_password_email_failure(
        self, mock_dispatcher, mock_get_user, mock_retry
    ):
        # Set up the mock user object
        mock_user = Mock(spec=User)
        mock_user.id = 1
        mock_user.email = "test123@gmail.com"
        mock_get_user.return_value = mock_user

        # Simulate an SMTPException when sending an email
        mock_dispatcher_instance = mock_dispatcher.return_value
        mock_dispatcher_instance.send_password_changed_email_for_user.side_effect = (
            SMTPException
        )

        # Attempt to send the email, which we expect to fail
        with self.assertRaises(SMTPException):
            send_password_changed_email_for_user(user_id=1)

        # Check if the task tried to retry the operation
        mock_retry.assert_called_once()
