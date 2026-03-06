# ESE Booking System - Backend API

A comprehensive Django REST Framework backend for an enterprise-grade booking system with advanced authentication and user management capabilities.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [Architecture](#architecture)
- [Installation](#installation)
- [Environment Configuration](#environment-configuration)
- [Running the Application](#running-the-application)
- [API Documentation](#api-documentation)
- [Database Models](#database-models)
- [Testing](#testing)
- [Deployment](#deployment)
- [Security Features](#security-features)
- [External Services](#external-services)
- [AI Usage Acknowledgment](#ai-usage-acknowledgment)

---

## 🎯 Overview

This Django REST Framework application provides a robust backend API for a booking management system with enterprise-level authentication, role-based access control, and comprehensive audit logging. The system supports multiple user roles (regular users and super admins) with granular permission controls.

---

## ✨ Features

### Authentication System
- **User Registration** with security questions
- **JWT-based Authentication** (access & refresh tokens)
- **Profile Management** with Cloudinary image uploads
- **Three-tier Password Reset System:**
  - Self-service email reset (SendGrid integration)
  - Admin-issued reset links
  - Admin direct password change
- **Security Questions** for account recovery

### Admin Management
- **Create Super Admins** with granular permissions
- **Permission Control** (can_revoke_admins flag)
- **Revoke Admin Privileges**
- **Admin Activity Logging** (comprehensive audit trail)
- **User Management:**
  - Create user accounts
  - Change user passwords
  - Send password reset links
  - Restrict/unrestrict accounts

### Booking System
- **CRUD Operations** (Create, Read, Update, Delete bookings)
- **Service Dropdown** with predefined options
- **Admin Booking Creation** for users
- **Status Management** (pending, confirmed, cancelled)
- **Server-side Validation**

### Audit & Logging
- **AdminActivityLog** - Tracks all admin actions
- **AccountHistory** - Complete lifecycle tracking for user accounts
- **IP Address Logging** for security events

---

## 🛠 Technology Stack

- **Framework:** Django 5.0.2
- **API:** Django REST Framework 3.15.0
- **Authentication:** Simple JWT (djangorestframework-simplejwt 5.3.0)
- **Database:** SQLite (development) / PostgreSQL (production)
- **Email:** SendGrid
- **Cloud Storage:** Cloudinary
- **CORS:** django-cors-headers 4.5.0
- **Environment:** python-dotenv 1.0.0

---

## 🏗 Architecture

### Three-Layer Architecture

```
┌─────────────────────────────────────┐
│         React Frontend              │
│    (User Interface Layer)           │
└─────────────────┬───────────────────┘
                  │ HTTP/REST API
                  ▼
┌─────────────────────────────────────┐
│      Django REST Framework          │
│    (Business Logic & API Layer)     │
│                                     │
│  ┌──────────────┐  ┌─────────────┐ │
│  │authentication│  │   booking   │ │
│  │     app      │  │     app     │ │
│  └──────────────┘  └─────────────┘ │
└─────────────────┬───────────────────┘
                  │ ORM
                  ▼
┌─────────────────────────────────────┐
│         PostgreSQL Database         │
│      (Data Persistence Layer)       │
└─────────────────────────────────────┘
```

### Django Apps Structure

```
backend/
├── authentication/          # User management & auth
│   ├── models.py           # User, UserProfile, Tokens, Logs
│   ├── views.py            # Auth endpoints
│   ├── serializers.py      # Data validation
│   ├── urls.py             # Route definitions
│   └── utils.py            # Helper functions
├── booking/                # Booking management
│   ├── models.py           # Booking model
│   ├── views.py            # Booking endpoints
│   ├── serializers.py      # Booking validation
│   └── urls.py             # Booking routes
└── backend/                # Project settings
    ├── settings.py         # Configuration
    ├── urls.py             # Main URL router
    └── send_email.py       # Email utilities
```

---

## 📦 Installation

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- PostgreSQL (for production)
- Virtual environment tool (venv or virtualenv)

### Setup Steps

1. **Clone the repository**
```bash
git clone https://github.com/KehindeOluwasogo-BC/ESE-APP.git
cd ESE-APP/ese-backend/backend
```

2. **Create virtual environment**
```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install django djangorestframework django-cors-headers djangorestframework-simplejwt sendgrid python-http-client python-dotenv
```

4. **Set up environment variables** (see next section)

5. **Run migrations**
```bash
python manage.py makemigrations
python manage.py migrate
```

6. **Create superuser**
```bash
python manage.py createsuperuser
```

7. **Run development server**
```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000`

---

## ⚙️ Environment Configuration

Create a `.env` file in the `backend/` directory:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (PostgreSQL for production)
DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# Frontend URL (for CORS)
FRONTEND_URL=http://localhost:5173

# SendGrid Configuration
SENDGRID_API_KEY=your-sendgrid-api-key
SENDGRID_FROM_EMAIL=noreply@yourdomain.com

# Cloudinary Configuration
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret

# JWT Settings (optional, has defaults)
ACCESS_TOKEN_LIFETIME_MINUTES=60
REFRESH_TOKEN_LIFETIME_DAYS=7
```

### Environment Variables Reference

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `SECRET_KEY` | Django secret key | Yes | - |
| `DEBUG` | Debug mode (False in production) | No | True |
| `ALLOWED_HOSTS` | Comma-separated allowed hosts | No | localhost |
| `DATABASE_URL` | PostgreSQL connection string | Production | SQLite |
| `FRONTEND_URL` | Frontend URL for CORS | Yes | - |
| `SENDGRID_API_KEY` | SendGrid API key | Yes | - |
| `SENDGRID_FROM_EMAIL` | Sender email address | Yes | - |
| `CLOUDINARY_CLOUD_NAME` | Cloudinary cloud name | Yes | - |
| `CLOUDINARY_API_KEY` | Cloudinary API key | Yes | - |
| `CLOUDINARY_API_SECRET` | Cloudinary API secret | Yes | - |

---

## 🚀 Running the Application

### Development Mode

```bash
python manage.py runserver
```

Access the API at: `http://localhost:8000`

### Production Mode

```bash
# Collect static files
python manage.py collectstatic --noinput

# Run with gunicorn
gunicorn backend.wsgi:application --bind 0.0.0.0:8000
```

---

## 📚 API Documentation

### Base URL
- Development: `http://localhost:8000/api`
- Production: `https://your-domain.com/api`

### Authentication Endpoints

#### POST `/api/auth/register/`
Register a new user account.

**Request Body:**
```json
{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "SecurePass123!",
  "first_name": "John",
  "last_name": "Doe",
  "memorable_information": "{\"question\":\"Name of pet\",\"answer\":\"Fluffy\"}"
}
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

#### POST `/api/auth/token/`
Obtain JWT tokens (login).

**Request Body:**
```json
{
  "username": "johndoe",
  "password": "SecurePass123!"
}
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

#### POST `/api/auth/token/refresh/`
Refresh access token.

**Request Body:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

#### GET `/api/auth/user/`
Get current user information (requires authentication).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "id": 1,
  "username": "johndoe",
  "email": "john@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "full_name": "John Doe",
  "is_superuser": false,
  "is_active": true,
  "profile_picture": "https://res.cloudinary.com/...",
  "can_revoke_admins": true,
  "memorable_information": "{\"question\":\"Name of pet\",\"answer\":\"Fluffy\"}"
}
```

### Password Reset Endpoints

#### POST `/api/auth/password-reset/request/`
Request password reset email.

**Request Body:**
```json
{
  "email": "john@example.com"
}
```

#### POST `/api/auth/password-reset/validate/`
Validate reset token.

**Request Body:**
```json
{
  "token": "abc123def456"
}
```

#### POST `/api/auth/password-reset/confirm/`
Reset password with token.

**Request Body:**
```json
{
  "token": "abc123def456",
  "new_password": "NewSecurePass123!"
}
```

### Admin Management Endpoints (Superuser Required)

#### POST `/api/auth/admin/create/`
Create a new admin user.

**Request Body:**
```json
{
  "username": "adminuser",
  "email": "admin@example.com",
  "password": "AdminPass123!",
  "first_name": "Admin",
  "last_name": "User",
  "can_revoke_admins": true,
  "memorable_information": "{\"question\":\"Country of origin\",\"answer\":\"Nigeria\"}"
}
```

#### GET `/api/auth/admin/list/`
List all admin users.

#### POST `/api/auth/admin/revoke/`
Revoke admin privileges from a user.

**Request Body:**
```json
{
  "user_id": 5
}
```

#### GET `/api/auth/admin/activity-logs/`
Get admin activity logs.

**Query Parameters:**
- `limit` (optional): Number of logs to return (default: 50)

### User Management Endpoints (Superuser Required)

#### GET `/api/auth/users/list/`
List all regular users.

#### POST `/api/auth/users/create/`
Create a regular user account.

**Request Body:**
```json
{
  "username": "newuser",
  "email": "newuser@example.com",
  "password": "UserPass123!",
  "first_name": "New",
  "last_name": "User",
  "memorable_information": "{\"question\":\"Mother's maiden name\",\"answer\":\"Smith\"}"
}
```

#### POST `/api/auth/users/change-password/`
Change a user's password (admin only).

**Request Body:**
```json
{
  "user_id": 10,
  "new_password": "NewSecurePass123!"
}
```

#### POST `/api/auth/users/send-reset-link/`
Send password reset link to a user.

**Request Body:**
```json
{
  "user_id": 10
}
```

#### POST `/api/auth/users/toggle-active/`
Restrict or unrestrict a user account.

**Request Body:**
```json
{
  "user_id": 10
}
```

**Response:**
```json
{
  "message": "User username has been restricted successfully.",
  "is_active": false
}
```

### Booking Endpoints

#### GET `/api/bookings/`
List all bookings for the authenticated user.

#### POST `/api/bookings/`
Create a new booking.

**Request Body:**
```json
{
  "full_name": "John Doe",
  "email": "john@example.com",
  "service": "Haircut",
  "booking_date": "2026-03-01",
  "booking_time": "14:30",
  "notes": "Please use organic products",
  "status": "pending"
}
```

**Admin creating booking for user:**
```json
{
  "full_name": "Jane Smith",
  "email": "jane@example.com",
  "service": "Massage",
  "booking_date": "2026-03-05",
  "booking_time": "10:00",
  "notes": "Deep tissue massage",
  "status": "pending",
  "user_id": 15
}
```

#### GET `/api/bookings/<id>/`
Get booking details.

#### PUT `/api/bookings/<id>/`
Update a booking.

#### DELETE `/api/bookings/<id>/`
Delete a booking.

### Profile Management

#### PUT `/api/auth/profile/picture/`
Update profile picture.

**Request Body:**
```json
{
  "profile_picture": "https://res.cloudinary.com/your-cloud/image/upload/..."
}
```

---

## 🗄 Database Models

### User (Django Built-in)
Extended with Django's AbstractUser.

### UserProfile
```python
- user (OneToOne → User)
- bio (TextField)
- profile_picture (URLField)
- memorable_information (TextField)  # JSON string
- can_revoke_admins (BooleanField)   # Admin permission
- created_at (DateTimeField)
- updated_at (DateTimeField)
```

### PasswordResetToken
```python
- user (ForeignKey → User)
- token (CharField)
- created_at (DateTimeField)
- expires_at (DateTimeField)
- is_used (BooleanField)
```

### PasswordResetAttempt
```python
- email (EmailField)
- ip_address (GenericIPAddressField)
- created_at (DateTimeField)
```

### AdminActivityLog
```python
- admin_user (ForeignKey → User)
- action (CharField)  # CREATED_ADMIN, REVOKED_ADMIN, OTHER
- target_user (ForeignKey → User)
- description (TextField)
- ip_address (GenericIPAddressField)
- created_at (DateTimeField)
```

### AccountHistory
```python
- user (ForeignKey → User)
- event_type (CharField)  # CREATED, ADMIN_GRANTED, ADMIN_REVOKED, etc.
- performed_by (ForeignKey → User)
- description (TextField)
- ip_address (GenericIPAddressField)
- created_at (DateTimeField)
```

### Booking
```python
- user (ForeignKey → User)
- full_name (CharField)
- email (EmailField)
- service (CharField)
- booking_date (DateField)
- booking_time (TimeField)
- status (CharField)  # pending, confirmed, cancelled
- notes (TextField)
- created_at (DateTimeField)
- updated_at (DateTimeField)
```

---

## 🧪 Testing

### Running Tests

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test authentication
python manage.py test booking

# With pytest (if installed)
pytest
pytest authentication/tests/
```

### Test Structure

```
authentication/
└── tests/
    ├── test_models.py
    ├── test_views.py
    ├── test_serializers.py
    └── test_permissions.py

booking/
└── tests/
    ├── test_models.py
    ├── test_views.py
    └── test_api.py
```

---

## 🌐 Deployment

### Deploying to Render

1. **Create PostgreSQL Database**
   - Log into Render
   - Create new PostgreSQL database
   - Copy the Internal Database URL

2. **Create Web Service**
   - Connect GitHub repository
   - Select `ese-backend` directory
   - Build Command: `pip install -r requirements.txt && python manage.py migrate`
   - Start Command: `gunicorn backend.wsgi:application`

3. **Set Environment Variables**
   - Add all variables from `.env` file
   - Set `DEBUG=False`
   - Set `DATABASE_URL` to Render PostgreSQL URL

4. **Deploy**
   - Trigger manual deploy or push to main branch

### Production Checklist

- [ ] Set `DEBUG=False`
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Set secure `SECRET_KEY`
- [ ] Configure PostgreSQL database
- [ ] Set up SendGrid for production
- [ ] Configure Cloudinary for production
- [ ] Enable HTTPS
- [ ] Set secure cookie flags
- [ ] Configure CORS properly
- [ ] Set up logging
- [ ] Create superuser on production

---

## 🔒 Security Features

### Authentication & Authorization
- **JWT-based Authentication** with access and refresh tokens
- **Role-based Access Control** (regular users vs super admins)
- **Granular Permissions** (can_revoke_admins flag)
- **Account Restriction** capability

### Password Security
- **Django Password Validation** (built-in validators)
- **Secure Password Hashing** (PBKDF2 algorithm)
- **Password Reset Flow** with time-limited tokens
- **Security Questions** for account recovery

### API Security
- **CORS Configuration** with specific origin whitelisting
- **CSRF Protection** for state-changing operations
- **Rate Limiting** on password reset (3 attempts per 15 minutes)
- **Input Validation** on all endpoints
- **SQL Injection Protection** via Django ORM

### Audit Logging
- **Admin Activity Tracking** (all admin actions logged)
- **Account History** (complete lifecycle tracking)
- **IP Address Logging** for security events
- **Timestamp Tracking** for all events

### Data Protection
- **Email Privacy** (validation before sending)
- **Secure Token Generation** (cryptographically secure)
- **Environment Variable Protection** (secrets not in code)

---

## 🔌 External Services

### SendGrid (Email Service)
- **Password reset emails**
- **Account notifications**
- **Admin notifications**

**Setup:**
1. Create SendGrid account
2. Verify sender email
3. Generate API key
4. Add to environment variables

### Cloudinary (Media Storage)
- **Profile picture uploads**
- **Image optimization**
- **CDN delivery**

**Setup:**
1. Create Cloudinary account
2. Get cloud name, API key, and secret
3. Add to environment variables
4. Frontend handles upload, backend stores URL

---

## 🤖 AI Usage Acknowledgment

This project was developed with assistance from AI tools, specifically:

- **GitHub Copilot** - Code completion and suggestions
- **ChatGPT/Claude** - Architecture planning, debugging assistance, and documentation

All code has been reviewed, understood, and tested by the developer. AI tools were used to:
- Generate boilerplate code structures
- Suggest best practices for Django REST Framework
- Assist with debugging complex issues
- Help write comprehensive documentation

The developer takes full responsibility for all submitted code and can explain the implementation of all features.

---

## 📝 License

This project is part of an academic assignment for Enterprise Software Engineering at Ada National College for Digital Skills.

---

## 👤 Author

**Kehinde Oluwasogo**
- GitHub: [@KehindeOluwasogo-BC](https://github.com/KehindeOluwasogo-BC)

---

## 🙏 Acknowledgments

- Django and Django REST Framework documentation
- SendGrid for email service
- Cloudinary for media management
- Ada National College for Digital Skills
- Module instructors and teaching assistants

---

**Last Updated:** February 23, 2026
