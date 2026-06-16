from unittest.mock import MagicMock, Mock, patch

from django.test import SimpleTestCase

from notifications.tasks import (
    notify_overdue_rentals,
    send_payment_notification,
)


class NotifyOverdueRentalsTests(SimpleTestCase):

    @patch("notifications.tasks.NotificationService.send")
    def test_should_not_send_message_when_no_overdue_rentals(
        self,
        mock_send,
    ):
        queryset = Mock()
        queryset.exists.return_value = False

        rental_model = Mock()
        rental_model.objects.filter.return_value = queryset

        notify_overdue_rentals(rental_model)

        mock_send.assert_not_called()

    @patch("notifications.tasks.NotificationService.send")
    def test_should_send_overdue_rentals_report(
        self,
        mock_send,
    ):
        first_rental = Mock(
            id=8,
            user_id=3,
        )

        second_rental = Mock(
            id=12,
            user_id=7,
        )

        queryset = MagicMock()
        queryset.exists.return_value = True
        queryset.count.return_value = 2
        queryset.__iter__.return_value = iter([first_rental,second_rental,])

        rental_model = Mock()
        rental_model.objects.filter.return_value = queryset

        notify_overdue_rentals(rental_model)

        expected_message = (
            "🚨 Overdue rentals report\n\n"
            "Total overdue rentals: 2\n\n"
            "Rental ID: 8\n"
            "User ID: 3\n\n"
            "Rental ID: 12\n"
            "User ID: 7\n\n"
        )

        mock_send.assert_called_once_with(
            expected_message,
        )


class SendPaymentNotificationTests(SimpleTestCase):

    @patch("notifications.tasks.NotificationService.send")
    def test_should_send_payment_notification(
        self,
        mock_send,
    ):
        user = Mock(id=3)

        rental = Mock(
            id=8,
            user=user,
        )

        payment = Mock(
            id=15,
            rental=rental,
            money_to_pay=120,
        )

        manager = Mock()
        manager.select_related.return_value.get.return_value = (
            payment
        )

        payment_model = Mock()
        payment_model.objects = manager

        send_payment_notification(
            payment_model,
            15,
        )

        expected_message = (
            "💰 Payment successful\n\n"
            "Payment ID: 15\n"
            "Rental ID: 8\n"
            "User ID: 3\n"
            "Amount: 120"
        )

        mock_send.assert_called_once_with(
            expected_message,
        )