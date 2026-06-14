from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

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
    serializer_class = RentalSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Rental.objects.select_related("car", "user")
        if not user.is_staff:
            qs = qs.filter(user=user)
        user_id = self.request.query_params.get("user_id")
        status_param = self.request.query_params.get("status")
        if user_id and user.is_staff:
            qs = qs.filter(user_id=user_id)
        if status_param:
            qs = qs.filter(status=status_param.upper())
        return qs

    @action(detail=True, methods=["post"], url_path="return")
    def return_rental(self, request, pk=None):
        rental = self.get_object()
        serializer = RentalReturnSerializer(
            rental, data={}, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(RentalSerializer(rental).data)

    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel_rental(self, request, pk=None):
        rental = self.get_object()
        serializer = RentalCancelSerializer(
            rental, data={}, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(RentalSerializer(rental).data)