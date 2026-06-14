from django.contrib.auth import get_user_model
from rest_framework import serializers


User = get_user_model()


class SignUpSerializer(serializers.ModelSerializer):
    """
    Serializer for the user signup with email and password.
    First name and last name are optional.
    """
    class Meta:
        model = User
        fields = ("email", "password", "first_name", "last_name")
        extra_kwargs = {
            "password": {
                "write_only": True,
                "style": {"input_type": "password"}
            },
        }

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UserMeSerializer(serializers.ModelSerializer):
    """Serializer for the currently authenticated user."""
    class Meta:
        model = User
        fields = ("id", "email", "first_name", "last_name")
        read_only_fields = ("id", "email")
