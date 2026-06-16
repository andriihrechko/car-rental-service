from django.shortcuts import reverse
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from payments.service import StripeService
from rentals.filters import RentalFilter
from rentals.models import Rental
from rentals.serializers import (
    RentalCancelSerializer,
    RentalReturnSerializer,
    RentalSerializer,
)


stripe_service = StripeService()


class RentalViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """ViewSet for managing rentals."""

    serializer_class = RentalSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = RentalFilter
    queryset = Rental.objects.select_related("car", "user")

    def get_queryset(self):
        """Return rentals for current user. Staff can see all rentals."""
        user = self.request.user
        queryset = self.queryset
        if not user.is_staff:
            queryset = queryset.filter(user=user)
        return queryset

    @action(detail=True, methods=["post"], url_path="return")
    def return_rental(self, request, pk=None):
        """Mark rental as COMPLETED/OVERDUE."""
        rental = self.get_object()

        serializer = RentalReturnSerializer(rental, data={})
        serializer.is_valid(raise_exception=True)
        rental = serializer.save()

        success_url = request.build_absolute_uri(reverse("payments:success"))
        success_url = f"{success_url}?session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = request.build_absolute_uri(reverse("payments:cancel"))

        payment = stripe_service.create_rental_payment(
            rental,
            success_url=success_url,
            cancel_url=cancel_url,
        )

        return Response(
            {
                "rental": RentalSerializer(rental).data,
                "amount_to_pay": payment.money_to_pay,
                "payment_url": payment.session_url,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel_rental(self, request, pk=None):
        """Cancel a BOOKED rental."""
        rental = self.get_object()
        serializer = RentalCancelSerializer(rental, data={})

        serializer.is_valid(raise_exception=True)
        rental = serializer.save()
        if timezone.now().date() >= rental.start_date:
            success_url = request.build_absolute_uri(
                reverse("payments:success")
            )
            success_url = f"{success_url}?session_id={{CHECKOUT_SESSION_ID}}"
            cancel_url = request.build_absolute_uri(reverse("payments:cancel"))

            payment = stripe_service.create_rental_payment(
                rental,
                success_url=success_url,
                cancel_url=cancel_url,
            )
            return Response(
                {
                    "rental": RentalSerializer(rental).data,
                    "message": ".",
                    "amount_to_pay": payment.money_to_pay,
                    "payment_url": payment.session_url,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(RentalSerializer(rental).data)
