import stripe
from django.conf import settings

from payments.helper import MoneyHelper
from payments.models import Payment
from rentals.models import Rental


stripe.api_key = settings.STRIPE_SECRET_KEY
helper = MoneyHelper()


class StripeService:
    def create_rental_payment(self, rental, *, success_url, cancel_url):
        payment = self._create_rental_payment(rental)
        try:
            session = self._create_checkout_session(
                payment, success_url=success_url, cancel_url=cancel_url
            )
            payment.session_id = session.id
            payment.session_url = session.url
            payment.save()
            return payment

        except Exception:
            payment.delete()
            payment.rental.status = Rental.Status.BOOKED
            payment.rental.save()
            raise

    def _create_rental_payment(self, rental):
        money_to_pay, payment_type = helper.calculate_rental_price(rental)
        return Payment.objects.create(
            rental=rental, type=payment_type, money_to_pay=money_to_pay
        )

    def _create_checkout_session(self, payment, *, success_url, cancel_url):
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
            metadata={"payment_id": str(payment.id)},
        )
