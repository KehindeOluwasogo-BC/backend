# Database Schema Documentation

Complete database schema for ESE Booking System.

## Overview

The system uses Django ORM with support for SQLite (development) and PostgreSQL (production). All models inherit from Django's `models.Model` class.

---

## User & Authentication Models

### User (Django Built-in)

Django's standard User model with additional profile support.

```
Table: auth_user

Columns:
- id (PRIMARY KEY)
- username (VARCHAR, UNIQUE)
- email (VARCHAR)
- password (VARCHAR - hashed with PBKDF2)
- first_name (VARCHAR)
- last_name (VARCHAR)
- is_active (BOOLEAN, default: True)
- is_staff (BOOLEAN, default: False)
- is_superuser (BOOLEAN, default: False)
  └─ Set to True for admin users
- last_login (DATETIME, nullable)
- date_joined (DATETIME, auto_now_add)

Indexes:
- username (UNIQUE)
- email
- is_superuser (for admin filtering)

Related:
- UserProfile (1:1)
- PasswordResetToken (1:N)
- AdminActivityLog (1:N as admin)
- AccountHistory (1:N as user)
- Booking (1:N)
```

---

### UserProfile

Extended user information.

```
Table: authentication_userprofile

Columns:
- id (PRIMARY KEY)
- user_id (FOREIGN KEY → auth_user.id, UNIQUE)
- profile_picture (URLField, max_length=500, nullable)
- bio (TextField, nullable)
- memorable_information (TextField, for password recovery)
- can_revoke_admins (BOOLEAN, default: True)
- created_at (DATETIME, auto_now_add)
- updated_at (DATETIME, auto_now)

Indexes:
- user_id (UNIQUE, FOREIGN KEY)
- created_at (for sorting/filtering)

Constraints:
- CASCADE delete with User (if user deleted, profile deleted)

Example Data:
┌────┬─────────┬──────────────────┬─────────────────┬──────────────────┬──────────────┐
│ id │ user_id │ profile_picture  │ bio             │ memorable_info   │ can_revoke   │
├────┼─────────┼──────────────────┼─────────────────┼──────────────────┼──────────────┤
│ 1  │ 2       │ https://...jpg   │ Software Dev    │ First pet: Buddy │ true         │
│ 2  │ 5       │ NULL             │ NULL            │ Favorite color   │ false        │
└────┴─────────┴──────────────────┴─────────────────┴──────────────────┴──────────────┘
```

---

### PasswordResetToken

Tracks password reset tokens for security purposes.

```
Table: authentication_passwordresettoken

Columns:
- id (PRIMARY KEY)
- user_id (FOREIGN KEY → auth_user.id)
- token (VARCHAR, UNIQUE)
  └─ 43-character URL-safe random token
  └─ Example: ABCDef1234567890abcdef1234567890aBcDefGh
- created_at (DATETIME, auto_now_add)
- expires_at (DATETIME)
  └─ Calculated as created_at + 1 hour
- is_used (BOOLEAN, default: False)

Indexes:
- token (UNIQUE, for fast lookup)
- user_id (FOREIGN KEY)
- expires_at (for cleanup queries)

Constraints:
- CASCADE delete with User
- Single use: is_used becomes True after password reset

TTL/Expiration:
- Tokens expire 1 hour after creation
- On reset confirmation: is_used = True
- Expired or used tokens cannot be reused

Example Data:
┌────┬─────────┬──────────────────┬──────────────────┬──────────────────┬──────────┐
│ id │ user_id │ token            │ created_at       │ expires_at       │ is_used  │
├────┼─────────┼──────────────────┼──────────────────┼──────────────────┼──────────┤
│ 1  │ 5       │ ABC123...        │ 2026-03-23:12:00 │ 2026-03-23:13:00 │ false    │
│ 2  │ 7       │ XYZ789...        │ 2026-03-22:10:00 │ 2026-03-22:11:00 │ true     │
└────┴─────────┴──────────────────┴──────────────────┴──────────────────┴──────────┘
```

---

### PasswordResetAttempt

Rate limiting for password reset requests.

```
Table: authentication_passwordresetattempt

Columns:
- id (PRIMARY KEY)
- email (VARCHAR)
- timestamp (DATETIME, auto_now_add)

Indexes:
- email (for fast filtering)
- timestamp (for time-window queries)

Purpose:
- Track reset requests per email
- Enforce 3 attempts per 10-minute window
- Prevent brute force password reset attacks

Cleanup:
- Attempts older than 10 minutes auto-deleted

Example Data:
┌────┬──────────────────────┬──────────────────┐
│ id │ email                │ timestamp        │
├────┼──────────────────────┼──────────────────┤
│ 1  │ john@example.com     │ 2026-03-23:12:00 │
│ 2  │ john@example.com     │ 2026-03-23:12:05 │
│ 3  │ john@example.com     │ 2026-03-23:12:10 │
│ 4  │ jane@example.com     │ 2026-03-23:12:15 │
└────┴──────────────────────┴──────────────────┘
```

---

## Admin & Audit Models

### AdminActivityLog

Audit trail for all admin actions.

```
Table: authentication_adminactivitylog

Columns:
- id (PRIMARY KEY)
- admin_id (FOREIGN KEY → auth_user.id)
  └─ User who performed the action
- action (VARCHAR, max_length=50)
  └─ Choices: CREATE_ADMIN, REVOKE_ADMIN, CREATE_USER, 
             CHANGE_PASSWORD, SEND_RESET_LINK, TOGGLE_ACTIVE
- target_user_id (FOREIGN KEY → auth_user.id, nullable)
  └─ User affected by action (null if no target)
- description (TextField)
  └─ Human-readable explanation
- ip_address (GenericIPAddressField)
  └─ IPv4 or IPv6 address of admin
- timestamp (DATETIME, auto_now_add)

Indexes:
- admin_id (for "find actions by admin")
- target_user_id (for "find actions affecting user")
- action (for filtering by action type)
- timestamp (for date-range queries)

Constraints:
- CASCADE delete with User (admin or target_user)

Example Data:
┌────┬──────────┬──────────────┬─────────────┬──────────────────┬──────────────┐
│ id │ admin_id │ action       │ target_user │ description      │ ip_address   │
├────┼──────────┼──────────────┼─────────────┼──────────────────┼──────────────┤
│ 1  │ 1        │ CREATE_ADMIN │ 3           │ Created new...   │ 192.168.1.1  │
│ 2  │ 1        │ REVOKE_ADMIN │ 3           │ Revoked admin... │ 192.168.1.1  │
│ 3  │ 1        │ CREATE_USER  │ 5           │ Created user...  │ 192.168.1.1  │
└────┴──────────┴──────────────┴─────────────┴──────────────────┴──────────────┘
```

---

### AccountHistory

Account lifecycle event tracking.

```
Table: authentication_accounthistory

Columns:
- id (PRIMARY KEY)
- user_id (FOREIGN KEY → auth_user.id)
  └─ Account affected
- event_type (VARCHAR, max_length=50)
  └─ Choices: CREATED, REVOKED, RESTRICTED, UNRESTRICTED, 
             PASSWORD_RESET_INITIATED, PASSWORD_RESET_COMPLETED
- performed_by_id (FOREIGN KEY → auth_user.id, nullable)
  └─ Admin who performed action (null if self-action)
- description (TextField)
  └─ Details about the event
- ip_address (GenericIPAddressField)
  └─ Client IP address
- timestamp (DATETIME, auto_now_add)

Indexes:
- user_id (for "history of user")
- event_type (for filtering events)
- timestamp (for date-range queries)

Constraints:
- CASCADE delete with User

Example Data:
┌────┬────────┬────────────┬──────────────┬────────────────┬──────────────┐
│ id │ user_id│ event_type │ performed_by │ description    │ timestamp    │
├────┼────────┼────────────┼──────────────┼────────────────┼──────────────┤
│ 1  │ 5      │ CREATED    │ NULL         │ Self-registered│ 2026-03-20   │
│ 2  │ 5      │ PASSWORD.. │ 5            │ Reset password │ 2026-03-23   │
│ 3  │ 5      │ REVOKED    │ 1            │ Admin revoked..│ 2026-03-23   │
└────┴────────┴────────────┴──────────────┴────────────────┴──────────────┘
```

---

## Booking Model

### Booking

Main business domain model for booking management.

```
Table: booking_booking

Columns:
- id (PRIMARY KEY)
- user_id (FOREIGN KEY → auth_user.id)
  └─ User who made the booking
  └─ Regular users can only see/modify their own
  └─ Admins can see/modify all
- full_name (VARCHAR, max_length=120)
  └─ Customer full name
- email (EmailField)
  └─ Customer email address
  └─ Used for booking confirmation notifications
- booking_date (DATE)
  └─ Date of the booking (YYYY-MM-DD)
  └─ Cannot be in the past
  └─ SQL type: DATE
- booking_time (TIME)
  └─ Start time of the booking (HH:MM:SS)
  └─ Must be within business hours (9:00 AM - 7:30 PM)
  └─ SQL type: TIME
- service (VARCHAR, max_length=120)
  └─ Type of service from catalog
  └─ Valid services: Haircut, Hair Coloring, Massage, Facial, Manicure, Pedicure, Spa Package, Consultation
  └─ Each service has defined duration and buffers
- status (VARCHAR, max_length=20)
  └─ Choices: pending, confirmed, completed, cancelled
  └─ Regular users: resets to "pending" on update
  └─ Admins: can set any status
  └─ Default: "pending"
- notes (TextField, nullable)
  └─ Additional details or comments about the booking
- created_at (DATETIME, auto_now_add)
  └─ When booking was created
- updated_at (DATETIME, auto_now)
  └─ Last modification timestamp

Indexes:
- (booking_date, booking_time) - Composite index for availability checks
- status - Finding pending/confirmed bookings
- user_id - Filtering by user

Constraints:
- CASCADE delete with User
- status field limited to predefined choices
- Service must be valid (from SERVICE_CATALOG)
- booking_date cannot be in the past
- Booking end time (including service duration and buffer) must be within business hours

Availability Validation:
- Uses service duration + buffer times to determine time slot occupancy
- Prevents overlapping bookings considering buffers
- Respects business hours: 9:00 AM - 7:30 PM (19:30)
- Service-specific buffers prevent back-to-back incompatible services

Example Data:
┌────┬────────┬───────────┬────────┬──────────┬──────────┬──────────┬──────────────┐
│ id │ user_id│ full_name │ email  │ service  │status    │ bdate    │ btime        │
├────┼────────┼───────────┼────────┼──────────┼──────────┼──────────┼──────────────┤
│ 1  │ 5      │ John Doe  │ j@ex.co│ Haircut  │ pending  │2026-04-15│ 10:00:00     │
│ 2  │ 5      │ John Doe  │ j@ex.co│ Coloring │ confirmed│2026-04-16│ 14:00:00     │
│ 3  │ 7      │ Jane Smith│ j@ex.co│ Massage  │ completed│2026-04-20│ 09:30:00     │
└────┴────────┴───────────┴────────┴──────────┴──────────┴──────────┴──────────────┘
```

### Service Catalog

The booking system includes a predefined catalog of services, each with specific durations and buffer times for scheduling:

```
Service Catalog (from booking/services.py):

1. Haircut
   - Duration: 60 minutes
   - Buffer before: 15 minutes
   - Buffer after: 15 minutes
   - Total time needed: 90 minutes

2. Hair Coloring
   - Duration: 120 minutes
   - Buffer before: 15 minutes
   - Buffer after: 30 minutes
   - Total time needed: 165 minutes

3. Massage
   - Duration: 90 minutes
   - Buffer before: 10 minutes
   - Buffer after: 20 minutes
   - Total time needed: 120 minutes

4. Facial
   - Duration: 75 minutes
   - Buffer before: 15 minutes
   - Buffer after: 15 minutes
   - Total time needed: 105 minutes

5. Manicure
   - Duration: 45 minutes
   - Buffer before: 10 minutes
   - Buffer after: 10 minutes
   - Total time needed: 65 minutes

6. Pedicure
   - Duration: 60 minutes
   - Buffer before: 10 minutes
   - Buffer after: 15 minutes
   - Total time needed: 85 minutes

7. Spa Package
   - Duration: 180 minutes
   - Buffer before: 20 minutes
   - Buffer after: 30 minutes
   - Total time needed: 230 minutes

8. Consultation
   - Duration: 30 minutes
   - Buffer before: 5 minutes
   - Buffer after: 10 minutes
   - Total time needed: 45 minutes
```

---

## Relationships Diagram

```
┌─────────────────┐
│   auth_user     │ (Django built-in)
│                 │
│ id (PK)         │
│ username ◄─ UNIQUE
│ email           │
│ is_superuser    │
│ is_active       │
└────┬────────────┘
     │
     ├─→ UserProfile (1:1)
     │   └─ profile_picture, bio, memorable_info
     │
     ├─→ PasswordResetToken (1:N)
     │   └─ token, expires_at, is_used
     │
     ├─→ PasswordResetAttempt (1:N)
     │   └─ Used for rate limiting
     │
     ├─→ AdminActivityLog (1:N as admin)
     │   ├─ action, description, ip_address
     │   └─ target_user_id (can point back to User)
     │
     ├─→ AccountHistory (1:N)
     │   ├─ event_type, description
     │   └─ performed_by_id (can point back to User)
     │
     └─→ Booking (1:N)
         ├─ booking_date, booking_time
         ├─ service_type, status, notes
         └─ User can have multiple bookings
```

---

## Database Queries Structure

### Commonly Used Queries

```sql
-- Get all bookings for a user
SELECT * FROM booking_booking 
WHERE user_id = 5 
ORDER BY booking_date DESC;

-- Get pending bookings for admin view
SELECT * FROM booking_booking 
WHERE status = 'pending' 
ORDER BY booking_date ASC;

-- Get valid password reset tokens
SELECT * FROM authentication_passwordresettoken 
WHERE is_used = false 
AND expires_at > NOW();

-- Get admin activity in last 7 days
SELECT * FROM authentication_adminactivitylog 
WHERE timestamp > NOW() - INTERVAL '7 days'
ORDER BY timestamp DESC;

-- Check rate limiting for password reset
SELECT COUNT(*) FROM authentication_passwordresetattempt 
WHERE email = 'user@example.com' 
AND timestamp > NOW() - INTERVAL '10 minutes';

-- Get account history for user
SELECT * FROM authentication_accounthistory 
WHERE user_id = 5 
ORDER BY timestamp DESC;
```

---

## Migration History

### Current Schema Version

Django uses migration files to track schema changes.

```
Migrations:
0001_initial.py
  └─ User, UserProfile, PasswordResetToken, PasswordResetAttempt models

0002_passwordresetattempt_userprofile.py
  └─ Additional UserProfile fields

0003_adminactivitylog.py
  └─ AdminActivityLog model

0004_userprofile_can_revoke_admins.py
  └─ Added can_revoke_admins field to UserProfile

0005_accounthistory.py
  └─ AccountHistory model

0006_userprofile_memorable_information.py
  └─ Added memorable_information field
```

To view migration history:
```bash
python manage.py showmigrations
```

---

## Performance Considerations

### Query Optimization Tips

1. **Use `.select_related()` for ForeignKey:**
   ```python
   # Avoid N+1 queries
   bookings = Booking.objects.select_related('user').all()
   ```

2. **Use `.prefetch_related()` for reverse relations:**
   ```python
   # Avoid N+1 queries
   users = User.objects.prefetch_related('userprofile').all()
   ```

3. **Filter early:**
   ```python
   # Good: Filter in query
   bookings = Booking.objects.filter(status='pending')
   
   # Bad: Filter in Python
   bookings = Booking.objects.all()
   bookings = [b for b in bookings if b.status == 'pending']
   ```

4. **Use indexes for filtering:**
   - Fields used in WHERE clauses should have indexes
   - Current indexes: user_id, status, booking_date, created_at

### Database Statistics

Monitor with:
```bash
# PostgreSQL table sizes
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) 
FROM pg_tables 
WHERE schemaname = 'public';

# Row counts
SELECT COUNT(*) FROM booking_booking;
SELECT COUNT(*) FROM auth_user;
```

---

## Backup & Recovery

### Backup Strategy

**PostgreSQL (Production):**
- Render provides automated daily backups
- 7-day retention policy
- Manual on-demand backups available

**SQLite (Development):**
- File-based: `db.sqlite3`
- Include in Git (not recommended for large DBs)
- Or use `.gitignore` and backup separately

### Recovery Procedures

```bash
# List available backups
render postgres:backups list

# Restore from backup
render postgres:restore database-id backup-id

# Export data (PostgreSQL)
pg_dump dbname > backup.sql

# Restore from export
psql dbname < backup.sql
```

---

## Data Types Reference

| Django Type | SQLite | PostgreSQL | Example |
|------------|--------|-----------|---------|
| CharField | TEXT | VARCHAR | "John" |
| TextField | TEXT | TEXT | Long text |
| DateField | DATE | DATE | 2026-03-23 |
| TimeField | TIME | TIME | 14:30:00 |
| DateTimeField | DATETIME | TIMESTAMP | 2026-03-23 14:30:00 |
| IntegerField | INTEGER | INTEGER | 42 |
| BooleanField | BOOLEAN | BOOLEAN | true/false |
| URLField | TEXT | VARCHAR | https://... |
| EmailField | TEXT | VARCHAR | user@example.com |
| GenericIPAddressField | TEXT | INET | 192.168.1.1 |
| ForeignKey | INTEGER | INTEGER (FK) | 5 (user_id) |

