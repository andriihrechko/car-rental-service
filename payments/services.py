from django.conf import settings
from django.db import transaction

import stripe

from payments.models import Payment


def calculate_rental_price(rental):
    rental_days = (rental.end_date - rental.start_date).days
    rental_days = max(rental_days, 1)
    price = rental_days * rental.price_per_day
    return price


@transaction.atomic
def create_rental_payment(rental, *, success_url, cancel_url):
    payment_exists = Payment.objects.filter(
        rental=rental,
        type=Payment.Type.RENTAL,
        status__in=[
            Payment.Status.PENDING,
            Payment.Status.PAID,
        ],
    ).exists()
    if payment_exists:
        raise ValueError("Rental payment already exists.")
    money_to_pay = calculate_rental_price(rental)
    payment = Payment.objects.create(
        rental=rental,
        type=Payment.Type.RENTAL,
        status=Payment.Status.PENDING,
        money_to_pay=money_to_pay,
    )
    stripe.api_key = settings.STRIPE_SECRET_KEY
    session = stripe.checkout.Session.create(
        mode="payment",
        line_items=[
            {
                "price_data": {
                    "currency": "usd",
                    "unit_amount": int(payment.money_to_pay * 100),
                    "product_data": {
                        "name": f"Rental #{rental.id}",
                    },
                },
                "quantity": 1,
            }
        ],
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={
            "payment_id": str(payment.id),
        },
    )
    payment.session_id = session.id
    payment.session_url = session.url
    payment.save(update_fields=["session_id", "session_url"])

    return payment
