from decimal import Decimal
from unittest.mock import MagicMock, patch

import stripe
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from cars.models import Car
from payments.helper import MoneyHelper
from payments.models import Payment
from payments.serializers import PaymentSerializer
from payments.service import StripeService
from rentals.models import Rental


User = get_user_model()


def make_rental(status=Rental.Status.BOOKED, days=3, price_per_day="50.00"):
    user = User.objects.create_user(
        email=f"user{Rental.objects.count()}@test.com", password="pass1234"
    )
    car = Car.objects.create(
        brand="Toyota",
        model="Camry",
        year=2022,
        fuel_type="GAS",
        daily_rate=price_per_day,
        inventory=5,
    )
    from datetime import date, timedelta

    start = date.today() if status != Rental.Status.OVERDUE else date.today() - timedelta(days=10)
    end = start + timedelta(days=days)
    rental = Rental.objects.create(
        car=car,
        user=user,
        start_date=start,
        end_date=end,
        price_per_day=Decimal(price_per_day),
        status=status,
    )
    return rental


class MoneyHelperTests(TestCase):
    def setUp(self):
        self.helper = MoneyHelper()

    def test_base_rental_price(self):
        rental = make_rental(status=Rental.Status.BOOKED, days=3, price_per_day="50.00")
        amount, payment_type = self.helper.calculate_rental_price(rental)
        self.assertEqual(amount, Decimal("150.00"))
        self.assertEqual(payment_type, Payment.Type.RENTAL)

    def test_completed_rental_uses_base_price(self):
        rental = make_rental(status=Rental.Status.COMPLETED, days=3, price_per_day="50.00")
        amount, payment_type = self.helper.calculate_rental_price(rental)
        self.assertEqual(amount, Decimal("150.00"))
        self.assertEqual(payment_type, Payment.Type.RENTAL)

    def test_same_day_rental_billed_as_one_day(self):
        rental = make_rental(status=Rental.Status.BOOKED, days=0, price_per_day="50.00")
        amount, payment_type = self.helper.calculate_rental_price(rental)
        self.assertEqual(amount, Decimal("50.00"))
        self.assertEqual(payment_type, Payment.Type.RENTAL)

    def test_cancellation_fee_is_half_of_base_price(self):
        rental = make_rental(status=Rental.Status.CANCELLED, days=4, price_per_day="50.00")
        amount, payment_type = self.helper.calculate_rental_price(rental)
        self.assertEqual(amount, Decimal("100.00"))  # 4 * 50 * 0.5
        self.assertEqual(payment_type, Payment.Type.CANCELLATION_FEE)

    def test_overdue_fee_adds_surcharge_on_top_of_base_price(self):
        rental = make_rental(status=Rental.Status.OVERDUE, days=10, price_per_day="50.00")
        amount, payment_type = self.helper.calculate_rental_price(rental)
        expected_base = Decimal("10") * Decimal("50.00")
        expected_overdue = Decimal("10") * Decimal("50.00") * Decimal("1.5")
        self.assertEqual(amount, expected_base + expected_overdue)
        self.assertEqual(payment_type, Payment.Type.OVERDUE_FEE)


@patch("payments.service.stripe.checkout.Session.create")
class StripeServiceTests(TestCase):
    def setUp(self):
        self.service = StripeService()

    def test_create_rental_payment_success(self, mock_session_create):
        rental = make_rental(status=Rental.Status.BOOKED, days=3, price_per_day="50.00")
        mock_session_create.return_value = MagicMock(
            id="sess_test_123", url="https://stripe.test/checkout/sess_test_123"
        )

        payment = self.service.create_rental_payment(
            rental,
            success_url="https://example.com/success",
            cancel_url="https://example.com/cancel",
        )

        self.assertEqual(Payment.objects.count(), 1)
        self.assertEqual(payment.status, Payment.Status.PENDING)
        self.assertEqual(payment.type, Payment.Type.RENTAL)
        self.assertEqual(payment.money_to_pay, Decimal("150.00"))
        self.assertEqual(payment.session_id, "sess_test_123")
        self.assertEqual(payment.session_url, "https://stripe.test/checkout/sess_test_123")
        mock_session_create.assert_called_once()

    def test_create_rental_payment_sends_correct_amount_to_stripe(self, mock_session_create):
        rental = make_rental(status=Rental.Status.BOOKED, days=2, price_per_day="50.00")
        mock_session_create.return_value = MagicMock(id="sess_1", url="https://stripe.test/1")

        self.service.create_rental_payment(
            rental, success_url="https://example.com/success", cancel_url="https://example.com/cancel"
        )

        _, kwargs = mock_session_create.call_args
        sent_unit_amount = kwargs["line_items"][0]["price_data"]["unit_amount"]
        self.assertEqual(sent_unit_amount, 10000)  # 100.00 -> 10000 cents

    def test_create_rental_payment_rolls_back_on_stripe_failure(self, mock_session_create):
        rental = make_rental(status=Rental.Status.CANCELLED, days=3, price_per_day="50.00")
        mock_session_create.side_effect = Exception("stripe is down")

        with self.assertRaises(Exception):
            self.service.create_rental_payment(
                rental,
                success_url="https://example.com/success",
                cancel_url="https://example.com/cancel",
            )

        self.assertEqual(Payment.objects.count(), 0)
        rental.refresh_from_db()
        # NOTE: this asserts the EXISTING behavior, which looks like a bug — see chat.
        self.assertEqual(rental.status, Rental.Status.BOOKED)


class PaymentSuccessViewTests(APITestCase):
    def setUp(self):
        self.rental = make_rental(status=Rental.Status.BOOKED, days=3, price_per_day="50.00")
        self.payment = Payment.objects.create(
            rental=self.rental,
            type=Payment.Type.RENTAL,
            money_to_pay=Decimal("150.00"),
            session_id="sess_abc",
            status=Payment.Status.PENDING,
        )

    def test_missing_session_id_returns_400(self):
        res = self.client.get(reverse("payments:success"))
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("payments.views.stripe.checkout.Session.retrieve")
    def test_marks_payment_paid_when_stripe_confirms_paid(self, mock_retrieve):
        mock_retrieve.return_value = MagicMock(payment_status="paid")

        res = self.client.get(reverse("payments:success"), {"session_id": "sess_abc"})

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.Status.PAID)

    @patch("payments.views.stripe.checkout.Session.retrieve")
    def test_does_not_mark_paid_when_stripe_says_unpaid(self, mock_retrieve):
        mock_retrieve.return_value = MagicMock(payment_status="unpaid")

        res = self.client.get(reverse("payments:success"), {"session_id": "sess_abc"})

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.Status.PENDING)

    @patch("payments.views.stripe.checkout.Session.retrieve")
    def test_invalid_session_id_is_not_handled_gracefully(self, mock_retrieve):
        mock_retrieve.side_effect = stripe.error.InvalidRequestError(
            message="No such checkout session", param="session_id"
        )

        with self.assertRaises(stripe.error.InvalidRequestError):
            self.client.get(reverse("payments:success"), {"session_id": "sess_does_not_exist"})


class PaymentCancelViewTests(APITestCase):
    def test_returns_200_with_message(self):
        res = self.client.get(reverse("payments:cancel"))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("detail", res.data)


class StripeWebhookViewTests(APITestCase):
    def setUp(self):
        self.rental = make_rental(status=Rental.Status.BOOKED, days=3, price_per_day="50.00")
        self.payment = Payment.objects.create(
            rental=self.rental,
            type=Payment.Type.RENTAL,
            money_to_pay=Decimal("150.00"),
            session_id="sess_webhook_1",
            status=Payment.Status.PENDING,
        )

    def _post_webhook(self, event):
        with patch("payments.views.stripe.Webhook.construct_event", return_value=event):
            return self.client.post(
                reverse("payments:webhook"),
                data=b"{}",
                content_type="application/json",
                HTTP_STRIPE_SIGNATURE="test_signature",
            )

    def test_checkout_session_completed_marks_payment_paid(self):
        event = {
            "type": "checkout.session.completed",
            "data": {"object": {"id": "sess_webhook_1"}},
        }
        res = self._post_webhook(event)

        self.assertEqual(res.status_code, 200)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.Status.PAID)

    def test_unhandled_event_type_is_ignored(self):
        event = {
            "type": "payment_intent.created",
            "data": {"object": {"id": "sess_webhook_1"}},
        }
        res = self._post_webhook(event)

        self.assertEqual(res.status_code, 200)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.Status.PENDING)

    def test_checkout_session_expired_is_not_handled(self):
        event = {
            "type": "checkout.session.expired",
            "data": {"object": {"id": "sess_webhook_1"}},
        }
        res = self._post_webhook(event)

        self.assertEqual(res.status_code, 200)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.Status.PENDING)

    def test_invalid_signature_returns_400(self):
        with patch(
            "payments.views.stripe.Webhook.construct_event",
            side_effect=stripe.error.SignatureVerificationError(
                "Invalid signature", sig_header="bad"
            ),
        ):
            res = self.client.post(
                reverse("payments:webhook"),
                data=b"{}",
                content_type="application/json",
                HTTP_STRIPE_SIGNATURE="bad_signature",
            )
        self.assertEqual(res.status_code, 400)

    def test_malformed_payload_returns_400(self):
        with patch(
            "payments.views.stripe.Webhook.construct_event",
            side_effect=ValueError("bad payload"),
        ):
            res = self.client.post(
                reverse("payments:webhook"),
                data=b"not json",
                content_type="application/json",
                HTTP_STRIPE_SIGNATURE="test_signature",
            )
        self.assertEqual(res.status_code, 400)


class PaymentSerializerTests(TestCase):
    def test_session_and_rental_are_read_only(self):
        rental = make_rental(status=Rental.Status.BOOKED, days=3, price_per_day="50.00")
        payment = Payment.objects.create(
            rental=rental, type=Payment.Type.RENTAL, money_to_pay=Decimal("150.00")
        )

        serializer = PaymentSerializer(
            payment,
            data={
                "session_id": "hacked_session",
                "session_url": "https://evil.example.com",
                "rental": other_rental.pk,
            },
            partial=True,
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated = serializer.save()

        self.assertEqual(updated.session_id, None)
        self.assertEqual(updated.session_url, None)
        self.assertEqual(updated.rental_id, rental.pk)

    def test_status_and_money_to_pay_are_NOT_protected(self):
        rental = make_rental(status=Rental.Status.BOOKED, days=3, price_per_day="50.00")
        payment = Payment.objects.create(
            rental=rental, type=Payment.Type.RENTAL, money_to_pay=Decimal("150.00")
        )

        serializer = PaymentSerializer(
            payment,
            data={"status": Payment.Status.PAID, "money_to_pay": "1.00"},
            partial=True,
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated = serializer.save()

        self.assertEqual(updated.status, Payment.Status.PAID)
        self.assertEqual(updated.money_to_pay, Decimal("1.00"))
