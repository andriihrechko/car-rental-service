from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, permissions
from rest_framework.filters import SearchFilter

from cars.models import Car
from cars.serializers import CarSerializer


class CarViewSet(viewsets.ModelViewSet):
    """ViewSet for managing cars inventory."""

    queryset = Car.objects.all()
    serializer_class = CarSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["brand", "fuel_type", "inventory"]
    search_fields = ["brand", "model"]

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]
