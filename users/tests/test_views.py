from django.contrib.auth import get_user_model
from django.shortcuts import reverse
from rest_framework import test, status


User = get_user_model()

class TestSignUpView(test.APITestCase):
    """Test the signup view."""
    def setUp(self):
        self.url = reverse("users:signup")
        self.valid_data = {
            "email": "test@example.com",
            "password": "StrongPassword123!",
            "first_name": "John",
            "last_name": "Doe",
        }

    def test_signup_success(self):
        response = self.client.post(self.url, self.valid_data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.get().email, self.valid_data["email"])

    def test_signup_missing_email(self):
        data = self.valid_data.copy()
        del data["email"]

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 0)

    def test_signup_invalid_email(self):
        data = self.valid_data.copy()
        data["email"] = "not-an-email"
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserMeViewTests(test.APITestCase):
    def setUp(self):
        self.url = reverse("users:me")
        self.user = User.objects.create_user(
            email="test@example.com",
            password="password123",
            first_name="John"
        )

    def test_get_user_me_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_user_me_success(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], self.user.email)

    def test_update_user_me_success(self):
        self.client.force_authenticate(user=self.user)
        updated_data = {"first_name": "Jane"}

        response = self.client.patch(self.url, updated_data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Jane")
