# ESE Booking System Backend API

Backend service for booking management, authentication, and admin operations, built with Django and Django REST Framework.

## Overview

This repository contains the API layer for the ESE booking system. It includes:

- JWT authentication
- User registration and profile retrieval
- Password reset flow with token validation
- Super-admin user and admin management endpoints
- Booking CRUD endpoints with role-aware behavior
- Admin and account activity logging

## Tech Stack

- Python
- Django
- Django REST Framework
- Simple JWT
- SendGrid (email delivery)
- SQLite (default) or PostgreSQL via DATABASE_URL
- Gunicorn + WhiteNoise (production serving)

Dependencies are listed in [requirements.txt](requirements.txt).

## Project Structure

- [backend](backend): Django project settings and root URL configuration
- [authentication](authentication): auth, password reset, admin/user management, logging
- [booking](booking): booking model, serializer, and viewset
- [manage.py](manage.py): Django management entrypoint
- [build.sh](build.sh): build/deploy helper script

## Setup

1. Clone repository and move into project directory.
2. Create and activate a virtual environment.
3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create environment variables (see next section).
5. Apply migrations:

```bash
python manage.py migrate
```

6. Create admin user (optional, recommended):

```bash
python manage.py createsuperuser
```

7. Start development server:

```bash
python manage.py runserver
```

API is available at http://localhost:8000.

## Environment Variables

Create a .env file at project root (same level as [manage.py](manage.py)).

```env
SECRET_KEY=change-me
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# Database
DATABASE_URL=sqlite:///db.sqlite3

# Email
SENDGRID_API_KEY=your-sendgrid-api-key
SENDGRID_FROM_EMAIL=noreply@example.com
# Optional alias used by settings
FROM_EMAIL=noreply@example.com

# URL used to build password reset links in email
FRONTEND_URL=http://localhost:3000

# CORS / CSRF (mainly for non-debug or hosted clients)
CORS_ALLOWED_ORIGINS=http://localhost:3000
CSRF_TRUSTED_ORIGINS=http://localhost:3000
```

## API Routes

Base root:

- /admin/
- /api/
- /api/auth/

Authentication routes are defined in [authentication/urls.py](authentication/urls.py).

### Public Authentication Endpoints

- POST /api/auth/token/
- POST /api/auth/token/refresh/
- POST /api/auth/register/
- POST /api/auth/password-reset/request/
- POST /api/auth/password-reset/validate/
- POST /api/auth/password-reset/confirm/

### Authenticated User Endpoints

- GET /api/auth/user/
- POST /api/auth/profile/picture/

### Super Admin Endpoints

- POST /api/auth/admin/create/
- GET /api/auth/admin/list/
- POST /api/auth/admin/revoke/
- GET /api/auth/admin/activity-logs/
- GET /api/auth/users/list/
- POST /api/auth/users/create/
- POST /api/auth/users/change-password/
- POST /api/auth/users/send-reset-link/
- POST /api/auth/users/toggle-active/

### Booking Endpoints

The bookings API is provided by a DRF router in [backend/urls.py](backend/urls.py):

- GET /api/bookings/
- POST /api/bookings/
- GET /api/bookings/{id}/
- PUT /api/bookings/{id}/
- PATCH /api/bookings/{id}/
- DELETE /api/bookings/{id}/

Behavior summary:

- Regular users only see and manage their own bookings.
- Super admins can view all bookings.
- Super admins may create bookings for another user by passing user_id.

## Data Model Summary

Core models are defined in [authentication/models.py](authentication/models.py) and [booking/models.py](booking/models.py):

- UserProfile
- PasswordResetToken
- PasswordResetAttempt
- AdminActivityLog
- AccountHistory
- Booking

## Security Features

This application implements enterprise-grade security practices:

### Authentication & Authorization
- **JWT Token-Based Authentication**: Secure, stateless Bearer token authentication using `djangorestframework-simplejwt`
- **Role-Based Access Control**: Superusers vs. regular users with granular endpoint protection
- **Password Hashing**: Django's PBKDF2 hashing with salted keys (secure by default)
- **Password Validation**: Built-in Django validators enforcing minimum length, complexity, and preventing common/dictionary passwords

### Rate Limiting
- **Password Reset Rate Limiting**: Maximum 3 password reset attempts in 10 minutes; further attempts return HTTP 429 (Too Many Requests)
- **Prevents Brute Force Attacks**: Automatic throttling with time-remaining feedback to client

### Activity Logging & Audit Trail
- **AdminActivityLog**: Tracks all admin actions (create admin, revoke privileges, password changes, etc.)
- **AccountHistory**: Logs account lifecycle events (creation, revocation, restriction/unrestriction)
- **IP Address Capture**: Client IP captured for audit trail investigation

### Input Validation & Error Handling
- **Server-Side Validation**: Serializer-level validation for all inputs (email format, password strength, required fields)
- **Clear Error Messages**: Detailed, actionable error responses without exposing sensitive system details
- **Token Expiration**: Reset tokens expire after 1 hour; already-used tokens cannot be reused

### Network Security
- **CORS Protection**: Configured for specific frontend origins only; no wildcard origins in production
- **CSRF Protection**: Django's CSRF middleware enabled with trusted origins configuration
- **Environment-Based Secrets**: All sensitive data (API keys, database credentials) loaded from environment variables, never hardcoded

### External Service Integration
- **SendGrid Email**: Password reset tokens delivered securely via SendGrid (not stored in emails)
- **Token Validation**: Time-bound, single-use tokens prevent unauthorized password resets

## How to Use the Application

### User Flow

1. **Registration**
   - Send POST request to `/api/auth/register/` with username, email, password, and optional profile fields
   - Receives JWT access and refresh tokens
   - UserProfile is automatically created

2. **Login**
   - Send POST request to `/api/auth/token/` with username and password
   - Receive JWT access token (for API requests) and refresh token (to obtain new access tokens)

3. **Manage Profile**
   - GET `/api/auth/user/` to view authenticated user info
   - POST `/api/auth/profile/picture/` to update profile picture URL

4. **Password Reset**
   - POST `/api/auth/password-reset/request/` with email to trigger reset email
   - Check email for reset link (sent via SendGrid)
   - POST `/api/auth/password-reset/validate/` to verify token is valid
   - POST `/api/auth/password-reset/confirm/` with token and new password to reset

5. **Create & Manage Bookings**
   - GET `/api/bookings/` to view your bookings
   - POST `/api/bookings/` to create a new booking with date, time, service details
   - PATCH `/api/bookings/{id}/` to update booking notes (status resets to pending)
   - DELETE `/api/bookings/{id}/` to cancel a booking
   - *Admin Note*: Admins can see all bookings and override status changes

6. **Token Refresh**
   - Access tokens expire after a short period
   - POST `/api/auth/token/refresh/` with refresh token to obtain a new access token

### Admin User Flow

Admins have additional capabilities:
- Create other admin users: POST `/api/auth/admin/create/`
- Revoke admin privileges: POST `/api/auth/admin/revoke/`
- Create regular user accounts: POST `/api/auth/users/create/`
- Change user passwords: POST `/api/auth/users/change-password/`
- Send password reset links to users: POST `/api/auth/users/send-reset-link/`
- Restrict/unrestrict accounts: POST `/api/auth/users/toggle-active/`
- View all bookings and modify status: GET/PATCH `/api/bookings/`
- View admin activity logs: GET `/api/auth/admin/activity-logs/`

## Deployment

### Deployed on Render

This application is currently deployed on [Render](https://render.com) with a PostgreSQL database.

**Production API URL**: https://ese-booking-backend.onrender.com (or your Render service URL)

### Environment Variables on Render

The following environment variables are configured in the Render dashboard:

```env
SECRET_KEY=<Django secret key>
DEBUG=False
ALLOWED_HOSTS=ese-booking-backend.onrender.com,localhost
DATABASE_URL=<Render PostgreSQL connection URL>
SENDGRID_API_KEY=<SendGrid API key>
SENDGRID_FROM_EMAIL=noreply@example.com
FROMTAIL_URL=<Your React frontend URL on Render>
CORS_ALLOWED_ORIGINS=<Frontend Render URL>
CSRF_TRUSTED_ORIGINS=<Frontend Render URL>
```

### Pre-Configured Admin Account for Testing

**Important**: An admin account has been pre-configured on the live Render deployment for testing purposes. Reviewers should use these credentials to test admin functionality.

**Admin Login Credentials**:
- **Email**: `Sirkeno@gmail.com`
- **Password**: `Sirkeno7991!`

*Note*: New admin accounts cannot be created without superuser permissions. The system creator has seeded this account to allow reviewers to fully test admin functionality without requiring the ability to create new superusers.

### Production Deployment Checklist

- ✅ DEBUG set to False
- ✅ SECRET_KEY loaded from environment (not hardcoded)
- ✅ ALLOWED_HOSTS configured for production domain
- ✅ CORS_ALLOWED_ORIGINS restricted to frontend domain(s)
- ✅ CSRF_TRUSTED_ORIGINS set appropriately
- ✅ PostgreSQL database configured via DATABASE_URL
- ✅ SENDGRID_API_KEY configured for email delivery
- ✅ Static files served via WhiteNoise
- ✅ Gunicorn configured for production

### Build & Deploy Commands (Render)

**Build Command**:
```bash
pip install -r requirements.txt && python manage.py migrate && python manage.py collectstatic --noinput
```

**Start Command**:
```bash
gunicorn backend.wsgi:application
```

## Testing

The project includes **33 comprehensive tests** covering unit, integration, and BDD scenarios:

### Test Structure

- **Unit Tests** (8): Business logic validation
  - Password reset rate limiting logic
  - Token expiration and validity checks
  - User profile creation via signals
  - Serializer field validation and role enforcement

- **Integration Tests** (23): Full API endpoint coverage
  - User registration, login, and token refresh
  - Password reset flow (request, validate, confirm)
  - Admin endpoints (create, revoke, list, activity logs)
  - Booking CRUD with permissions
  - Error handling (invalid tokens, unauthorized access, missing fields)

- **BDD Tests** (2): Feature-based acceptance scenarios using pytest-bdd
  - Authentication profile retrieval
  - Booking visibility rules

### Running Tests Locally

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest authentication/tests/test_auth_unit.py

# Run with coverage report
coverage run -m pytest && coverage report
```

### Continuous Integration

GitHub Actions automatically runs the full test suite on every push and pull request to `main` or `develop` branches.
- ✅ Tests run on Python 3.10 and 3.11
- ✅ PostgreSQL database service for integration tests
- ✅ Code formatting checks (Black)
- ✅ Linting checks (Flake8)
- ✅ Coverage reports uploaded to Codecov

See [.github/workflows/ci.yml](.github/workflows/ci.yml) for full CI/CD configuration.

## Production Notes

- Build helper script: [build.sh](build.sh)
- Typical production start command:

```bash
gunicorn backend.wsgi:application --bind 0.0.0.0:8000
```

- Static files are collected to staticfiles and served with WhiteNoise.
- Set DEBUG=False and configure ALLOWED_HOSTS, CORS_ALLOWED_ORIGINS, and CSRF_TRUSTED_ORIGINS appropriately.

## AI Usage Acknowledgment

This project benefited from the use of **GitHub Copilot** and **ChatGPT** as development assistants. AI was instrumental in:

- **Framework Understanding**: Clarifying Django concepts, DRF patterns, and best practices for REST API design
- **Challenge Resolution**: Debugging authentication flows, serializer validation logic, and role-based access control
- **Code Generation**: Generating boilerplate for models, serializers, viewsets, and test cases that would require significant manual effort
- **Testing Strategy**: Designing unit, integration, and BDD test structures; generating test cases for edge cases and error scenarios
- **Documentation**: Helping structure and refine API documentation and README content

**Important**: All generated code has been thoroughly reviewed, tested, and verified for correctness, security, and alignment with enterprise standards. The developer takes full responsibility for all submitted work and understands every component of the implementation.

## Author

- Kehinde Oluwasogo
- GitHub: https://github.com/KehindeOluwasogo-BC