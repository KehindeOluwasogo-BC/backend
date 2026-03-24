import pytest
from datetime import date, time

from django.contrib.auth.models import User
from rest_framework.test import APIClient

from booking.models import Booking


pytestmark = pytest.mark.django_db


def test_superuser_can_create_booking_for_target_user_with_user_id():
    admin = User.objects.create_superuser(
        username="booking_admin",
        email="booking_admin@example.com",
        password="StrongPass123!",
    )
    target_user = User.objects.create_user(
        username="booking_target",
        email="booking_target@example.com",
        password="StrongPass123!",
    )

    client = APIClient()
    client.force_authenticate(user=admin)

    payload = {
        "full_name": "Target User",
        "email": "booking_target@example.com",
        "service": "Massage",
        "booking_date": date(2026, 4, 13).isoformat(),
        "booking_time": time(14, 0).isoformat(),
        "notes": "admin-created booking",
        "status": "pending",
        "user_id": target_user.id,
    }

    response = client.post("/api/bookings/", payload, format="json")

    assert response.status_code == 201

    created_booking = Booking.objects.get(id=response.data["id"])
    assert created_booking.user_id == target_user.id
    assert created_booking.full_name == payload["full_name"]


def test_regular_user_can_only_create_booking_for_self_even_if_user_id_provided():
    user = User.objects.create_user(
        username="regular_booking_user",
        email="regular_booking_user@example.com",
        password="StrongPass123!",
    )
    other_user = User.objects.create_user(
        username="other_user",
        email="other_user@example.com",
        password="StrongPass123!",
    )

    client = APIClient()
    client.force_authenticate(user=user)

    payload = {
        "full_name": "Regular User",
        "email": "regular_booking_user@example.com",
        "service": "Massage",
        "booking_date": date(2026, 4, 14).isoformat(),
        "booking_time": time(15, 30).isoformat(),
        "notes": "regular user booking",
        "status": "pending",
        "user_id": other_user.id,
    }

    response = client.post("/api/bookings/", payload, format="json")

    assert response.status_code == 201

    created_booking = Booking.objects.get(id=response.data["id"])
    assert created_booking.user_id == user.id
    assert created_booking.user_id != other_user.id


def test_regular_user_sees_only_their_own_bookings():
    requester = User.objects.create_user(username="booking_owner", password="pass1234")
    other_user = User.objects.create_user(username="other_owner", password="pass1234")

    Booking.objects.create(
        user=requester,
        full_name="Owner User",
        email="owner@example.com",
        service="Haircut",
        booking_date=date(2026, 4, 11),
        booking_time=time(10, 30),
        notes="own",
    )

    Booking.objects.create(
        user=other_user,
        full_name="Other User",
        email="other@example.com",
        service="Massage",
        booking_date=date(2026, 4, 12),
        booking_time=time(11, 0),
        notes="other",
    )

    client = APIClient()
    client.force_authenticate(user=requester)

    response = client.get("/api/bookings/")

    assert response.status_code == 200
    returned_ids = {item["id"] for item in response.data}
    assert len(returned_ids) == 1


def test_superuser_can_list_all_bookings():
    admin = User.objects.create_superuser(
        username="booking_admin2",
        email="booking_admin2@example.com",
        password="StrongPass123!",
    )

    first_user = User.objects.create_user(
        username="first_user",
        email="first_user@example.com",
        password="StrongPass123!",
    )
    second_user = User.objects.create_user(
        username="second_user",
        email="second_user@example.com",
        password="StrongPass123!",
    )

    Booking.objects.create(
        user=first_user,
        full_name="First User",
        email="first@example.com",
        service="Haircut",
        booking_date=date(2026, 4, 15),
        booking_time=time(9, 30),
        notes="first",
    )
    Booking.objects.create(
        user=second_user,
        full_name="Second User",
        email="second@example.com",
        service="Massage",
        booking_date=date(2026, 4, 16),
        booking_time=time(10, 30),
        notes="second",
    )

    client = APIClient()
    client.force_authenticate(user=admin)

    response = client.get("/api/bookings/")

    assert response.status_code == 200
    assert len(response.data) == 2
