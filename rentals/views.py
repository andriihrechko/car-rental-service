from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from rentals.filters import RentalFilter
from rentals.models import Rental
from rentals.serializers import (
    RentalCancelSerializer,
    RentalReturnSerializer,
    RentalSerializer,
)


class RentalViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    GenericViewSet,
):
    """ViewSet for managing rentals."""

    serializer_class = RentalSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = RentalFilter

    def get_queryset(self):
        """Return rentals for current user. Staff can see all rentals."""
        user = self.request.user
        queryset = Rental.objects.select_related("car", "user")
        if not user.is_staff:
            queryset = queryset.filter(user=user)
        return queryset

    @action(detail=True, methods=["post"], url_path="return")
    def return_rental(self, request, pk=None):
        """Mark rental as COMPLETED and restore car inventory."""
        rental = self.get_object()
        serializer = RentalReturnSerializer(
            rental, data={}, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(RentalSerializer(rental).data)

    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel_rental(self, request, pk=None):
        """Cancel a BOOKED rental and restore car inventory."""
        rental = self.get_object()
        serializer = RentalCancelSerializer(
            rental, data={}, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(RentalSerializer(rental).data)
