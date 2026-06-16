from rest_framework import serializers

from payments.models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    rental = serializers.PrimaryKeyRelatedField(
        source="rental", read_only=True
    )

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
            "session_id",
            "session_url",
        )
