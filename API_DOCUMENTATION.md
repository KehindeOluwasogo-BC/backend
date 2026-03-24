# API Documentation

Complete reference for all ESE Booking System API endpoints.

## Base URL

- **Development**: `http://localhost:8000/api`
- **Production**: `https://ese-booking-backend.onrender.com/api`

---

## Authentication Endpoints

### Register User
**POST** `/auth/register/`

Create a new user account.

**Request Body:**
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "SecurePass123!",
  "first_name": "John",
  "last_name": "Doe",
  "memorable_information": "My pet's name"
}
```

**Response (201 Created):**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Error (400 Bad Request):**
```json
{
  "username": ["A user with that username already exists."],
  "email": ["This field may not be blank."]
}
```

---

### Login (Obtain Token)
**POST** `/auth/token/`

Authenticate and receive JWT tokens. Username lookup is **case-insensitive** for better UX.

**Request Body:**
```json
{
  "username": "john_doe",
  "password": "SecurePass123!"
}
```

**Response (200 OK):**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Error (401 Unauthorized):**
```json
{
  "detail": "No active account found with the given credentials"
}
```

**Note:** Username is case-insensitive - both "john_doe" and "JOHN_DOE" will work.

---

### Refresh Access Token
**POST** `/auth/token/refresh/`

Get a new access token using refresh token.

**Request Body:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response (200 OK):**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

---

### Get User Info
**GET** `/auth/user/`

Retrieve authenticated user's profile information.

**Headers:**
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

**Response (200 OK):**
```json
{
  "id": 5,
  "username": "john_doe",
  "email": "john@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "full_name": "John Doe",
  "is_superuser": false,
  "is_active": true,
  "profile_picture": "https://example.com/pic.jpg",
  "can_revoke_admins": false,
  "memorable_information": "My pet's name"
}
```

**Error (401 Unauthorized):**
```json
{
  "detail": "Authentication credentials were not provided."
}
```

---

### Update Profile Picture
**POST** `/auth/profile/picture/`

Update user's profile picture URL.

**Headers:**
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

**Request Body:**
```json
{
  "profile_picture": "https://example.com/new-pic.jpg"
}
```

**Response (200 OK):**
```json
{
  "message": "Profile picture updated successfully"
}
```

---

## Password Reset Endpoints

### Request Password Reset
**POST** `/auth/password-reset/request/`

Send a password reset email to the user. Email lookup is **case-insensitive**.

**Request Body:**
```json
{
  "email": "john@example.com"
}
```

**Response (200 OK):**
```json
{
  "message": "Password reset email sent successfully. Please check your inbox."
}
```

**Error (400 Bad Request):**
```json
{
  "email": ["No user found with this email address."]
}
```

**Note:** Email lookup is case-insensitive - both "john@example.com" and "JOHN@EXAMPLE.COM" will work.

**Error (429 Too Many Requests):**
```json
{
  "error": "Too many reset attempts. Please try again later.",
  "rate_limited": true,
  "seconds_remaining": 480,
  "retry_message": "Please wait 8 minutes and 0 seconds before trying again."
}
```

---

### Validate Reset Token
**POST** `/auth/password-reset/validate/`

Check if a password reset token is valid.

**Request Body:**
```json
{
  "token": "ABCDef1234567890abcdef1234567890"
}
```

**Response (200 OK):**
```json
{
  "valid": true,
  "message": "Token is valid."
}
```

**Error (400 Bad Request):**
```json
{
  "valid": false,
  "error": "Token has expired or already been used."
}
```

---

### Confirm Password Reset
**POST** `/auth/password-reset/confirm/`

Reset password using token and new password.

**Request Body:**
```json
{
  "token": "ABCDef1234567890abcdef1234567890",
  "new_password": "NewSecurePass456!"
}
```

**Response (200 OK):**
```json
{
  "message": "Password has been reset successfully. You can now login with your new password."
}
```

**Error (400 Bad Request):**
```json
{
  "new_password": ["This password is too common."]
}
```

---

## Admin Management Endpoints

### Create Admin User
**POST** `/auth/admin/create/`

Create a new administrator account. **Superuser only.**

**Headers:**
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

**Request Body:**
```json
{
  "username": "admin_user",
  "email": "admin@example.com",
  "password": "AdminPass123!",
  "first_name": "Admin",
  "last_name": "User",
  "can_revoke_admins": true,
  "memorable_information": "Security question answer"
}
```

**Response (201 Created):**
```json
{
  "id": 3,
  "username": "admin_user",
  "email": "admin@example.com",
  "is_superuser": true,
  "is_active": true
}
```

**Error (403 Forbidden):**
```json
{
  "detail": "You do not have permission to perform this action."
}
```

---

### List Admin Users
**GET** `/auth/admin/list/`

Retrieve all administrator accounts. **Superuser only.**

**Headers:**
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "username": "superuser",
    "email": "super@example.com",
    "is_superuser": true,
    "is_active": true
  },
  {
    "id": 3,
    "username": "admin_user",
    "email": "admin@example.com",
    "is_superuser": true,
    "is_active": true
  }
]
```

---

### Revoke Admin Privileges
**POST** `/auth/admin/revoke/`

Remove administrator privileges from a user. **Superuser only.**

**Headers:**
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

**Request Body:**
```json
{
  "admin_id": 3
}
```

**Response (200 OK):**
```json
{
  "message": "Admin privileges revoked successfully"
}
```

**Error (400 Bad Request):**
```json
{
  "error": "Cannot revoke admin privileges from yourself"
}
```

---

### View Admin Activity Logs
**GET** `/auth/admin/activity-logs/`

Retrieve audit logs of all admin actions. **Superuser only.**

**Headers:**
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "admin": "superuser",
    "action": "CREATE_ADMIN",
    "target_user": "admin_user",
    "description": "Created new admin user",
    "ip_address": "192.168.1.1",
    "timestamp": "2026-03-23T12:30:00Z"
  },
  {
    "id": 2,
    "admin": "superuser",
    "action": "REVOKE_ADMIN",
    "target_user": "admin_user",
    "description": "Revoked admin privileges",
    "ip_address": "192.168.1.1",
    "timestamp": "2026-03-23T12:35:00Z"
  }
]
```

---

## User Management Endpoints

### List All Users
**GET** `/auth/users/list/`

Retrieve all user accounts. **Superuser only.**

**Headers:**
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

**Response (200 OK):**
```json
[
  {
    "id": 5,
    "username": "john_doe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "is_active": true,
    "full_name": "John Doe"
  }
]
```

---

### Create User Account
**POST** `/auth/users/create/`

Create a new regular user account. **Superuser only.**

**Headers:**
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

**Request Body:**
```json
{
  "username": "jane_smith",
  "email": "jane@example.com",
  "password": "SecurePass123!",
  "first_name": "Jane",
  "last_name": "Smith"
}
```

**Response (201 Created):**
```json
{
  "id": 6,
  "username": "jane_smith",
  "email": "jane@example.com",
  "first_name": "Jane",
  "last_name": "Smith",
  "is_active": true
}
```

---

### Change User Password
**POST** `/auth/users/change-password/`

Reset a user's password. **Superuser only.**

**Headers:**
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

**Request Body:**
```json
{
  "user_id": 5,
  "new_password": "NewPass456!"
}
```

**Response (200 OK):**
```json
{
  "message": "Password changed successfully"
}
```

---

### Send Password Reset Link
**POST** `/auth/users/send-reset-link/`

Send a password reset email to a user. **Superuser only.**

**Headers:**
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

**Request Body:**
```json
{
  "email": "john@example.com"
}
```

**Response (200 OK):**
```json
{
  "message": "Password reset link sent successfully"
}
```

---

### Toggle User Active Status
**POST** `/auth/users/toggle-active/`

Activate or deactivate a user account. **Superuser only.**

**Headers:**
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

**Request Body:**
```json
{
  "user_id": 5,
  "is_active": false
}
```

**Response (200 OK):**
```json
{
  "message": "User account toggled successfully"
}
```

---

## Booking Endpoints

### Get Available Services
**GET** `/bookings/services/`

Retrieve list of all available services with their details.

**Headers:**
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

**Response (200 OK):**
```json
{
  "services": [
    {
      "name": "Haircut",
      "duration": 60,
      "description": "Basic haircut service",
      "buffer_before": 15,
      "buffer_after": 15,
      "total_time": 90
    },
    {
      "name": "Hair Coloring",
      "duration": 120,
      "description": "Full hair coloring service",
      "buffer_before": 15,
      "buffer_after": 30,
      "total_time": 165
    },
    {
      "name": "Massage",
      "duration": 90,
      "description": "Relaxation massage therapy",
      "buffer_before": 10,
      "buffer_after": 20,
      "total_time": 120
    },
    {
      "name": "Facial",
      "duration": 75,
      "description": "Facial treatment",
      "buffer_before": 15,
      "buffer_after": 15,
      "total_time": 105
    },
    {
      "name": "Manicure",
      "duration": 45,
      "description": "Manicure service",
      "buffer_before": 10,
      "buffer_after": 10,
      "total_time": 65
    },
    {
      "name": "Pedicure",
      "duration": 60,
      "description": "Pedicure service",
      "buffer_before": 10,
      "buffer_after": 15,
      "total_time": 85
    },
    {
      "name": "Spa Package",
      "duration": 180,
      "description": "Full spa experience",
      "buffer_before": 20,
      "buffer_after": 30,
      "total_time": 230
    },
    {
      "name": "Consultation",
      "duration": 30,
      "description": "Initial consultation",
      "buffer_before": 5,
      "buffer_after": 10,
      "total_time": 45
    }
  ]
}
```

---

### Get Available Time Slots
**GET** `/bookings/available_slots/?date=2026-04-15&service=Haircut`

Get all available time slots for a specific date and service.

**Headers:**
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

**Query Parameters:**
- `date` (required): Date in YYYY-MM-DD format
- `service` (optional): Service name (if not provided, shows general availability with 60-min slots)

**Response (200 OK):**
```json
{
  "date": "2026-04-15",
  "business_hours": {
    "start": "09:00",
    "end": "19:30"
  },
  "service": "Haircut",
  "service_duration": 60,
  "slots": [
    {
      "time": "09:00",
      "display_time": "09:00 AM",
      "available": true
    },
    {
      "time": "09:30",
      "display_time": "09:30 AM",
      "available": true
    },
    {
      "time": "10:00",
      "display_time": "10:00 AM",
      "available": false
    }
  ],
  "summary": {
    "total_slots": 21,
    "available_slots": 18,
    "booked_slots": 3
  }
}
```

**Errors:**
```json
{
  "error": "Date parameter is required"
}
```

```json
{
  "error": "Invalid date format. Use YYYY-MM-DD"
}
```

```json
{
  "error": "Cannot check availability for past dates"
}
```

---

### Check Specific Slot Availability
**POST** `/bookings/check_availability/`

Check if a specific time slot is available for a service.

**Headers:**
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

**Request Body:**
```json
{
  "date": "2026-04-15",
  "time": "10:00",
  "service": "Haircut"
}
```

**Response (200 OK - Available):**
```json
{
  "available": true,
  "service": "Haircut",
  "start_time": "2026-04-15T10:00:00",
  "end_time": "2026-04-15T11:00:00",
  "duration_minutes": 60
}
```

**Response (200 OK - Not Available):**
```json
{
  "available": false,
  "service": "Haircut",
  "start_time": "2026-04-15T10:00:00",
  "error": "This time slot is not available for Haircut. Please choose a different time."
}
```

**Errors:**
```json
{
  "error": "date, time, and service are required"
}
```

---

### List Bookings
**GET** `/bookings/`

Retrieve bookings. Regular users see only their bookings; admins see all.

**Headers:**
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

**Query Parameters:**
- `ordering`: Sort by field (e.g., `-created_at`, `booking_date`)
- `limit`: Number of results per page
- `offset`: Pagination offset

**Response (200 OK):**
```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "user": 5,
      "username": "john_doe",
      "full_name": "John Doe",
      "email": "john@example.com",
      "booking_date": "2026-04-15",
      "booking_time": "10:00",
      "service": "Haircut",
      "service_duration": 60,
      "estimated_end_time": "11:00",
      "status": "pending",
      "notes": "Regular cut with fade",
      "created_at": "2026-03-23T12:00:00Z",
      "updated_at": "2026-03-23T12:00:00Z"
    }
  ]
}
```

---

### Create Booking
**POST** `/bookings/`

Create a new booking.

**Headers:**
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

**Request Body (Regular User):**
```json
{
  "full_name": "John Doe",
  "email": "john@example.com",
  "booking_date": "2026-04-15",
  "booking_time": "10:00",
  "service": "Haircut",
  "notes": "Regular cut with fade"
}
```

**Request Body (Admin - can book for another user):**
```json
{
  "user_id": 5,
  "full_name": "John Doe",
  "email": "john@example.com",
  "booking_date": "2026-04-15",
  "booking_time": "10:00",
  "service": "Haircut",
  "status": "confirmed",
  "notes": "Regular cut with fade"
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "user": 5,
  "username": "john_doe",
  "full_name": "John Doe",
  "email": "john@example.com",
  "booking_date": "2026-04-15",
  "booking_time": "10:00",
  "service": "Haircut",
  "service_duration": 60,
  "estimated_end_time": "11:00",
  "status": "pending",
  "notes": "Regular cut with fade",
  "created_at": "2026-03-23T12:00:00Z",
  "updated_at": "2026-03-23T12:00:00Z"
}
```

**Errors:**
```json
{
  "service": ["'InvalidService' is not a valid service. Valid services are: Haircut, Hair Coloring, Massage, ..."]
}
```

```json
{
  "booking_date": ["Cannot create bookings for past dates."]
}
```

```json
{
  "booking_time": ["Booking starts before business hours. Earliest time for Haircut is 9:15 AM."]
}
```

```json
{
  "booking_time": ["This time slot is not available for Haircut. Please choose a different time."]
}
```

---

### Retrieve Booking
**GET** `/bookings/{id}/`

Get a specific booking by ID.

**Headers:**
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

**Response (200 OK):**
```json
{
  "id": 1,
  "user": 5,
  "username": "john_doe",
  "full_name": "John Doe",
  "email": "john@example.com",
  "booking_date": "2026-04-15",
  "booking_time": "10:00",
  "service": "Haircut",
  "service_duration": 60,
  "estimated_end_time": "11:00",
  "status": "pending",
  "notes": "Regular cut with fade",
  "created_at": "2026-03-23T12:00:00Z",
  "updated_at": "2026-03-23T12:00:00Z"
}
```

---

### Update Booking (Full)
**PUT** `/bookings/{id}/`

Replace all fields of a booking.

**Headers:**
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

**Request Body (Regular User):**
```json
{
  "full_name": "John Doe",
  "email": "john@example.com",
  "booking_date": "2026-04-16",
  "booking_time": "14:00",
  "service": "Hair Coloring",
  "notes": "Full color treatment"
}
```

**Request Body (Admin - update status):**
```json
{
  "full_name": "John Doe",
  "email": "john@example.com",
  "booking_date": "2026-04-15",
  "booking_time": "10:00",
  "service": "Haircut",
  "status": "confirmed",
  "notes": "Regular cut with fade"
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "user": 5,
  "username": "john_doe",
  "full_name": "John Doe",
  "email": "john@example.com",
  "booking_date": "2026-04-16",
  "booking_time": "14:00",
  "service": "Hair Coloring",
  "service_duration": 120,
  "estimated_end_time": "16:00",
  "status": "pending",
  "notes": "Full color treatment",
  "created_at": "2026-03-23T12:00:00Z",
  "updated_at": "2026-03-23T13:00:00Z"
}
```

**Note:** Regular users' status is automatically reset to `pending`. Admins can set any status.

---

### Update Booking (Partial)
**PATCH** `/bookings/{id}/`

Update specific fields of a booking.

**Headers:**
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

**Request Body (Admin - update status only):**
```json
{
  "status": "confirmed"
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "user": 5,
  "username": "john_doe",
  "full_name": "John Doe",
  "email": "john@example.com",
  "booking_date": "2026-04-15",
  "booking_time": "10:00",
  "service": "Haircut",
  "service_duration": 60,
  "estimated_end_time": "11:00",
  "status": "confirmed",
  "notes": "Regular cut with fade",
  "created_at": "2026-03-23T12:00:00Z",
  "updated_at": "2026-03-23T13:05:00Z"
}
```

**Note:** Status-only updates skip availability validation.

---

### Delete Booking
**DELETE** `/bookings/{id}/`

Cancel/delete a booking.

**Headers:**
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

**Response (204 No Content):**
```
(empty response)
```

---

## Response Codes Summary

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 204 | No Content (successful deletion) |
| 400 | Bad Request (invalid data) |
| 401 | Unauthorized (missing/invalid token) |
| 403 | Forbidden (insufficient permissions) |
| 404 | Not Found |
| 429 | Too Many Requests (rate limited) |
| 500 | Internal Server Error |

---

## Authentication Header Format

All authenticated endpoints require the following header:

```
Authorization: Bearer <access_token>
```

Example:
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjo1LCJ1c2VybmFtZSI6ImpvaG5fZG9lIiwiZXhwIjoxNjc5NTc2MDAwfQ.abc123
```

---

## Rate Limiting

Password reset endpoint has rate limiting configured:

- **3 requests** allowed per email address
- **10-minute** rolling window
- Returns **HTTP 429** with retry information when exceeded

Example rate limit response:
```json
{
  "error": "Too many reset attempts. Please try again later.",
  "rate_limited": true,
  "seconds_remaining": 480,
  "retry_message": "Please wait 8 minutes and 0 seconds before trying again."
}
```
