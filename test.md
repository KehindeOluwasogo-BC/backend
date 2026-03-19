# Test Coverage Summary

This repository contains a total of **25 tests** across unit, integration, and BDD layers.

## ✅ What’s Tested

### Authentication (Unit)
- Rate limiting logic for password reset attempts
- Cleanup of old password reset attempts
- Token validity and expiration behavior for password reset tokens
- User profile creation via `post_save` signal when a `User` is created

### Authentication (Integration)
- `/api/auth/register/` returns access/refresh tokens, creates a profile, and logs account creation
- JWT token endpoint (`/api/auth/token/`) returns refresh/access tokens, and `/api/auth/token/refresh/` rotates access
- Password reset request endpoint enforces rate limiting (returns `429`)
- Password reset request endpoint creates a token record and calls the email sender (mocked)
- Password reset validation endpoint (`/api/auth/password-reset/validate/`) verifies tokens
- Password reset confirm endpoint (`/api/auth/password-reset/confirm/`) changes the user password
- Profile picture update endpoint (`/api/auth/profile/picture/`) updates the user's profile
- Auth root endpoint (`/api/auth/`) returns the available endpoints
- Admin endpoints: create admin, list admins, revoke admin privileges
- User management endpoints: list users, create user, change user password, send reset link, and toggle user active state

### Booking (Unit)
- Regular users cannot force status changes (non-pending status resets to `pending`)
- Regular users cannot override status when a booking is already `pending`
- Superusers can update booking status normally

### Booking (Integration)
- Superuser can create a booking for another user using `user_id`
- Regular users cannot create bookings for other users (ignores supplied `user_id`)
- Regular users see only their own bookings in the list endpoint
- Superusers can list all bookings

### BDD (pytest-bdd feature tests)
- Authentication profile retrieval (authenticated user fetches own profile)
- Booking list visibility (user sees only their own bookings)
