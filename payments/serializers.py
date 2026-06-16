from rest_framework import serializers

from payments.models import Payment
from rentals.models import Rental


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = (
            "id",
            "status",
            "type",
            "rental",
            "session_url",
            "session_id",
            "money_to_pay",
        )
        read_only_fields = (
            "id",
            "status",
            "session_id",
            "session_url",
            "money_to_pay",
        )


class PaymentCreateSerializer(serializers.Serializer):
    rental = serializers.PrimaryKeyRelatedField(queryset=Rental.objects.all())
