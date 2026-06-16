from django.conf import settings
from django.db import transaction

import stripe

from payments.models import Payment


class StripeService:
    def create_rental_payment(self, rental, *, success_url, cancel_url):
        payment = self._prepare_rental_payment(rental)

        try:
            session = self._create_checkout_session(
                payment,
                success_url=success_url,
                cancel_url=cancel_url,
            )
        except Exception:
            self._delete_unconfirmed_payment(payment)
            raise

        return self._attach_checkout_session(payment, session)

    def _calculate_rental_price(self, rental):
        rental_days = (rental.end_date - rental.start_date).days
        rental_days = max(rental_days, 1)
        return rental_days * rental.price_per_day

    @transaction.atomic
    def _prepare_rental_payment(self, rental):
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

        return Payment.objects.create(
            rental=rental,
            type=Payment.Type.RENTAL,
            status=Payment.Status.PENDING,
            money_to_pay=self._calculate_rental_price(rental),
        )

    def _create_checkout_session(self, payment, *, success_url, cancel_url):
        stripe.api_key = settings.STRIPE_SECRET_KEY

        return stripe.checkout.Session.create(
            mode="payment",
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "unit_amount": int(payment.money_to_pay * 100),
                        "product_data": {
                            "name": f"Rental #{payment.rental_id}",
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

    @transaction.atomic
    def _attach_checkout_session(self, payment, session):
        payment.session_id = session.id
        payment.session_url = session.url
        payment.save(update_fields=["session_id", "session_url"])
        return payment

    @transaction.atomic
    def _delete_unconfirmed_payment(self, payment):
        payment.delete()


def create_rental_payment(rental, *, success_url, cancel_url):
    return StripeService().create_rental_payment(
        rental,
        success_url=success_url,
        cancel_url=cancel_url,
    )


def calculate_rental_price(rental):
    return StripeService()._calculate_rental_price(rental)
