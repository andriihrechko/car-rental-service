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
    overdue_rentals = Rental.objects.filter(
        actual_return_date__isnull=True,
        end_date__lt=timezone.now().date(),
        status=Rental.Status.BOOKED,
    )

    overdue_rentals.update(
        status=Rental.Status.OVERDUE,
    )

    if not overdue_rentals.exists():
        return

    message = (
        f"🚨 Overdue rentals report\n\n"
        f"Total overdue rentals: {overdue_rentals.count()}\n\n"
    )

    for rental in overdue_rentals:
        message += f"Rental: {rental}\nUser ID: {rental.user_id}\n\n"

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
