import datetime
from decimal import Decimal as D
from unittest.mock import Mock, patch

from django.utils import timezone
from oscar.core.compat import get_user_model

from ecommerce.apps.payment.models import Bankcard, Source
from ecommerce.test import factories
from ecommerce.test.testcases import TestCase


class TestBankcard(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

        self.bankcard = Bankcard.objects.create(
            user=self.user,
            card_type="Visa",
            last_4_digits="1234",
            expiry_date=datetime.date(2025, 12, 31),
        )

    def test_bankcard_without_stripe_id(self):
        bankcard = factories.BankcardFactory(stripe_card_id=None)
        self.assertFalse(bankcard.is_saved_to_stripe)

    def test_expiry_month_property(self):
        bankcard = factories.BankcardFactory(expiry_date=datetime.date(2023, 12, 1))
        self.assertEqual(bankcard.expiry_month(), "12/23")

        bankcard_no_expiry = factories.BankcardFactory(expiry_date=None)
        self.assertEqual(bankcard_no_expiry.expiry_month(), "-")

    def test_str_representation(self):
        bankcard = factories.BankcardFactory(
            card_type="Visa",
            last_4_digits="1234",
            expiry_date=datetime.date(2023, 12, 1),
        )
        self.assertEqual(str(bankcard), "Visa XXXX-XXXX-XXXX-1234 (Expires: 12/23)")

    def test_obfuscated_number(self):
        self.assertEqual(self.bankcard.obfuscated_number, "XXXX-XXXX-XXXX-1234")

    def test_is_saved_to_stripe(self):
        # Assuming no Stripe card ID is saved
        self.assertFalse(self.bankcard.is_saved_to_stripe)

        # Now let's simulate having a stripe card ID
        self.bankcard.stripe_card_id = "stripe_id_123"
        self.assertTrue(self.bankcard.is_saved_to_stripe)

    def test_bankcard_creation(self):
        # Create a bankcard using the factory
        bankcard = factories.BankcardFactory()

        # Ensure bankcard was created
        self.assertIsInstance(bankcard, Bankcard)

        # Check its properties
        self.assertEqual(bankcard.card_type in ["Visa", "MasterCard", "Amex"], True)
        self.assertEqual(len(bankcard.last_4_digits), 4)
        self.assertTrue(bankcard.is_saved_to_stripe)

        # Check obfuscated number
        expected_obfuscated_number = "XXXX-XXXX-XXXX-%s" % bankcard.last_4_digits
        self.assertEqual(bankcard.obfuscated_number, expected_obfuscated_number)

        # Check expiry_month property
        expected_expiry_month = bankcard.expiry_date.strftime("%m/%y")
        self.assertEqual(bankcard.expiry_month(), expected_expiry_month)

    @patch("ecommerce.apps.payment.models.stripe.Customer.retrieve_payment_method")
    def test_update_card_details_from_stripe(self, mock_retrieve_payment_method):
        # Mocking the response from Stripe API
        mock_retrieve_payment_method.return_value = Mock(
            card=Mock(brand="MasterCard", last4="5678", exp_year=2025, exp_month=6)
        )

        bankcard = factories.BankcardFactory(
            stripe_card_id="test_id", stripe_customer_id="test_customer_id"
        )
        bankcard.update_card_details_from_stripe()

        # Ensure attributes of the Bankcard instance are updated
        self.assertEqual(bankcard.card_type, "MasterCard")
        self.assertEqual(bankcard.last_4_digits, "5678")
        self.assertEqual(bankcard.expiry_date, datetime.date(2025, 6, 1))

    @patch("ecommerce.apps.payment.models.stripe.Customer.retrieve_payment_method")
    def test_get_stripe_card(self, mock_retrieve_payment_method):
        mock_retrieve_payment_method.return_value = Mock(
            card=Mock(brand="Visa", last4="1234", exp_year=2024, exp_month=12)
        )

        bankcard = factories.BankcardFactory(
            stripe_card_id="test_id", stripe_customer_id="test_customer_id"
        )
        stripe_card = bankcard.get_stripe_card()

        # Check if Stripe API was called with the right arguments
        mock_retrieve_payment_method.assert_called_with("test_customer_id", "test_id")

        # For the sake of example, you can also test attributes of the returned card
        self.assertEqual(stripe_card.card.brand, "Visa")
        self.assertEqual(stripe_card.card.last4, "1234")

    @patch("ecommerce.apps.payment.models.stripe.Customer.retrieve_payment_method")
    def test_expiry_month_invalid_format(self, mock_retrieve_payment_method):
        # Mock to ensure stripe isn't actually called
        mock_retrieve_payment_method.return_value = None

        bankcard = factories.BankcardFactory(expiry_date=datetime.date(2023, 12, 1))

        bankcard.expiry_month(format="%invalid_format%")

    @patch("ecommerce.apps.payment.models.stripe.Customer.retrieve_payment_method")
    def test_expiry_month_without_format_argument(self, mock_retrieve_payment_method):
        # Mock to ensure stripe isn't actually called
        mock_retrieve_payment_method.return_value = None

        bankcard = factories.BankcardFactory(expiry_date=datetime.date(2023, 12, 1))
        self.assertEqual(bankcard.expiry_month(), "12/23")

    @patch("ecommerce.apps.payment.models.stripe.Customer.retrieve_payment_method")
    def test_get_stripe_card_without_stripe_info(self, mock_retrieve_payment_method):
        # Mock to ensure stripe isn't actually called
        mock_retrieve_payment_method.return_value = None

        bankcard = factories.BankcardFactory(
            stripe_card_id=None, stripe_customer_id=None
        )
        result = bankcard.get_stripe_card()
        self.assertIsNone(result)


class TestSource(TestCase):
    def setUp(self):
        self.order = factories.OrderFactory()
        self.source_type = factories.SourceTypeFactory()
        self.source = factories.SourceFactory(
            order=self.order, source_type=self.source_type, amount_allocated=D("100.00")
        )

    def test_calculates_initial_balance_correctly(self):
        source = Source(amount_allocated=D("100"))
        self.assertEqual(D("100"), source.balance)

    def test_calculates_balance_correctly(self):
        source = Source(
            amount_allocated=D("100"), amount_debited=D("80"), amount_refunded=D("20")
        )
        self.assertEqual(D("100") - D("80") + D("20"), source.balance)

    def test_calculates_amount_for_refund_correctly(self):
        source = Source(
            amount_allocated=D("100"), amount_debited=D("80"), amount_refunded=D("20")
        )
        self.assertEqual(D("80") - D("20"), source.amount_available_for_refund)

    def test_str_method(self):
        self.assertIn(str(self.source.amount_allocated), str(self.source))
        self.assertIn(str(self.source.source_type), str(self.source))

    def test_balance_property(self):
        self.assertEqual(self.source.balance, D("100.00"))

        # Alter amounts to test balance calculation
        self.source.amount_debited = D("50.00")
        self.assertEqual(self.source.balance, D("50.00"))

        self.source.amount_refunded = D("20.00")
        self.assertEqual(self.source.balance, D("70.00"))

    def test_amount_available_for_refund(self):
        self.assertEqual(self.source.amount_available_for_refund, D("0.00"))

        self.source.amount_debited = D("50.00")
        self.assertEqual(self.source.amount_available_for_refund, D("50.00"))

        self.source.amount_refunded = D("20.00")
        self.assertEqual(self.source.amount_available_for_refund, D("30.00"))

    def test_allocate(self):
        self.source.allocate(D("50.00"))
        self.assertEqual(self.source.amount_allocated, D("150.00"))

    def test_debit(self):
        self.source.debit(D("50.00"))
        self.assertEqual(self.source.amount_debited, D("50.00"))

    def test_refund(self):
        self.source.amount_debited = D("100.00")
        self.source.refund(D("50.00"))
        self.assertEqual(self.source.amount_refunded, D("50.00"))

    def test_create_deferred_transaction_without_save(self):
        self.source.create_deferred_transaction("test_txn", D("10.00"))
        # Here you would test that the deferred transaction is not yet created

    def test_allocation_doesnt_error(self):
        self.source.allocate(D("100.00"))

    def test_debit_doesnt_error(self):
        self.source.allocate(D("100.00"))
        self.source.debit(D("80.00"))

    def test_full_debit_doesnt_error(self):
        self.source.allocate(D("100.00"))
        self.source.debit()
        self.assertEqual(D("0.00"), self.source.balance)

    def test_refund_doesnt_error(self):
        self.source.allocate(D("100.00"))
        self.source.debit(D("80.00"))
        self.source.refund(D("50.00"))


class TestTransaction(TestCase):
    def setUp(self):
        self.source = factories.SourceFactory()
        self.transaction = factories.TransactionFactory(
            source=self.source,
            txn_type="debit",
            amount=D("100.00"),
            reference="TEST_REF",
            status="pending",
        )

    def test_transaction_creation(self):
        self.assertEqual(self.transaction.txn_type, "debit")
        self.assertEqual(self.transaction.amount, D("100.00"))
        self.assertEqual(self.transaction.reference, "TEST_REF")
        self.assertEqual(self.transaction.status, "pending")

    def test_date_created_auto_add(self):
        # Assuming the transaction was just created, its date_created field
        # should be close to the current time. You can adjust the seconds as per your requirement.
        self.assertTrue((timezone.now() - self.transaction.date_created).seconds < 5)

    def test_str_method(self):
        # If the __str__ method is defined in Transaction model, test it
        self.assertIn(self.transaction.txn_type, str(self.transaction))
        self.assertIn(str(self.transaction.amount), str(self.transaction))

    def test_transaction_has_source(self):
        self.assertEqual(self.transaction.source, self.source)

    def test_reference_uniqueness(self):
        # This assumes reference needs to be unique.
        # If not, you can skip this test.
        with self.assertRaises(
            Exception
        ):  # Adjust to the specific exception you expect.
            duplicate_transaction = factories.TransactionFactory(reference="TEST_REF")
            print(duplicate_transaction)

    # def test_cascade_delete_source(self):
    #     self.source.delete()
    #     self.assertEqual(Transaction.objects.filter(reference="TEST_REF").count(), 0)

    def test_invalid_txn_type(self):
        # If you have a list of valid transaction types, check against those.
        with self.assertRaises(
            Exception
        ):  # Adjust to the specific exception you expect.
            invalid_txn = factories.TransactionFactory(txn_type="invalid_type")
            print(invalid_txn)

    def test_invalid_status(self):
        # If you have a list of valid statuses, check against those.
        with self.assertRaises(
            Exception
        ):  # Adjust to the specific exception you expect.
            invalid_status_txn = factories.TransactionFactory(status="invalid_status")
            print(invalid_status_txn)
