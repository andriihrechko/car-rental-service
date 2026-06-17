from celery import shared_task
from django.db import transaction
from django.utils import timezone

from notifications.notification_service import NotificationService
from payments.models import Payment
from rentals.models import Rental


@shared_task
def notify_overdue_rentals():
    with transaction.atomic():
        overdue_rentals = list(
            Rental.objects.select_related("user").filter(
                actual_return_date__isnull=True,
                end_date__lt=timezone.now().date(),
                status=Rental.Status.BOOKED,
            )
        )

        if not overdue_rentals:
            return

        Rental.objects.filter(
            id__in=[rental.id for rental in overdue_rentals]
        ).update(
            status=Rental.Status.OVERDUE,
        )

        message = (
            "🚨 Overdue rentals report\n\n"
            f"Total overdue rentals: {len(overdue_rentals)}\n\n"
        )

        for rental in overdue_rentals:
            rental.status = Rental.Status.OVERDUE
            user = rental.user

            message += (
                f"Rental: {rental}\n"
                f"User info: {user.first_name} {user.last_name}\n"
                f"User email: {user.email}\n\n"
            )

    NotificationService.send(message)


@shared_task
def send_payment_notification(payment_id: int):
    payment = Payment.objects.select_related(
        "rental",
        "rental__user",
    ).get(id=payment_id)

    user = payment.rental.user

    message = (
        "💰 Payment successful\n\n"
        f"Payment ID: {payment.id}\n"
        f"Rental: {payment.rental}\n"
        f"User info: {user.first_name} {user.last_name}\n"
        f"User email: {user.email}\n"
        f"Amount: {payment.money_to_pay}"
    )

    NotificationService.send(message)
