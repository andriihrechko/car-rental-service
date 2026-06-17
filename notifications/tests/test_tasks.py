from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from cars.models import Car
from notifications.tasks import (
    notify_overdue_rentals,
    send_payment_notification,
)
from payments.models import Payment
from rentals.models import Rental
from users.models import User


class BaseTaskTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="john@test.com",
            first_name="John",
            last_name="Doe",
            password="test_password",
        )

        self.car = Car.objects.create(
            brand="Toyota",
            model="Camry",
            year=2022,
            fuel_type=Car.FuelType.GAS,
            daily_rate=Decimal("50.00"),
            inventory=5,
        )


class NotifyOverdueRentalsTests(BaseTaskTestCase):

    @patch("notifications.tasks.NotificationService.send")
    def test_should_not_send_message_when_no_overdue_rentals(
        self,
        mock_send,
    ):
        notify_overdue_rentals()

        mock_send.assert_not_called()

    @patch("notifications.tasks.NotificationService.send")
    def test_should_mark_rental_as_overdue_and_send_notification(
        self,
        mock_send,
    ):
        rental = Rental.objects.create(
            car=self.car,
            user=self.user,
            start_date=timezone.now().date() - timedelta(days=7),
            end_date=timezone.now().date() - timedelta(days=1),
            status=Rental.Status.BOOKED,
            price_per_day=Decimal("50.00"),
        )

        notify_overdue_rentals()

        rental.refresh_from_db()

        self.assertEqual(
            rental.status,
            Rental.Status.OVERDUE,
        )

        expected_message = (
            "🚨 Overdue rentals report\n\n"
            "Total overdue rentals: 1\n\n"
            f"Rental: {rental}\n"
            "User info: John Doe\n"
            "User email: john@test.com\n\n"
        )

        mock_send.assert_called_once_with(
            expected_message,
        )

    @patch("notifications.tasks.NotificationService.send")
    def test_should_not_mark_today_rental_as_overdue(
        self,
        mock_send,
    ):
        rental = Rental.objects.create(
            car=self.car,
            user=self.user,
            start_date=timezone.now().date(),
            end_date=timezone.now().date(),
            status=Rental.Status.BOOKED,
            price_per_day=Decimal("50.00"),
        )

        notify_overdue_rentals()

        rental.refresh_from_db()

        self.assertEqual(
            rental.status,
            Rental.Status.BOOKED,
        )

        mock_send.assert_not_called()


class SendPaymentNotificationTests(BaseTaskTestCase):

    @patch("notifications.tasks.NotificationService.send")
    def test_should_send_payment_notification(
        self,
        mock_send,
    ):
        rental = Rental.objects.create(
            car=self.car,
            user=self.user,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=3),
            status=Rental.Status.BOOKED,
            price_per_day=Decimal("50.00"),
        )

        payment = Payment.objects.create(
            rental=rental,
            status=Payment.Status.PAID,
            type=Payment.Type.RENTAL,
            session_url="https://stripe.com/test",
            session_id="session_123",
            money_to_pay=Decimal("150.00"),
        )

        send_payment_notification(payment.id)

        expected_message = (
            "💰 Payment successful\n\n"
            f"Payment ID: {payment.id}\n"
            f"Rental: {rental}\n"
            "User info: John Doe\n"
            "User email: john@test.com\n"
            "Amount: 150.00"
        )

        mock_send.assert_called_once_with(
            expected_message,
        )