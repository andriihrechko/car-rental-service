import decimal

from django.utils import timezone

from payments.models import Payment
from rentals.models import Rental


class MoneyHelper:
    def calculate_rental_price(self, rental):
        if rental.status == Rental.Status.OVERDUE:
            return self._calculate_overdue(rental), Payment.Type.OVERDUE_FEE

        if rental.status == Rental.Status.CANCELLED:
            amount = self._calculate_base_rental(rental) * decimal.Decimal(
                "0.5"
            )
            return amount, Payment.Type.CANCELLATION_FEE

        return self._calculate_base_rental(rental), Payment.Type.RENTAL

    def _calculate_overdue(self, rental):
        days_rented = max((rental.end_date - rental.start_date).days, 1)
        overdue_days = max((timezone.now().date() - rental.end_date).days, 1)

        base_price = days_rented * rental.price_per_day
        overdue_price = (
            overdue_days * rental.price_per_day * decimal.Decimal("1.5")
        )

        return base_price + overdue_price

    def _calculate_base_rental(self, rental):
        days_rented = max((rental.end_date - rental.start_date).days, 1)
        return days_rented * rental.price_per_day
