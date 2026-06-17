from celery import shared_task
from django.db import transaction
from django.utils import timezone

from notifications.notification_service import NotificationService
from payments.models import Payment
from rentals.models import Rental
from users.models import User


@shared_task
@transaction.atomic
def notify_overdue_rentals():
    overdue_rentals = Rental.objects.select_related("user").filter(
        actual_return_date__isnull=True,
        end_date__lt=timezone.now().date(),
        status=Rental.Status.BOOKED,
    )

    if not overdue_rentals:
        return

    overdue_rentals.update(
        status=Rental.Status.OVERDUE,
    )

    message = (
        f"🚨 Overdue rentals report\n\n"
        f"Total overdue rentals: {overdue_rentals.count()}\n\n"
    )

    for rental in overdue_rentals:
        user_first_name = rental.user.first_name
        user_last_name = rental.user.last_name
        user_email = rental.user.email

        message += (
            f"Rental: {rental}\n"
            f"User:"
            f" {user_first_name} {user_last_name} - {user_email}\n\n"
        )

    NotificationService.send(message)


@shared_task
def send_payment_notification(payment_id: int):
    payment = Payment.objects.select_related(
        "rental",
        "rental__user",
    ).get(id=payment_id)

    user_first_name = payment.rental.user.first_name
    user_last_name = payment.rental.user.last_name
    user_email = payment.rental.user.email

    message = (
        "💰 Payment successful\n\n"
        f"Payment ID: {payment.id}\n"
        f"Rental: {payment.rental}\n"
        f"User: {user_first_name} {user_last_name} - {user_email}\n"
        f"Amount: {payment.money_to_pay}"
    )

    NotificationService.send(message)
