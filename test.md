# Test Coverage Summary

This repository contains a total of **33 comprehensive tests** across unit, integration, and BDD layers, ensuring enterprise-quality reliability and security.

---

## Test Distribution

| Test Type | Count | Focus |
|-----------|-------|-------|
| **Unit Tests** | 8 | Business logic, models, validators |
| **Integration Tests** | 23 | API endpoints, real request/response cycles |
| **BDD Tests** | 2 | Feature-based acceptance scenarios |
| **Total** | **33** | ✅ All Passing |

---

## Authentication Tests (5 Unit + 14 Integration)

### Unit Tests (Models & Serializers)
1. **Rate Limiting Logic** - Verifies that 3+ password reset attempts within 10 minutes triggers rate limit
2. **Rate Limit Expiration** - Confirms rate limit resets after 10-minute window expires
3. **Old Attempts Cleanup** - Validates automatic deletion of reset attempts older than 10 minutes
4. **User Profile Auto-Creation** - Confirms Django signal creates UserProfile when User is created
5. **Password Reset Token Validity** - Tests token expiration, usage tracking, and validity checks

### Integration Tests (API Endpoints)
6. **User Registration** - POST `/api/auth/register/` creates user, profile, returns JWT tokens, logs account history
7. **JWT Token Obtain** - POST `/api/auth/token/` returns access/refresh tokens for valid credentials
8. **JWT Token Refresh** - POST `/api/auth/token/refresh/` rotates access token using refresh token
9. **Invalid Credentials Rejection** - Token endpoint returns 401 for wrong password
10. **Invalid Token Refresh** - Refresh endpoint rejects malformed/invalid refresh tokens
11. **Password Reset Request (Success)** - POST `/api/auth/password-reset/request/` creates token, sends email
12. **Password Reset Rate Limiting** - Rate-limited email returns 429 with retry_message
13. **Reset Token Validation** - POST `/api/auth/password-reset/validate/` confirms token validity
14. **Invalid Reset Token Handling** - Validation endpoint rejects non-existent/expired tokens
15. **Password Reset Confirm** - POST `/api/auth/password-reset/confirm/` updates user password successfully
16. **Profile Picture Update** - POST `/api/auth/profile/picture/` stores profile URL in UserProfile
17. **Auth Root Endpoint** - GET `/api/auth/` returns available endpoints directory
18. **Admin Create** - POST `/api/auth/admin/create/` creates superuser (superuser only, logs activity)
19. **Admin List** - GET `/api/auth/admin/list/` returns all superusers (superuser only)
20. **Admin Revoke** - POST `/api/auth/admin/revoke/` removes superuser status (prevents self-revocation)
21. **Password Change (Admin)** - POST `/api/auth/users/change-password/` updates user password (superuser only)
22. **Send Reset Link (Admin)** - POST `/api/auth/users/send-reset-link/` triggers email, handles missing user/email
23. **Toggle User Active** - POST `/api/auth/users/toggle-active/` restricts/unrestricts accounts, prevents self-restriction
24. **Permission Rejection** - Non-superusers get 403 Forbidden for admin endpoints (change-password, send-reset-link, toggle-active)

---

## Booking Tests (3 Unit + 4 Integration)

### Unit Tests (Serializer Business Logic)
25. **User Cannot Override Status (Non-Pending)** - Regular user updating booking with status forcibly resets to pending
26. **User Cannot Override Status (Already Pending)** - Regular user updating pending booking maintains pending status
27. **Superuser Can Update Status** - Admin user can set booking status to confirmed/completed/cancelled

### Integration Tests (API Endpoints)
28. **Admin Create Booking for User** - POST `/api/bookings/` with `user_id` creates booking for target user (admin only)
29. **User Cannot Create for Others** - Regular user sending `user_id` has it ignored; booking assigned to self
30. **User Sees Only Own Bookings** - GET `/api/bookings/` returns only authenticated user's bookings
31. **Admin Sees All Bookings** - GET `/api/bookings/` returns all system bookings for superuser

---

## BDD Tests (Feature Scenarios)

32. **Profile Retrieval** - Authenticated user can GET `/api/auth/user/` and receive their profile info
33. **Booking Visibility** - Regular user list endpoint enforces booking isolation (user sees only their bookings)

---

## Running the Test Suite

### Run All Tests
```bash
pytest
```

### Run with Verbose Output
```bash
pytest -v
```

### Run Specific Test File
```bash
pytest authentication/tests/test_auth_unit.py
pytest authentication/tests/test_auth_integration.py
pytest booking/tests/test_booking_unit.py
```

### Run with Coverage Report
```bash
coverage run -m pytest
coverage report -m
coverage html  # Generate HTML report
```

### Run Only Integration Tests
```bash
pytest -k "integration"
```

### Run Only Unit Tests
```bash
pytest -k "unit"
```

---

## Test Organization

Tests are organized by layer and domain for clarity and maintainability:

```
authentication/tests/
├── test_auth_unit.py           # 5 pure business logic tests
├── test_auth_integration.py    # 14 API endpoint tests
├── test_bdd_authentication.py  # 1 feature-based test
└── features/
    └── auth_user_info.feature   # Gherkin feature file

booking/tests/
├── test_booking_unit.py      # 3 pure business logic tests
├── test_booking_integration.py # 4 API endpoint tests
├── test_bdd_booking.py       # 1 feature-based test
└── features/
    └── booking_visibility.feature # Gherkin feature file
```

---

## Continuous Integration

GitHub Actions runs the full test suite automatically on every push and pull request to `main`/`develop` branches:
- ✅ Tests run on Python 3.10 and 3.11
- ✅ PostgreSQL database service for integration test isolation
- ✅ Code quality checks (Black formatting, Flake8 linting)
- ✅ Coverage reports uploaded to Codecov

See [.github/workflows/ci.yml](.github/workflows/ci.yml) for full configuration.

---

## What's Being Tested & Why

| Feature | Why It Matters | Test Type |
|---------|----------------|-----------|
| **Password Reset Rate Limiting** | Prevents brute-force attacks | Unit + Integration |
| **Token Expiration** | Ensures temporary access; stale tokens become invalid | Unit + Integration |
| **Role-Based Access Control** | Users cannot escalate privileges or access others' data | Integration |
| **Status Enforcement** | Business rule: regular users cannot confirm their own bookings | Unit + Integration |
| **Booking Visibility** | Data isolation: users only see their own bookings | Unit + Integration |
| **Email Integration** | SendGrid delivery is triggered and mocked in tests (no real emails) | Integration |
| **Admin Activity Logging** | Audit trail for compliance and security monitoring | Integration |
| **Password Validation** | Strong password enforcement (length, complexity) | Unit (implicit via validators) |

---

## Test Quality Metrics

- **Coverage**: Core authentication and booking logic fully covered
- **Isolation**: Tests use in-memory database fixtures; no side effects
- **Clarity**: Descriptive test names explaining what is being tested
- **Assertions**: Each test has multiple assertions validating different aspects
- **Error Cases**: Negative tests validate rejection of invalid inputs and unauthorized access
