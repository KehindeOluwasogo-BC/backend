# Security Documentation

Comprehensive security practices and configurations for ESE Booking System.

## Table of Contents

1. [Authentication & Authorization](#authentication--authorization)
2. [Password Security](#password-security)
3. [Token Management](#token-management)
4. [Rate Limiting](#rate-limiting)
5. [Data Protection](#data-protection)
6. [Network Security](#network-security)
7. [Security Audit Trail](#security-audit-trail)
8. [Best Practices for Deployment](#best-practices-for-deployment)
9. [Incident Response](#incident-response)
10. [Security Checklist](#security-checklist)

---

## Authentication & Authorization

### JWT Authentication

**Implementation:** Django REST Framework Simple JWT

**Flow:**
1. User provides credentials (username + password)
2. Backend validates against Django User model
3. If valid, backend issues JWT tokens:
   - **Access Token**: Short-lived (5 minutes default), used for API requests
   - **Refresh Token**: Long-lived (24 hours default), used to obtain new access tokens
4. Client stores tokens securely
5. Client includes Access Token in `Authorization: Bearer <token>` header
6. Backend validates token signature before processing request

**Token Structure:**
```
Header: { "typ": "JWT", "alg": "HS256" }
Payload: { "user_id": 5, "username": "john_doe", "exp": 1679576000 }
Signature: base64(HMAC-SHA256(header.payload, SECRET_KEY))
```

**Security Features:**
- ✅ Signed with SECRET_KEY (HMAC-SHA256)
- ✅ Expiration enforced (`exp` claim)
- ✅ Access tokens are short-lived (low exposure)
- ✅ Refresh tokens have separate expiration
- ✅ Token signature prevents tampering
- ✅ No sensitive data in token (except user_id username)

---

### Role-Based Access Control (RBAC)

**Two-Tier System:**

```
Regular User (is_superuser = False)
├─ Can register, login, reset password
├─ Can view/update own profile
├─ Can manage own bookings (create/read/update/delete)
└─ Cannot:
   ├─ Access admin endpoints
   ├─ View other users' bookings
   ├─ Change other users' passwords

Superuser/Admin (is_superuser = True)
├─ Can do everything a regular user can
├─ Can create other admin accounts
├─ Can revoke admin privileges
├─ Can manage all user accounts
├─ Can view all bookings (and set status)
├─ Can view activity logs
└─ Can view account history
```

**Implementation:**
- View-level: `permission_classes = (IsAuthenticated,)` or checks `request.user.is_superuser`
- Serializer-level: Conditional field updates (e.g., booking status reset for non-admin)
- Queryset-level: Filter by user (e.g., `filter(user=request.user)`)

**Example Protection:**
```python
class BookingViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Regular users: see only own bookings
        # Admins: see all bookings
        if self.request.user.is_superuser:
            return Booking.objects.all()
        return Booking.objects.filter(user=self.request.user)
    
    def perform_update(self, serializer):
        # Serializer resets status to pending for non-admin
        serializer.save()
```

---

## Password Security

### Password Hashing

**Algorithm:** PBKDF2 (Password-Based Key Derivation Function 2)

**Configuration:**
```
- Algorithm: PBKDF2-SHA256
- Iterations: 260,000+ (Django configures based on version)
- Salt: Generated uniquely per user (auto)
- Hash Length: 256 bits
```

**Verification:**
- Passwords are **never stored in plaintext**
- On login, Django hashes submitted password and compares to stored hash
- If hashes match, user is authenticated
- Hashes are irreversible (one-way function)

**Example Hash:**
```
pbkdf2_sha256$260000$abc123xyz$hashed_password_very_long_string
```

---

### Password Strength Validation

**Enforced on Registration & Reset:**

Django's built-in password validators:

1. **Minimum Length**: Minimum 8 characters (default)
2. **Complexity**: Must include numbers, uppercase, lowercase, special chars
3. **Dictionary Check**: Common passwords rejected (e.g., "password123")
4. **User Attribute Check**: Password can't be too similar to username/email
5. **Common Patterns**: Prevents sequential numbers/letters

**Validation Code:**
```python
from django.contrib.auth.password_validation import validate_password

try:
    validate_password(user_provided_password)
except ValidationError as e:
    # Return error to user
```

**Example Validation Errors:**
```
❌ "123456" → Too short/simple
❌ "password" → Too common
❌ "john_doe_password" → Too similar to username
✅ "SecurePass2026!" → Meets all criteria
```

---

### Password Reset Security

**Design Goals:**
- Single-use tokens (can't reuse after reset)
- Time-limited (expires after 1 hour)
- Secure delivery (via email)
- No token in URL (frontend stores separately)

**Flow:**
```
1. User requests password reset
2. System generates secure token: secrets.token_urlsafe(32)
   └─ 43-character URL-safe random string
   └─ Example: "ABCDef1234567890abcdef1234567890aBcDefGh"
3. Token stored in DB with expiration: NOW() + 1 hour
4. Email sent with reset link: FRONTEND_URL + token
5. User clicks link, frontend extracts token
6. User submits new password + token to backend
7. Backend validates:
   └─ Token exists in DB
   └─ Token not expired
   └─ Token not already used (is_used = False)
   └─ Password meets strength requirements
8. Backend updates password, marks token as used
9. Token cannot be reused or after expiration, token is invalid
```

**Security Features:**
- ✅ Tokens are cryptographically secure (secrets.token_urlsafe)
- ✅ Single-use enforcement (is_used flag)
- ✅ Time-limited (1-hour expiration)
- ✅ Email delivery is secure (HTTPS)
- ✅ No token in URL (no browser history exposure)
- ✅ Rate limiting (3 attempts per 10 minutes)

**Vulnerabilities Prevented:**
- ❌ Token reuse: Prevented by is_used flag
- ❌ Expired tokens: Checked via expires_at
- ❌ Token replay: Tokens are single-use
- ❌ Brute force: Rate limiting enforced
- ❌ Enumeration: No feedback on whether email exists (potential future improvement)

---

## Token Management

### Token Expiration

**Access Token:**
- Expires: 5 minutes (default Simple JWT setting)
- Use case: API requests
- Benefit: Low exposure if token leaked
- Downside: Frequent refresh needed

**Refresh Token:**
- Expires: 24 hours (or 7 days for "remember me")
- Use case: Obtaining new access tokens
- Benefit: Users don't need to re-login daily
- Downside: Longer exposure; should be stored securely

**Example Token Lifetimes:**
```
13:00:00 - User logs in
         - Access token issued (expires at 13:05:00)
         - Refresh token issued (expires at 2026-03-24 13:00:00)

13:04:00 - User makes API request
         - Access token still valid (1 min remaining)
         - Request processed

13:05:30 - User makes API request
         - Access token expired
         - Frontend detects 401 response
         - Frontend uses refresh token to get new access token
         - New access token issued (expires at 13:10:30)
         - Original request retried

2026-03-24 13:01:00 - Refresh token expired
         - Frontend can no longer refresh
         - User must re-login
```

---

### Token Storage (Frontend Responsibility)

**Secure Storage Options:**

1. **Memory (Most Secure, Lost on Refresh)**
   ```javascript
   // Store in memory variable
   let accessToken = response.data.access;
   ```
   - ✅ Pros: Not vulnerable to XSS attacks (can't access from console)
   - ❌ Cons: Lost when page refreshes

2. **LocalStorage (Standard, XSS Vulnerable)**
   ```javascript
   localStorage.setItem('access_token', response.data.access);
   ```
   - ⚠️️ Pros: Persists across refreshes
   - ❌ Cons: Vulnerable to XSS attacks (can be accessed via `document.cookie`)

3. **HttpOnly Cookies (Most Secure, Server-Set)**
   ```javascript
   // Backend sets automatically
   Set-Cookie: access_token=...; HttpOnly; Secure; SameSite=Strict
   ```
   - ✅ Pros: Cannot be accessed via JavaScript (blocked by browser)
   - ✅ Cons: More complex to implement CORS
   - ✅ Protects against XSS

**Recommendation for This Project:**
- Use HttpOnly cookies with `Secure` and `SameSite` flags
- Or use memory + secure refresh token endpoint

---

## Rate Limiting

### Password Reset Rate Limiting

**Configuration:**
- **Limit**: 3 password reset attempts per email
- **Window**: 10 minutes
- **Response**: HTTP 429 Too Many Requests

**Implementation:**
```python
# PasswordResetAttempt model tracks attempts
attempts = PasswordResetAttempt.objects.filter(
    email=requested_email,
    timestamp__gt=timezone.now() - timedelta(minutes=10)
).count()

if attempts >= 3:
    return Response({"error": "Too many attempts"}, status=429)
```

**User Experience:**
```json
{
  "error": "Too many reset attempts. Please try again later.",
  "rate_limited": true,
  "seconds_remaining": 480,
  "retry_message": "Please wait 8 minutes and 0 seconds before trying again."
}
```

**Attack Prevention:**
- ❌ Brute force password resets: Prevented (3/10min limit)
- ❌ Email enumeration: Partially (returns rate limit, not "user not found")
- ❌ DoS via email spam: Mitigated (sender is limited to 3/10min)

---

## Data Protection

### Input Validation

**Serializer-Level Validation:**
```python
# Email format validation
email = serializers.EmailField()

# Password strength validation
new_password = serializers.CharField(
    write_only=True,
    validators=[validate_password]
)

# Email existence check
def validate_email(self, value):
    if not User.objects.filter(email=value).exists():
        raise serializers.ValidationError("User not found")
    return value
```

**Benefits:**
- ✅ Prevents invalid data in database
- ✅ Returns clear error messages to user
- ✅ Prevents SQL injection (Django ORM parameterizes queries)
- ✅ Prevents NoSQL injection (not applicable, using relational DB)

---

### SQL Injection Prevention

**Django ORM Protection:**
- All queries parameterized (safe by default)
- Never concatenate user input into query strings

**Safe Example:**
```python
# SAFE: Uses ORM parameterization
booking = Booking.objects.filter(id=request.data['booking_id'])

# UNSAFE: String concatenation (DON'T DO THIS)
booking = Booking.objects.raw(f"SELECT * FROM booking WHERE id={request.data['booking_id']}")
```

---

### Sensitive Data Handling

**PII (Personally Identifiable Information):**
- ✅ Passwords: Hashed with PBKDF2
- ✅ Tokens: Signed and time-limited
- ✅ Email: Encrypted in transit (HTTPS), hashed in password reset attempts
- ✅ IP Address: Logged for audit trail only

**Data Minimization:**
- Only collect necessary fields
- No credit card data stored
- No health information stored
- No biometric data stored

**Data Retention:**
- User profiles: Kept until user deletion
- Password reset tokens: Deleted after 1 hour expiration
- PasswordResetAttempt: Deleted after 10 minutes (auto cleanup)
- AdminActivityLog: Kept indefinitely (audit trail)
- AccountHistory: Kept indefinitely (compliance)

---

## Network Security

### CORS Configuration

**Current Settings:**
```python
CORS_ALLOWED_ORIGINS = os.getenv('CORS_ALLOWED_ORIGINS')
# Example: https://frontend.onrender.com
```

**What CORS Protects:**
- ✅ Prevents unauthorized domains from accessing API
- ⚠️ Does NOT protect against backend requests (server-to-server attacks)

**Configuration Best Practices:**
```python
# ❌ NEVER use wildcard in production
CORS_ALLOWED_ORIGINS = ["*"]

# ✅ Specify exact domains
CORS_ALLOWED_ORIGINS = [
    "https://app.example.com",
    "https://admin.example.com"
]

# ✅ For development only
if DEBUG:
    CORS_ALLOWED_ORIGINS += ["http://localhost:3000"]
```

**For This Project:**
```env
# .env file
CORS_ALLOWED_ORIGINS=https://your-frontend.onrender.com
```

### CSRF Protection

**Configuration:**
```python
MIDDLEWARE = [
    ...
    'django.middleware.csrf.CsrfViewMiddleware',
    ...
]

CSRF_TRUSTED_ORIGINS = os.getenv('CSRF_TRUSTED_ORIGINS')
# Example: https://frontend.onrender.com
```

**CSRF Token Flow:**
1. Frontend requests CSRF token from backend
2. Backend returns token
3. Frontend includes token in POST/PUT/DELETE requests
4. Backend verifies token matches session
5. If tokens match, request is allowed

**For this REST API:**
- CSRF less relevant (using JWT tokens, not session cookies)
- Still configured for compatibility
- Frontend can send CSRF token in `X-CSRFToken` header if needed

### HTTPS/TLS

**Configuration:**
```python
# Production settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
```

**Benefits:**
- ✅ Encrypts communication between client and server
- ✅ Prevents man-in-the-middle attacks
- ✅ Authenticates server identity (via certificate)
- ✅ Ensures data integrity

**Implementation:**
- Render provides free SSL certificates
- Automatic HTTPS on all Render domains
- Redirect from HTTP to HTTPS

---

## Security Audit Trail

### AdminActivityLog

Tracks all administrative actions:

```python
admin_action = AdminActivityLog.objects.create(
    admin=request.user,
    action='CREATE_ADMIN',      # Action type
    target_user=new_admin,      # Affected user
    description='Created new admin account',
    ip_address=get_client_ip(request)  # Source IP
)
```

**Audit Fields:**
- `admin`: Which user performed action
- `action`: What action (CREATE_ADMIN, REVOKE_ADMIN, etc.)
- `target_user`: Which user was affected
- `description`: Human-readable details
- `ip_address`: Source IP address (for tracing)
- `timestamp`: When action occurred

**Querying Audit Logs:**
```bash
# View all admin actions
GET /api/auth/admin/activity-logs/

# Find actions by specific admin
SELECT * FROM authentication_adminactivitylog WHERE admin_id = 1;

# Find all actions affecting a user
SELECT * FROM authentication_adminactivitylog WHERE target_user_id = 5;

# Find actions in last 24 hours
SELECT * FROM authentication_adminactivitylog WHERE timestamp > NOW() - INTERVAL '24 hours';
```

---

### AccountHistory

Tracks account lifecycle events:

```python
AccountHistory.objects.create(
    user=user,
    event_type='PASSWORD_RESET_COMPLETED',
    performed_by=None,  # Self-action
    description='User successfully reset password',
    ip_address=get_client_ip(request)
)
```

**Event Types:**
- `CREATED`: Account created (registration)
- `REVOKED`: Admin privileges revoked
- `RESTRICTED`: Account deactivated
- `UNRESTRICTED`: Account reactivated
- `PASSWORD_RESET_INITIATED`: Password reset requested
- `PASSWORD_RESET_COMPLETED`: Password successfully reset

---

## Best Practices for Deployment

### Environment Variable Management

**Never Hardcode Secrets:**
```python
# ❌ WRONG
SECRET_KEY = "django-insecure-abc123xyz"
SENDGRID_API_KEY = "SG.xxxxx"

# ✅ CORRECT
SECRET_KEY = os.getenv('SECRET_KEY')
SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
```

**Environment Variables Checklist:**
- [ ] `SECRET_KEY` - Django secret (long random string)
- [ ] `DEBUG` - False in production
- [ ] `ALLOWED_HOSTS` - Production domain(s)
- [ ] `DATABASE_URL` - PostgreSQL connection
- [ ] `SENDGRID_API_KEY` - Email service key
- [ ] `SENDGRID_FROM_EMAIL` - Sender email
- [ ] `FRONTEND_URL` - Frontend domain (for reset links)
- [ ] `CORS_ALLOWED_ORIGINS` - Frontend URL
- [ ] `CSRF_TRUSTED_ORIGINS` - Frontend URL

### Secret Rotation

**When to Rotate:**
- Quarterly as best practice
- Immediately if compromised
- When team member leaves
- After security incident

**Rotation Process:**
1. Generate new secret
2. Update in environment variables
3. Redeploy application
4. Invalidate old tokens (optional, depends on requirements)
5. Verify application works

---

## Incident Response

### Compromised Access Token

**Response:**
1. Token is short-lived (5 min) - automatic expiration
2. No action needed if within 5 minutes
3. If token leaked and still valid:
   - Rotate SECRET_KEY (forces re-login)
   - Monitor user account for suspicious activity

**Prevention:**
- Store tokens securely (HttpOnly cookies)
- Use HTTPS only
- Avoid logging tokens
- Monitor for unusual activity

### Compromised Refresh Token

**Response:**
1. Delete refresh token from database (force re-login)
2. Rotate SECRET_KEY
3. Notify user of compromise
4. Reset user password
5. Review account activity history
6. Check if other accounts compromised

**Detection:**
- Multiple refresh requests from unusual IPs
- Refresh requests at odd times
- Multiple concurrent sessions

### Compromised Database

**Response:**
1. **Immediate:**
   - Rotate all secrets (SECRET_KEY, API keys)
   - Invalidate all tokens (force re-login)
   - Reset all user passwords
   
2. **Investigation:**
   - Determine what data was accessed
   - Check audit logs for breaches
   - Identify affected users
   
3. **Notification:**
   - Inform users of breach
   - Advise password reset
   - Check for unauthorized account modifications
   
4. **Prevention:**
   - Enable database backups
   - Implement encryption at rest
   - Restrict database access (firewall, VPN)
   - Add database monitoring/alerts

### Suspected DDoS Attack

**Response:**
1. Monitor request volume in Render dashboard
2. If legitimate traffic spike:
   - Upgrade Render plan temporarily
   - Add rate limiting
3. If malicious:
   - Enable WAF (Web Application Firewall)
   - Block problematic IPs
   - Contact Render support

---

## Security Checklist

### Development
- [ ] Never commit secrets to Git
- [ ] Use `.gitignore` for .env files
- [ ] Test password reset flow
- [ ] Test rate limiting (try 4+ password resets)
- [ ] Verify CORS configuration
- [ ] Test token expiration
- [ ] Verify audit logs are created
- [ ] No hardcoded API keys

### Before Production Deployment
- [ ] `DEBUG=False`
- [ ] `SECRET_KEY` is long and random
- [ ] `ALLOWED_HOSTS` configured
- [ ] `CORS_ALLOWED_ORIGINS` restricted (not wildcard)
- [ ] `CSRF_TRUSTED_ORIGINS` configured
- [ ] Unique `SENDGRID_API_KEY`
- [ ] HTTPS enabled
- [ ] Database backups enabled
- [ ] Admin user created
- [ ] Test all endpoints with valid token
- [ ] Verify error messages don't leak sensitive info

### Post-Deployment
- [ ] Monitor logs for errors
- [ ] Check audit logs for suspicious activity
- [ ] Verify password reset emails arrive
- [ ] Test rate limiting
- [ ] Confirm all users can login
- [ ] Verify admin endpoints are protected
- [ ] Set up monitoring/alerting

### Regular Maintenance (Monthly)
- [ ] Review audit logs for suspicious activity
- [ ] Check database size and query performance
- [ ] Update dependencies for security patches
- [ ] Rotate secrets if policy requires
- [ ] Test disaster recovery procedures

---

## Security Resources

**References:**
- OWASP Top 10: https://owasp.org/www-project-top-ten/
- Django Security: https://docs.djangoproject.com/en/stable/topics/security/
- JWT Best Practices: https://tools.ietf.org/html/rfc8725
- NIST Password Guidelines: https://pages.nist.gov/800-63-3/sp800-63b.html

**Tools:**
- Password strength checker: https://www.passwordmonster.com
- SSL test: https://www.ssllabs.com/ssltest/
- Security headers: https://securityheaders.com

