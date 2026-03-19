import pytest
from datetime import timedelta

from django.contrib.auth.models import User
from django.utils import timezone

from authentication.models import PasswordResetAttempt, PasswordResetToken


pytestmark = pytest.mark.django_db


def test_password_reset_attempt_not_rate_limited_below_threshold():
    email = "unit-rate-limit@example.com"

    for _ in range(2):
        PasswordResetAttempt.objects.create(email=email)

    is_limited, seconds_remaining = PasswordResetAttempt.is_rate_limited(email)

    assert is_limited is False
    assert seconds_remaining == 0


def test_password_reset_attempt_rate_limit_resets_after_time_window():
    email = "unit-rate-limit-expire@example.com"
    now = timezone.now()

    attempts = [PasswordResetAttempt.objects.create(email=email) for _ in range(3)]

    # Make the oldest attempt older than the rate limit window so only two recent attempts remain
    oldest_attempt = attempts[-1]
    PasswordResetAttempt.objects.filter(pk=oldest_attempt.pk).update(created_at=now - timedelta(minutes=11))

    is_limited, _ = PasswordResetAttempt.is_rate_limited(email)

    assert is_limited is False


def test_cleanup_old_attempts_removes_records_older_than_ten_minutes():
    email = "unit-cleanup@example.com"
    now = timezone.now()

    recent_attempt = PasswordResetAttempt.objects.create(email=email)
    old_attempt = PasswordResetAttempt.objects.create(email=email)
    PasswordResetAttempt.objects.filter(pk=old_attempt.pk).update(created_at=now - timedelta(minutes=11))

    PasswordResetAttempt.cleanup_old_attempts()

    assert PasswordResetAttempt.objects.filter(pk=old_attempt.pk).count() == 0
    assert PasswordResetAttempt.objects.filter(pk=recent_attempt.pk).count() == 1


def test_user_profile_created_when_user_is_created():
    user = User.objects.create_user(
        username="unit_user_profile",
        email="unit_user_profile@example.com",
        password="StrongPass123!",
    )

    assert hasattr(user, "profile")
    assert user.profile.memorable_information == ""


def test_password_reset_token_validity_and_usage():
    user = User.objects.create_user(
        username="unit_token_user",
        email="unit_token_user@example.com",
        password="StrongPass123!",
    )

    token = PasswordResetToken.objects.create(
        user=user,
        token="unit-token",
        expires_at=timezone.now() + timedelta(hours=1),
    )

    assert token.is_valid() is True

    token.is_used = True
    token.save()
    assert token.is_valid() is False

    token.is_used = False
    token.expires_at = timezone.now() - timedelta(minutes=1)
    token.save()
    assert token.is_valid() is False
