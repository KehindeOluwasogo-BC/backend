import pytest
from datetime import date, time
from types import SimpleNamespace

from django.contrib.auth.models import User

from booking.models import Booking
from booking.serializers import BookingSerializer


pytestmark = pytest.mark.django_db
