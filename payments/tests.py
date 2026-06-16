from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase

from payments.models import Payment
from payments.services import calculate_rental_price, create_rental_payment
from rentals.models import Rental


class CalculateRentalPriceTests(TestCase):
    def test_calculates_price_for_multiple_days(self):
        rental = Rental(
            start_date=date(2026, 6, 15),
            end_date=date(2026, 6, 18),
            price_per_day=Decimal("100.00"),
        )

        result = calculate_rental_price(rental)

        self.assertEqual(result, Decimal("300.00"))


class CreateRentalPaymentTests(TestCase):
    def setUp(self):
        self.rental = Rental.objects.create(
            start_date=date(2026, 6, 15),
            end_date=date(2026, 6, 18),
            price_per_day=Decimal("100.00"),
        )

    @patch("payments.services.stripe.checkout.Session.create")
    def test_creates_pending_rental_payment(self, mock_session_create):
        mock_session_create.return_value.id = "cs_test_123"
        mock_session_create.return_value.url = (
            "https://checkout.stripe.com/test"
        )

        payment = create_rental_payment(
            self.rental,
            success_url="http://testserver/api/payments/success/",
            cancel_url="http://testserver/api/payments/cancel/",
        )

        self.assertEqual(payment.status, Payment.Status.PENDING)
        self.assertEqual(payment.type, Payment.Type.RENTAL)
        self.assertEqual(payment.money_to_pay, Decimal("300.00"))
        self.assertEqual(payment.rental, self.rental)
        self.assertEqual(payment.session_id, "cs_test_123")
        self.assertEqual(
            payment.session_url,
            "https://checkout.stripe.com/test",
        )
        self.assertTrue(Payment.objects.filter(pk=payment.pk).exists())
        mock_session_create.assert_called_once()

    @patch("payments.services.stripe.checkout.Session.create")
    def test_rejects_duplicate_pending_payment(self, mock_session_create):
        mock_session_create.return_value.id = "cs_test_123"
        mock_session_create.return_value.url = (
            "https://checkout.stripe.com/test"
        )

        create_rental_payment(
            self.rental,
            success_url="http://testserver/api/payments/success/",
            cancel_url="http://testserver/api/payments/cancel/",
        )

        with self.assertRaisesMessage(
            ValueError,
            "Rental payment already exists.",
        ):
            create_rental_payment(
                self.rental,
                success_url="http://testserver/api/payments/success/",
                cancel_url="http://testserver/api/payments/cancel/",
            )

        self.assertEqual(
            Payment.objects.filter(rental=self.rental).count(),
            1,
        )
        mock_session_create.assert_called_once()

    @patch("payments.services.stripe.checkout.Session.create")
    def test_rolls_back_payment_when_stripe_fails(
        self,
        mock_session_create,
    ):
        mock_session_create.side_effect = RuntimeError(
            "Stripe is unavailable."
        )

        with self.assertRaisesMessage(
            RuntimeError,
            "Stripe is unavailable.",
        ):
            create_rental_payment(
                self.rental,
                success_url="http://testserver/api/payments/success/",
                cancel_url="http://testserver/api/payments/cancel/",
            )

        self.assertFalse(
            Payment.objects.filter(rental=self.rental).exists()
        )
