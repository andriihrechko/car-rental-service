from django.utils import timezone

from payments.models import Payment
from rentals.models import Rental


class RentalService:
    def check_if_pending_payments(self, request):
        if Payment.objects.filter(
            rental__user=request.user,
            status=Payment.Status.PENDING,
        ).exists():
            return {"error": "You have a pending payment."}
        return None

    def return_rental(self, rental):
        today = timezone.now().date()
        if today > rental.end_date:
            rental.status = Rental.Status.OVERDUE
        else:
            rental.status = Rental.Status.COMPLETED

        rental.actual_return_date = today
        rental.save()
        return rental

    def cancel_rental(self, rental):
        today = timezone.now().date()
        if (rental.start_date - today).days < 1:
            rental.status = Rental.Status.CANCELLED
            rental.save()
            return "penalty_required"
        rental.status = Rental.Status.CANCELLED
        rental.save()
        return None
