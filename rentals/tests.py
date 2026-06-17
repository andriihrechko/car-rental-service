from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

# Create your tests here.
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from cars.models import Car
from rentals.models import Rental


User = get_user_model()


class RentalAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="user@test.com",
            password="pass1234",
        )
        self.client.force_authenticate(user=self.user)

        self.car = Car.objects.create(
            brand="Toyota",
            model="Camry",
            year=2022,
            fuel_type="GAS",
            daily_rate="50.00",
            inventory=5,
        )

        self.today = date.today()
        self.rental_data = {
            "car": self.car.pk,
            "start_date": self.today,
            "end_date": self.today + timedelta(days=3),
        }

    def test_create_rental_success(self):
        # Змінено на rentals:rental-list
        res = self.client.post(
            reverse("rentals:rental-list"), self.rental_data
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Rental.objects.count(), 1)

    def test_create_rental_invalid_dates(self):
        data = {
            "car": self.car.pk,
            "start_date": self.today + timedelta(days=5),
            "end_date": self.today,
        }
        # Змінено на rentals:rental-list
        res = self.client.post(reverse("rentals:rental-list"), data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_rental_no_inventory(self):
        self.car.inventory = 0
        self.car.save()

        # Змінено на rentals:rental-list
        res = self.client.post(
            reverse("rentals:rental-list"), self.rental_data
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_return_rental(self):
        # Змінено на rentals:rental-list
        self.client.post(reverse("rentals:rental-list"), self.rental_data)
        rental = Rental.objects.first()

        # Змінено на rentals:rental-return-rental
        res = self.client.post(
            reverse("rentals:rental-return-rental", args=[rental.pk])
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        rental.refresh_from_db()
        self.assertEqual(rental.status, Rental.Status.COMPLETED)

    def test_cancel_rental(self):
        # Змінено на rentals:rental-list
        self.client.post(reverse("rentals:rental-list"), self.rental_data)
        rental = Rental.objects.first()

        # Змінено на rentals:rental-cancel-rental
        res = self.client.post(
            reverse("rentals:rental-cancel-rental", args=[rental.pk])
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        rental.refresh_from_db()
        self.assertEqual(rental.status, Rental.Status.CANCELLED)

    def test_list_rentals_only_own(self):
        # Змінено на rentals:rental-list
        self.client.post(reverse("rentals:rental-list"), self.rental_data)

        other_user = User.objects.create_user(
            email="other@test.com", password="pass1234"
        )
        other_client = APIClient()
        other_client.force_authenticate(user=other_user)

        # Змінено на rentals:rental-list
        res = other_client.get(reverse("rentals:rental-list"))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 0)


class RentalAPIAdditionalTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="user2@test.com", password="pass1234"
        )
        self.other_user = User.objects.create_user(
            email="other2@test.com", password="pass1234"
        )
        self.staff_user = User.objects.create_user(
            email="staff2@test.com", password="pass1234", is_staff=True
        )
        self.client.force_authenticate(user=self.user)

        self.car = Car.objects.create(
            brand="Toyota",
            model="Camry",
            year=2022,
            fuel_type="GAS",
            daily_rate="50.00",
            inventory=2,
        )

        self.today = date.today()
        self.rental_data = {
            "car": self.car.pk,
            "start_date": self.today,
            "end_date": self.today + timedelta(days=3),
        }

    def create_rental(self, client=None, **overrides):
        client = client or self.client
        data = {**self.rental_data, **overrides}
        return client.post(reverse("rentals:rental-list"), data)

    def test_create_rental_equal_start_and_end_date_allowed(self):
        res = self.create_rental(start_date=self.today, end_date=self.today)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_create_rental_no_inventory_when_dates_overlap(self):
        self.car.inventory = 1
        self.car.save()

        res1 = self.create_rental()
        self.assertEqual(res1.status_code, status.HTTP_201_CREATED)

        other_client = APIClient()
        other_client.force_authenticate(user=self.other_user)
        res2 = self.create_rental(client=other_client)
        self.assertEqual(res2.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_rental_allowed_when_dates_dont_overlap(self):
        self.car.inventory = 1
        self.car.save()

        res1 = self.create_rental()
        self.assertEqual(res1.status_code, status.HTTP_201_CREATED)

        other_client = APIClient()
        other_client.force_authenticate(user=self.other_user)
        res2 = self.create_rental(
            client=other_client,
            start_date=self.today + timedelta(days=10),
            end_date=self.today + timedelta(days=12),
        )
        self.assertEqual(res2.status_code, status.HTTP_201_CREATED)

    def test_create_rental_requires_authentication(self):
        anon_client = APIClient()
        res = self.create_rental(client=anon_client)
        self.assertIn(
            res.status_code,
            (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
        )

    def test_staff_sees_all_rentals(self):
        self.create_rental()

        staff_client = APIClient()
        staff_client.force_authenticate(user=self.staff_user)
        res = staff_client.get(reverse("rentals:rental-list"))

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)

    def test_retrieve_other_users_rental_not_found(self):
        self.create_rental()
        rental = Rental.objects.first()

        other_client = APIClient()
        other_client.force_authenticate(user=self.other_user)
        res = other_client.get(reverse("rentals:rental-detail", args=[rental.pk]))
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_filter_by_status(self):
        self.create_rental()
        res = self.client.get(
            reverse("rentals:rental-list"), {"status": Rental.Status.BOOKED}
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)

        res_empty = self.client.get(
            reverse("rentals:rental-list"), {"status": Rental.Status.CANCELLED}
        )
        self.assertEqual(len(res_empty.data), 0)


@patch("rentals.views.stripe_service.create_rental_payment")
class RentalReturnCancelAdditionalTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="user3@test.com", password="pass1234"
        )
        self.other_user = User.objects.create_user(
            email="other3@test.com", password="pass1234"
        )
        self.staff_user = User.objects.create_user(
            email="staff3@test.com", password="pass1234", is_staff=True
        )
        self.client.force_authenticate(user=self.user)

        self.car = Car.objects.create(
            brand="Toyota",
            model="Camry",
            year=2022,
            fuel_type="GAS",
            daily_rate="50.00",
            inventory=5,
        )
        self.today = date.today()

    def _fake_payment(self):
        payment = MagicMock()
        payment.money_to_pay = Decimal("50.00")
        payment.session_url = "https://stripe.test/session/abc123"
        return payment

    def create_rental(self, client=None, **overrides):
        client = client or self.client
        data = {
            "car": self.car.pk,
            "start_date": self.today,
            "end_date": self.today + timedelta(days=3),
            **overrides,
        }
        return client.post(reverse("rentals:rental-list"), data)

    def test_return_rental_overdue(self, mock_create_payment):
        mock_create_payment.return_value = self._fake_payment()

        self.create_rental(
            start_date=self.today - timedelta(days=10),
            end_date=self.today - timedelta(days=1),
        )
        rental = Rental.objects.first()

        self.client.post(reverse("rentals:rental-return-rental", args=[rental.pk]))
        rental.refresh_from_db()
        self.assertEqual(rental.status, Rental.Status.OVERDUE)

    def test_cannot_return_already_completed_rental(self, mock_create_payment):
        self.create_rental()
        rental = Rental.objects.first()
        rental.status = Rental.Status.COMPLETED
        rental.save()

        res = self.client.post(reverse("rentals:rental-return-rental", args=[rental.pk]))
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        mock_create_payment.assert_not_called()

    def test_cannot_return_another_users_rental(self, mock_create_payment):
        self.create_rental()
        rental = Rental.objects.first()

        other_client = APIClient()
        other_client.force_authenticate(user=self.other_user)
        res = other_client.post(reverse("rentals:rental-return-rental", args=[rental.pk]))
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        mock_create_payment.assert_not_called()

    def test_staff_can_return_any_users_rental(self, mock_create_payment):
        mock_create_payment.return_value = self._fake_payment()

        self.create_rental()
        rental = Rental.objects.first()

        staff_client = APIClient()
        staff_client.force_authenticate(user=self.staff_user)
        staff_client.post(reverse("rentals:rental-return-rental", args=[rental.pk]))
        rental.refresh_from_db()
        self.assertEqual(rental.status, Rental.Status.COMPLETED)

    def test_cancel_before_start_no_payment_required(self, mock_create_payment):
        self.create_rental(
            start_date=self.today + timedelta(days=2),
            end_date=self.today + timedelta(days=5),
        )
        rental = Rental.objects.first()

        res = self.client.post(reverse("rentals:rental-cancel-rental", args=[rental.pk]))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        rental.refresh_from_db()
        self.assertEqual(rental.status, Rental.Status.CANCELLED)
        mock_create_payment.assert_not_called()

    def test_cancel_after_start_charges_fee(self, mock_create_payment):
        mock_create_payment.return_value = self._fake_payment()

        self.create_rental(
            start_date=self.today,
            end_date=self.today + timedelta(days=3),
        )
        rental = Rental.objects.first()

        res = self.client.post(reverse("rentals:rental-cancel-rental", args=[rental.pk]))
        self.assertIn(res.status_code, (status.HTTP_200_OK, status.HTTP_201_CREATED))
        rental.refresh_from_db()
        self.assertEqual(rental.status, Rental.Status.CANCELLED)
        mock_create_payment.assert_called_once()

    def test_cannot_cancel_already_cancelled_rental(self, mock_create_payment):
        self.create_rental()
        rental = Rental.objects.first()
        rental.status = Rental.Status.CANCELLED
        rental.save()

        res = self.client.post(reverse("rentals:rental-cancel-rental", args=[rental.pk]))
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        mock_create_payment.assert_not_called()
