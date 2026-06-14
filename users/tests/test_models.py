from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase


User = get_user_model()

class TestUserModel(TestCase):
    """Test the user model and the user base manager."""
    def setUp(self):
        self.email = "test@test.py"
        self.password = "test1234"

    def test_create_user_with_email_and_password_successful(self):
        user = User.objects.create_user(email=self.email, password=self.password)
        self.assertEqual(user.email, self.email)
        self.assertTrue(user.check_password(self.password))

    def test_user_email_field_required(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(email="", password=self.password)

    def test_user_email_field_unique(self):
        User.objects.create_user(email=self.email, password=self.password)
        with self.assertRaises(IntegrityError):
            User.objects.create_user(email=self.email, password=self.password)

    def test_create_user_email_normalized(self):
        email = "TEST@EXAMPLE.COM"
        user = User.objects.create_user(email=email, password=self.password)
        self.assertEqual(user.email, "TEST@example.com")

    def test_user_manager_create_user(self):
        user = User.objects.create_user(email=self.email, password=self.password)
        self.assertEqual(user.is_active, True)
        self.assertEqual(user.is_staff, False)
        self.assertEqual(user.is_superuser, False)

    def test_user_manager_create_superuser(self):
        user = User.objects.create_superuser(email=self.email, password=self.password)
        self.assertEqual(user.is_staff, True)
        self.assertEqual(user.is_superuser, True)

    def test_create_user_with_optional_fields(self):
        user = User.objects.create_user(
            email="optional@test.py", password=self.password
        )
        self.assertIsNone(user.first_name)
        self.assertIsNone(user.last_name)

        user.first_name = "John"
        user.last_name = "Doe"
        user.save()
        user.refresh_from_db()
        self.assertEqual(user.first_name, "John")
        self.assertEqual(user.last_name, "Doe")

    def test_user_str(self):
        user = User.objects.create_user(email=self.email, password=self.password)
        self.assertEqual(str(user), self.email)
