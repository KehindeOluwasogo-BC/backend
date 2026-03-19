import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from authentication.models import AccountHistory, PasswordResetAttempt, PasswordResetToken


pytestmark = pytest.mark.django_db


def test_register_endpoint_creates_user_profile_and_returns_tokens():
    client = APIClient()
    payload = {
        "username": "integration_user",
        "email": "integration_user@example.com",
        "password": "StrongPass123!",
        "first_name": "Integration",
        "last_name": "User",
        "memorable_information": "first-school",
    }

    response = client.post("/api/auth/register/", payload, format="json")

    assert response.status_code == 201
    assert "access" in response.data
    assert "refresh" in response.data

    user = User.objects.get(username=payload["username"])
    assert hasattr(user, "profile")
    assert user.profile.memorable_information == payload["memorable_information"]

    history = AccountHistory.objects.get(user=user)
    assert history.event_type == "CREATED"


def test_password_reset_request_returns_429_when_rate_limited():
    user = User.objects.create_user(
        username="reset_target",
        email="reset_target@example.com",
        password="StrongPass123!",
    )

    for _ in range(3):
        PasswordResetAttempt.objects.create(email=user.email)

    client = APIClient()
    response = client.post(
        "/api/auth/password-reset/request/",
        {"email": user.email},
        format="json",
    )

    assert response.status_code == 429
    assert response.data["rate_limited"] is True
    assert "retry_message" in response.data


def test_password_reset_request_creates_token_and_sends_email(monkeypatch):
    user = User.objects.create_user(
        username="reset_target_success",
        email="reset_success@example.com",
        password="StrongPass123!",
    )

    sent = {}

    def fake_send_password_reset_email(user_email, token):
        # capture that it was called with a token and return success
        sent["email"] = user_email
        sent["token"] = token
        return True

    # Patch the view's send_password_reset_email helper so we don't hit SendGrid.
    import authentication.views as auth_views

    monkeypatch.setattr(
        auth_views,
        "send_password_reset_email",
        fake_send_password_reset_email,
    )

    client = APIClient()
    response = client.post(
        "/api/auth/password-reset/request/",
        {"email": user.email},
        format="json",
    )

    assert response.status_code == 200
    assert response.data["message"].startswith("Password reset email sent")

    # Ensure a token record was created and the helper was invoked
    assert PasswordResetToken.objects.filter(user=user).exists()
    assert sent["email"] == user.email
    assert "token" in sent


def test_token_obtain_and_refresh_work():
    user = User.objects.create_user(
        username="token_user",
        email="token_user@example.com",
        password="StrongPass123!",
    )

    client = APIClient()

    # Obtain token pair
    response = client.post(
        "/api/auth/token/",
        {"username": user.username, "password": "StrongPass123!"},
        format="json",
    )

    assert response.status_code == 200
    assert "access" in response.data
    assert "refresh" in response.data

    # Refresh access token
    refresh_token = response.data["refresh"]
    response_refresh = client.post(
        "/api/auth/token/refresh/",
        {"refresh": refresh_token},
        format="json",
    )

    assert response_refresh.status_code == 200
    assert "access" in response_refresh.data


def test_validate_reset_token_endpoint():
    user = User.objects.create_user(
        username="validate_user",
        email="validate_user@example.com",
        password="StrongPass123!",
    )

    token_obj = PasswordResetToken.objects.create(
        user=user,
        token="validate-token",
        expires_at=None,  # will be set automatically
    )

    client = APIClient()
    response = client.post(
        "/api/auth/password-reset/validate/",
        {"token": token_obj.token},
        format="json",
    )

    assert response.status_code == 200
    assert response.data["valid"] is True


def test_confirm_reset_token_changes_password():
    user = User.objects.create_user(
        username="confirm_user",
        email="confirm_user@example.com",
        password="StrongPass123!",
    )

    token_obj = PasswordResetToken.objects.create(
        user=user,
        token="confirm-token",
        expires_at=None,
    )

    client = APIClient()
    response = client.post(
        "/api/auth/password-reset/confirm/",
        {"token": token_obj.token, "new_password": "NewStrongPass123!"},
        format="json",
    )

    assert response.status_code == 200
    user.refresh_from_db()
    assert user.check_password("NewStrongPass123!")


def test_update_profile_picture_endpoint():
    user = User.objects.create_user(
        username="picture_user",
        email="picture_user@example.com",
        password="StrongPass123!",
    )

    client = APIClient()
    client.force_authenticate(user=user)

    payload = {"profile_picture": "https://example.com/avatar.png"}
    response = client.post(
        "/api/auth/profile/picture/", payload, format="json"
    )

    assert response.status_code == 200
    assert response.data["profile_picture"] == payload["profile_picture"]

    user.refresh_from_db()
    assert user.profile.profile_picture == payload["profile_picture"]


def test_auth_root_endpoint_returns_expected_keys():
    client = APIClient()
    response = client.get("/api/auth/")

    assert response.status_code == 200
    assert "endpoints" in response.data
    assert "register" in response.data["endpoints"]
    assert "token" in response.data["endpoints"]


def test_admin_create_and_list_and_revoke_work(monkeypatch):
    admin = User.objects.create_superuser(
        username="admin_user",
        email="admin_user@example.com",
        password="StrongPass123!",
    )

    client = APIClient()
    client.force_authenticate(user=admin)

    # Create a new admin via endpoint
    payload = {
        "username": "new_admin",
        "email": "new_admin@example.com",
        "password": "StrongPass123!",
        "first_name": "New",
        "last_name": "Admin",
        "can_revoke_admins": True,
        "memorable_information": "admin-info",
    }

    response = client.post("/api/auth/admin/create/", payload, format="json")
    assert response.status_code == 201
    assert response.data["user"]["username"] == payload["username"]

    new_admin_id = response.data["user"]["id"]

    # List admins should include the newly created admin
    response = client.get("/api/auth/admin/list/")
    assert response.status_code == 200
    assert any(item["id"] == new_admin_id for item in response.data["admins"])

    # Revoke the new admin privileges
    response = client.post("/api/auth/admin/revoke/", {"user_id": new_admin_id}, format="json")
    assert response.status_code == 200

    updated_user = User.objects.get(id=new_admin_id)
    assert updated_user.is_superuser is False


def test_list_users_and_create_user_account_and_change_password_and_send_reset_link(monkeypatch):
    admin = User.objects.create_superuser(
        username="list_admin",
        email="list_admin@example.com",
        password="StrongPass123!",
    )

    client = APIClient()
    client.force_authenticate(user=admin)

    # Create a regular user via endpoint
    payload = {
        "username": "created_user",
        "email": "created_user@example.com",
        "password": "StrongPass123!",
        "first_name": "Created",
        "last_name": "User",
    }

    response = client.post("/api/auth/users/create/", payload, format="json")
    assert response.status_code == 201

    created_user_id = response.data["user"]["id"]

    # List users should include the new regular user
    response = client.get("/api/auth/users/list/")
    assert response.status_code == 200
    assert any(item["id"] == created_user_id for item in response.data["users"])

    # Change password for the new user
    response = client.post(
        "/api/auth/users/change-password/",
        {"user_id": created_user_id, "new_password": "BrandNewPass123!"},
        format="json",
    )
    assert response.status_code == 200

    created_user = User.objects.get(id=created_user_id)
    assert created_user.check_password("BrandNewPass123!") is True

    # Patch send_password_reset_email for reset link flow
    sent = {}

    def fake_send_password_reset_email(user_email, token):
        sent["email"] = user_email
        sent["token"] = token
        return True

    import authentication.views as auth_views

    monkeypatch.setattr(
        auth_views,
        "send_password_reset_email",
        fake_send_password_reset_email,
    )

    response = client.post(
        "/api/auth/users/send-reset-link/",
        {"user_id": created_user_id},
        format="json",
    )

    assert response.status_code == 200
    assert sent["email"] == created_user.email
    assert "token" in sent


def test_toggle_user_active_and_prevent_self_restriction():
    admin = User.objects.create_superuser(
        username="toggle_admin",
        email="toggle_admin@example.com",
        password="StrongPass123!",
    )
    target = User.objects.create_user(
        username="toggle_target",
        email="toggle_target@example.com",
        password="StrongPass123!",
    )

    client = APIClient()
    client.force_authenticate(user=admin)

    # Restrict the target user
    response = client.post(
        "/api/auth/users/toggle-active/", {"user_id": target.id}, format="json"
    )
    assert response.status_code == 200
    assert response.data["is_active"] is False

    target.refresh_from_db()
    assert target.is_active is False

    # Prevent self restriction
    response = client.post(
        "/api/auth/users/toggle-active/", {"user_id": admin.id}, format="json"
    )
    assert response.status_code == 400


def test_token_obtain_invalid_credentials_returns_401():
    user = User.objects.create_user(
        username="token_user2",
        email="token_user2@example.com",
        password="StrongPass123!",
    )

    client = APIClient()
    response = client.post(
        "/api/auth/token/",
        {"username": user.username, "password": "WrongPassword"},
        format="json",
    )

    assert response.status_code == 401
    assert "access" not in response.data
    assert "refresh" not in response.data


def test_token_refresh_with_invalid_token_returns_401():
    client = APIClient()
    response = client.post(
        "/api/auth/token/refresh/",
        {"refresh": "invalid-token"},
        format="json",
    )

    assert response.status_code == 401


def test_validate_reset_token_with_invalid_token_returns_400():
    client = APIClient()
    response = client.post(
        "/api/auth/password-reset/validate/",
        {"token": "invalid-token"},
        format="json",
    )

    assert response.status_code == 400
    assert response.data.get("valid") is False


def test_confirm_reset_with_invalid_token_returns_400():
    client = APIClient()
    response = client.post(
        "/api/auth/password-reset/confirm/",
        {"token": "invalid-token", "new_password": "AnotherPass123!"},
        format="json",
    )

    assert response.status_code == 400


def test_change_password_endpoint_rejects_non_superuser():
    user = User.objects.create_user(
        username="normal_user",
        email="normal_user@example.com",
        password="StrongPass123!",
    )
    target = User.objects.create_user(
        username="target_user",
        email="target_user@example.com",
        password="StrongPass123!",
    )

    client = APIClient()
    client.force_authenticate(user=user)

    response = client.post(
        "/api/auth/users/change-password/",
        {"user_id": target.id, "new_password": "NewPass123!"},
        format="json",
    )

    assert response.status_code == 403


def test_send_reset_link_rejects_non_superuser():
    user = User.objects.create_user(
        username="normal_user2",
        email="normal_user2@example.com",
        password="StrongPass123!",
    )
    target = User.objects.create_user(
        username="target_user2",
        email="target_user2@example.com",
        password="StrongPass123!",
    )

    client = APIClient()
    client.force_authenticate(user=user)

    response = client.post(
        "/api/auth/users/send-reset-link/",
        {"user_id": target.id},
        format="json",
    )

    assert response.status_code == 403


def test_send_reset_link_requires_user_id_and_email():
    admin = User.objects.create_superuser(
        username="send_link_admin",
        email="send_link_admin@example.com",
        password="StrongPass123!",
    )
    user_no_email = User.objects.create_user(
        username="no_email_user",
        email="",
        password="StrongPass123!",
    )

    client = APIClient()
    client.force_authenticate(user=admin)

    # missing user_id
    response = client.post(
        "/api/auth/users/send-reset-link/", {}, format="json"
    )
    assert response.status_code == 400

    # user exists but has no email
    response = client.post(
        "/api/auth/users/send-reset-link/",
        {"user_id": user_no_email.id},
        format="json",
    )
    assert response.status_code == 400


def test_toggle_user_active_rejects_non_superuser():
    user = User.objects.create_user(
        username="normal_user3",
        email="normal_user3@example.com",
        password="StrongPass123!",
    )
    target = User.objects.create_user(
        username="target_user3",
        email="target_user3@example.com",
        password="StrongPass123!",
    )

    client = APIClient()
    client.force_authenticate(user=user)

    response = client.post(
        "/api/auth/users/toggle-active/", {"user_id": target.id}, format="json"
    )
    assert response.status_code == 403
