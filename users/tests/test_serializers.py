from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from users.serializers import SignUpSerializer, UserMeSerializer


User = get_user_model()


class TestSignUpSerializer(APITestCase):
    """Test the user signup serializer."""
    def test_create_user_successful(self):
        payload = {
            "email": "test@example.com",
            "password": "password123",
            "first_name": "John",
            "last_name": "Doe",
        }
        serializer = SignUpSerializer(data=payload)
        self.assertTrue(serializer.is_valid())

    def test_password_is_write_only(self):
        payload = {"email": "test@example.com", "password": "password123"}
        serializer = SignUpSerializer(data=payload)
        serializer.is_valid()
        user = serializer.save()

        data = SignUpSerializer(user).data
        self.assertNotIn("password", data)


class TestUserMeSerializer(APITestCase):
    """Test the user me serializer."""
    def setUp(self):
        self.user = User.objects.create_user(
            email="me@example.com", password="password", first_name="OldName"
        )

    def test_user_me_serializer_read_only_fields(self):
        data = {"email": "changed@example.com", "first_name": "NewName"}
        serializer = UserMeSerializer(instance=self.user, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        serializer.save()
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "me@example.com")
        self.assertEqual(self.user.first_name, "NewName")

    def test_user_me_serializer_output(self):
        serializer = UserMeSerializer(self.user)
        expected_keys = {"id", "email", "first_name", "last_name"}
        self.assertEqual(set(serializer.data.keys()), expected_keys)
