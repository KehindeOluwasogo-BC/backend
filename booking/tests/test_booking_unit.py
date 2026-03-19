import pytest
from datetime import date, time
from types import SimpleNamespace

from django.contrib.auth.models import User

from booking.models import Booking
from booking.serializers import BookingSerializer


pytestmark = pytest.mark.django_db


def test_regular_user_update_forces_non_pending_status_back_to_pending():
    user = User.objects.create_user(username="booking_unit_user", password="StrongPass123!")
    booking = Booking.objects.create(
        user=user,
        full_name="Unit User",
        email="unit@example.com",
        service="Haircut",
        booking_date=date(2026, 3, 11),
        booking_time=time(9, 0),
        notes="initial",
        status="confirmed",
    )

    request = SimpleNamespace(user=user)

    serializer = BookingSerializer(
        instance=booking,
        data={"status": "cancelled", "notes": "updated by regular user"},
        partial=True,
        context={"request": request},
    )
    assert serializer.is_valid(), serializer.errors

    updated_booking = serializer.save()

    assert updated_booking.notes == "updated by regular user"
    assert updated_booking.status == "pending"


def test_regular_user_cannot_override_status_when_already_pending():
    user = User.objects.create_user(username="booking_unit_user2", password="StrongPass123!")
    booking = Booking.objects.create(
        user=user,
        full_name="Unit User",
        email="unit@example.com",
        service="Haircut",
        booking_date=date(2026, 3, 11),
        booking_time=time(9, 0),
        notes="initial",
        status="pending",
    )

    request = SimpleNamespace(user=user)

    serializer = BookingSerializer(
        instance=booking,
        data={"status": "cancelled", "notes": "updated by regular user"},
        partial=True,
        context={"request": request},
    )
    assert serializer.is_valid(), serializer.errors

    updated_booking = serializer.save()

    assert updated_booking.notes == "updated by regular user"
    assert updated_booking.status == "pending"


def test_superuser_can_update_status():
    admin = User.objects.create_superuser(
        username="booking_admin", email="booking_admin@example.com", password="StrongPass123!"
    )
    booking_owner = User.objects.create_user(
        username="booking_owner", email="booking_owner@example.com", password="StrongPass123!"
    )

    booking = Booking.objects.create(
        user=booking_owner,
        full_name="Owner User",
        email="owner@example.com",
        service="Massage",
        booking_date=date(2026, 3, 11),
        booking_time=time(10, 30),
        notes="initial",
        status="pending",
    )

    request = SimpleNamespace(user=admin)

    serializer = BookingSerializer(
        instance=booking,
        data={"status": "confirmed", "notes": "updated by admin"},
        partial=True,
        context={"request": request},
    )
    assert serializer.is_valid(), serializer.errors

    updated_booking = serializer.save()

    assert updated_booking.notes == "updated by admin"
    assert updated_booking.status == "confirmed"
