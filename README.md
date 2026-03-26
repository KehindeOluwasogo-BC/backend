# ESE Booking System Backend API

Enterprise-grade backend service for booking management, authentication, and admin operations, built with Django and Django REST Framework.

## 📋 Quick Links

- **[API Documentation](API_DOCUMENTATION.md)** - Complete endpoint reference with request/response examples
- **[System Architecture](ARCHITECTURE.md)** - Architecture diagrams and design patterns
- **[Deployment Guide](DEPLOYMENT.md)** - Step-by-step production deployment instructions
- **[Database Schema](DATABASE_SCHEMA.md)** - Complete database structure and relationships
- **[Security Documentation](SECURITY.md)** - Authentication, authorization, and security practices

## Overview

This repository contains the secure, scalable API layer for the ESE booking system with:

- ✅ **Enterprise Authentication** - JWT tokens, password reset with rate limiting, role-based access control
- ✅ **User Management** - Registration, profiles, admin capabilities with audit logging
- ✅ **Booking System** - Full CRUD operations with permission-based filtering
- ✅ **Activity Logging** - Comprehensive audit trail for compliance and security
- ✅ **Production Ready** - Deployed on Render with PostgreSQL, comprehensive testing (30 tests)

## Tech Stack

- **Backend Framework**: Python 3.10+ with Django & Django REST Framework
- **Authentication**: JWT (Simple JWT library)
- **Database**: SQLite (development) | PostgreSQL (production via DATABASE_URL)
- **Email**: SendGrid integration for password reset emailsid
- **Deployment**: Gunicorn + WhiteNoise on Render
- **Testing**: Pytest with unit, integration, and BDD test coverage

All dependencies are listed in [requirements.txt](requirements.txt).

## 📁 Project Structure

```
backend/                → Django project settings and root URL configuration
authentication/         → User auth, password reset, admin/user management, logging
booking/               → Booking CRUD with role-based access control
staticfiles/           → Collected static files (admin, rest_framework)
manage.py              → Django management entrypoint
build.sh               → Build and migration script for Render deployment
```

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Virtual environment tool (`venv`)
- Git
- SendGrid account (optional, for email testing (**ALWAYS CHECK SPAM FOR EMAILS FROM SENDGRID**))

### Installation (5 minutes)

**1. Create Virtual Environment**
```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows
```

**2. Install Dependencies**
```bash
pip install -r requirements.txt
```

**3. Create Environment Variables**
```bash
# Copy template
cp .env.example .env  # if available, or create manually

# Edit .env with your values (see Environment Variables section)
nano .env
```

**4. Run Migrations**
```bash
python manage.py migrate
```

**5. Create Admin User (Optional)**
```bash
python manage.py createsuperuser
# Follow prompts to create admin account
```

**6. Start Development Server**
```bash
python manage.py runserver
```

API available at **http://localhost:8000/api**

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Django Settings
SECRET_KEY=your-secret-key-change-me
DEBUG=True                              # Set to False in production
ENVIRONMENT=development

# Database (SQLite for development)
DATABASE_URL=sqlite:///db.sqlite3      # Or PostgreSQL in production

# Security
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
CORS_ALLOWED_ORIGINS=http://localhost:3000
CSRF_TRUSTED_ORIGINS=http://localhost:3000

# Email Service (SendGrid)
SENDGRID_API_KEY=your-sendgrid-api-key
SENDGRID_FROM_EMAIL=noreply@example.com
FROM_EMAIL=noreply@example.com          # Alias for SENDGRID_FROM_EMAIL

# Frontend URL (for password reset links)
FRONTEND_URL=http://localhost:3000

# With HashRouter, reset links should have the format:
# FRONTEND_URL=http://localhost:3000/#/reset-password?token=...
```

**For Production (Render):** See [Deployment Guide](DEPLOYMENT.md#environment-setup)

---

## 📚 API Quick Reference

### Base URL
- Development: `http://localhost:8000/api`
### Production URLS
- **[Backend](https://backend-b2tz.onrender.com)**
- **[Fronten](https://new-frontend-rew2.onrender.com)**

### Public Endpoints (No Auth Required)
```
POST /auth/register/                    # Create user account
POST /auth/token/                       # Login (get tokens)
POST /auth/token/refresh/               # Refresh access token
POST /auth/password-reset/request/      # Request password reset email
POST /auth/password-reset/validate/     # Validate reset token
POST /auth/password-reset/confirm/      # Confirm password reset
```

### Authenticated User Endpoints
```
GET  /auth/user/                        # Get current user profile
POST /auth/profile/picture/             # Update profile picture
GET  /bookings/                         # List user's bookings
POST /bookings/                         # Create booking
GET  /bookings/{id}/                    # Get booking details
PUT  /bookings/{id}/                    # Update booking
PATCH /bookings/{id}/                   # Partial update booking
DELETE /bookings/{id}/                  # Delete booking
```

### Admin-Only Endpoints
```
POST /auth/admin/create/                # Create admin user
GET  /auth/admin/list/                  # List all admins
POST /auth/admin/revoke/                # Revoke admin privileges
GET  /auth/admin/activity-logs/         # View admin activity logs
GET  /auth/users/list/                  # List all users
POST /auth/users/create/                # Create user account
POST /auth/users/change-password/       # Reset user password
POST /auth/users/send-reset-link/       # Send reset email to user
POST /auth/users/toggle-active/         # Activate/deactivate user
```

**For full endpoint documentation with request/response examples, see [API Documentation](API_DOCUMENTATION.md)**

---

## 🔐 Authentication

**Token-Based JWT Flow:**
1. User registers or logs in
2. Backend issues Access Token (5 min) + Refresh Token (24 hrs)
3. Frontend includes Access Token: `Authorization: Bearer <token>`
4. Token expires → use Refresh Token to get new Access Token
5. User re-logs in when Refresh Token expires

**Password Reset Security:**
- Rate limited: 3 attempts per 10 minutes
- One-time tokens: Valid for 1 hour only
- Secure delivery: Via SendGrid email
- No token reuse: Marked as used after reset

For detailed authentication, authorization, and token management, see [Security Documentation](SECURITY.md).

---

## 🛡️ Security Features

This application implements enterprise-grade security practices:

| Feature | Implementation |
|---------|-----------------|
| **JWT Authentication** | djangorestframework-simplejwt with short-lived tokens |
| **Password Hashing** | PBKDF2-SHA256 with 260,000+ iterations |
| **Rate Limiting** | 3 password reset attempts per 10 minutes |
| **Role-Based Access** | Superuser vs regular user with granular endpoint protection |
| **Audit Logging** | AdminActivityLog tracks all admin actions with IP addresses |
| **Input Validation** | Serializer-level validation prevents invalid data |
| **CORS Protection** | Restricted to configured frontend origins only |
| **CSRF Protection** | Django middleware with trusted origins configuration |
| **Token Expiration** | Single-use password reset tokens with 1-hour lifetime |
| **Environment Variables** | Secrets never hardcoded (loaded from .env) |

**→ Full security details in [Security Documentation](SECURITY.md)**

---

## 🧪 Testing

The project includes **30 comprehensive tests** across unit, integration, and BDD layers:

- **5 Unit Tests**: Password rate limiting, token validation, profile creation
- **23 Integration Tests**: Full API workflows with permissions and error handling
- **2 BDD Tests**: Feature-based acceptance scenarios

### Running Tests Locally

```bash
# Run all tests with verbose output
pytest -v

# Run specific test file
pytest authentication/tests/test_auth_unit.py

# Generate coverage report
coverage run -m pytest
coverage report
```

### Continuous Integration

Tests automatically run on GitHub with:
- ✅ Python 3.10 & 3.11
- ✅ PostgreSQL service for integration tests
- ✅ Code formatting checks (Black)
- ✅ Linting checks (Flake8)

See [test.md](test.md) for detailed test coverage report.

---

## 📦 Deployment

### Development
```bash
python manage.py runserver
# Runs on http://localhost:8000
```

### Production (Render)

The application is deployed on [Render](https://render.com) with PostgreSQL. You are required to set up a render account to deploy your application.

You can test my application at:

**Production URL:** 
**[Frontend](https://new-frontend-rew2.onrender.com/)**
**[Backend](https://backend-b2tz.onrender.com/)**

**Quick Deploy Steps:**
1. Push to `main` branch
2. Render automatically builds and deploys
3. See [Deployment Guide](DEPLOYMENT.md) for detailed instructions, troubleshooting, and monitoring

I have already setup an admin account for you to test:
**Pre-Configured Admin Credentials (Testing Only):**
```
Email: Sirkeno@gmail.com
Password: Sirkeno7991!
```

But you'll have to register a user account to make CRUD Operations.


**Production Deployment Checklist:**
- ✅ DEBUG set to False
- ✅ SECRET_KEY from environment variables
- ✅ ALLOWED_HOSTS configured correctly
- ✅ PostgreSQL database connected
- ✅ Static files served via WhiteNoise
- ✅ CORS restricted to frontend domain
- ✅ CSRF protection enabled
- ✅ SendGrid integrated for email delivery
- ✅ Gunicorn configured for production workloads

---

## 🏗️ Architecture

The system uses a modular, scalable architecture:

```
Frontend (React with HashRouter)
         ↓
    REST API (Django + DRF)
         ↓
  Authentication + Booking Apps
         ↓
    PostgreSQL Database
         ↓
    SendGrid Email Service
```

**Key Design Decisions:**
- JWT tokens for stateless authentication
- Role-Based Access Control (admin vs regular user)
- Modular Django apps for maintainability
- Separate serializers for API validation
- Comprehensive audit logging for compliance

See [System Architecture](ARCHITECTURE.md) for detailed diagram and design rationale.

---

## 📊 Data Models

Core entities:

| Model | Purpose |
|-------|---------|
| **User** | Django built-in with email, username, superuser flag |
| **UserProfile** | Extended user data: picture, bio, memorable_information |
| **Booking** | Service booking with date, time, status, notes |
| **PasswordResetToken** | One-time password reset tokens (1-hour expiration) |
| **AdminActivityLog** | Audit trail: admin actions, targets, IPs, timestamps |
| **AccountHistory** | Account lifecycle events (created, revoked, restricted) |

For complete schema with relationships and indexes, see [Database Schema](DATABASE_SCHEMA.md).

---

## 🔧 How to Use the Application

### User Workflow

**1. Registration**
```bash
POST /api/auth/register/
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "SecurePass123!",
  "first_name": "John",
  "last_name": "Doe"
}
# Response: access & refresh tokens
```

**2. Login**
```bash
POST /api/auth/token/
{
  "username": "john_doe",
  "password": "SecurePass123!"
}
# Response: access & refresh tokens
```

**3. View Profile**
```bash
GET /api/auth/user/
Authorization: Bearer <access_token>
```

**4. Create Booking**
```bash
POST /api/bookings/
Authorization: Bearer <access_token>
{
  "booking_date": "2026-04-15",
  "booking_time": "10:00:00",
  "service_type": "Haircut"
}
```

**5. Password Reset**
```bash
# Step 1: Request reset
POST /api/auth/password-reset/request/
{ "email": "john@example.com" }

# Step 2: User receives email with token link

# Step 3: Validate token
POST /api/auth/password-reset/validate/
{ "token": "ABC123..." }

# Step 4: Confirm reset with new password
POST /api/auth/password-reset/confirm/
{
  "token": "ABC123...",
  "new_password": "NewPass456!"
}
```

### Admin Workflow

Admins have additional capabilities:

```bash
# Create other admin users
POST /api/auth/admin/create/

# Create regular user accounts
POST /api/auth/users/create/

# Manage all bookings (view/update/delete)
GET/PUT/PATCH/DELETE /api/bookings/

# View admin activity logs
GET /api/auth/admin/activity-logs/

# View and manage user accounts
GET /api/auth/users/list/
POST /api/auth/users/change-password/
POST /api/auth/users/toggle-active/
```

---

## � Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **JWT Tokens** | Stateless auth enables horizontal scaling; works with SPAs and mobile apps |
| **Role-Based Access** | Simple two-tier system (admin/user); extensible to ABAC if needed |
| **Serializer Validation** | DRF best practice; keeps API logic away from models |
| **Rate Limiting** | Custom implementation; prevents brute force without external dependencies |
| **Audit Logging** | Explicit AdminActivityLog & AccountHistory for compliance and debugging |
| **Environment Config** | 12-factor app; secrets never in code, works across dev/staging/prod |
| **Modular Apps** | Independent auth & booking apps; can extract or scale separately |
| **PostgreSQL in Prod** | Better concurrency and scaling than SQLite; professional backups |
| **Gunicorn + WhiteNoise** | Production-tested WSGI; simple static file serving; fits free tier |

For detailed explanations of all 10 design decisions, see [System Architecture](ARCHITECTURE.md#key-technical-decisions).

---

## 📖 Complete Documentation

Every aspect of the system is documented:

| Document | Contents |
|----------|----------|
| **[API_DOCUMENTATION.md](API_DOCUMENTATION.md)** | All endpoints with request/response examples, error codes |
| **[ARCHITECTURE.md](ARCHITECTURE.md)** | System design, component interactions, data flows, diagrams |
| **[DEPLOYMENT.md](DEPLOYMENT.md)** | Render deployment, environment setup, monitoring, troubleshooting |
| **[DATABASE_SCHEMA.md](DATABASE_SCHEMA.md)** | Models, relationships, indexes, query examples, migrations |
| **[SECURITY.md](SECURITY.md)** | Authentication, authorization, token handling, incident response |
| **[test.md](test.md)** | Test coverage by module, running tests, CI/CD info |

---

## 🙏 Acknowledgments

This project benefited from **GitHub Copilot** and **ChatGPT** as development assistants for:
- Framework and DRF pattern guidance
- Code generation for boilerplate and tests
- Documentation structure and refinement
- Authentication flow debugging

**All code has been thoroughly reviewed and tested.** Full responsibility taken for all implementation.

---

## 👨‍💻 Author

**Kehinde Oluwasogo**
- GitHub: https://github.com/KehindeOluwasogo-BC

---

## 📝 License

[Add your license here if applicable]

---

## 📞 Support

For issues, questions, or contributions:
1. Check the relevant documentation file
2. Review [Deployment Guide](DEPLOYMENT.md#troubleshooting) for common issues
3. Check test files in `authentication/tests/` and `booking/tests/` for usage examples
