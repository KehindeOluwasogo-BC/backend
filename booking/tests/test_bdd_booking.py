from datetime import date, time

import pytest
from django.contrib.auth.models import User
from pytest_bdd import given, scenario, then, when
from rest_framework.test import APIClient

from booking.models import Booking


pytestmark = pytest.mark.django_db


@scenario("features/booking_visibility.feature", "Regular user sees only their own bookings")
def test_regular_user_sees_only_their_own_bookings():
    pass


@given("two users each have one booking", target_fixture="booking_context")
def booking_context():
    requester = User.objects.create_user(username="booking_owner", password="pass1234")
    other_user = User.objects.create_user(username="other_owner", password="pass1234")

    own_booking = Booking.objects.create(
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

    return {"requester": requester, "own_booking": own_booking}


@given("the first user is authenticated for the booking API", target_fixture="api_client")
def api_client(booking_context):
    client = APIClient()
    client.force_authenticate(user=booking_context["requester"])
    return client


@when("the first user requests the bookings list endpoint", target_fixture="response")
def request_booking_list(api_client):
    return api_client.get("/api/bookings/")


@then("the booking list response status code is 200")
def assert_status_ok(response):
    assert response.status_code == 200


@then("only the first user's booking is returned")
def assert_only_first_users_booking(response, booking_context):
    returned_ids = {item["id"] for item in response.data}
    assert returned_ids == {booking_context["own_booking"].id}
