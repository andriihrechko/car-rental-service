from decimal import Decimal

from payments.models import Payment


class MoneyHelper:
    OVERDUE_FEE = Decimal("1.5")
    CANCEL_FEE = Decimal("0.5")

    def calculate_rental_price(self, rental):
        if not rental.actual_return_date:
            price = rental.price_per_day
            days_rented = max((rental.end_date - rental.start_date).days, 1)
            amount = days_rented * price * self.CANCEL_FEE
            return amount, Payment.Type.CANCELLATION_FEE
        return self._calculate_correct_rental(rental)

    def _calculate_correct_rental(self, rental):
        price = rental.price_per_day
        days_rented = max((rental.end_date - rental.start_date).days, 1)
        rental_price = days_rented * price
        days_overdue = max(
            (rental.actual_return_date - rental.end_date).days, 0
        )
        overdue_fee = days_overdue * self.OVERDUE_FEE * price
        payment_status = (
            Payment.Type.OVERDUE_FEE
            if days_overdue
            else Payment.Type.OVERDUE_FEE
        )
        return rental_price + overdue_fee, payment_status
