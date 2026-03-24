# Deployment Guide

Complete guide for deploying ESE Booking System Backend to production and managing deployments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Database Setup](#database-setup)
4. [Deploying to Render](#deploying-to-render)
5. [Post-Deployment Verification](#post-deployment-verification)
6. [Monitoring & Maintenance](#monitoring--maintenance)
7. [Troubleshooting](#troubleshooting)
8. [Rollback Procedures](#rollback-procedures)

---

## Prerequisites

Before deploying, ensure you have:

1. **GitHub Account**: Repository must be hosted on GitHub
2. **Render Account**: Sign up at https://render.com
3. **SendGrid Account**: For email delivery (optional but recommended)
4. **PostgreSQL Knowledge**: Understanding of database connections
5. **Git**: Installed and configured
6. **Python 3.10+**: Local development environment

---

## Environment Setup

### Step 1: Repository Configuration

Ensure your repository is clean and ready for deployment:

```bash
# Check git status
git status

# Ensure all changes are committed
git add .
git commit -m "Prepare for deployment"

# Push to main branch
git push origin main
```

### Step 2: Create Render Web Service

1. Go to https://dashboard.render.com
2. Click **"New+"** → **"Web Service"**
3. Connect your GitHub repository
4. Configure settings:
   - **Name**: `ese-booking-backend` (or your preferred name)
   - **Environment**: `Python 3`
   - **Build Command**: (see below)
   - **Start Command**: (see below)
   - **Plan**: Choose appropriate tier (free tier available)

#### Build Command
```bash
pip install -r requirements.txt && python manage.py migrate && python manage.py collectstatic
```
#### Build Command (to include an Admin account)
```bash
pip install -r requirements.txt; python manage.py migrate; python manage.py collectstatic; python manage.py shell -c "from django.contrib.auth import get_user_model; import os; U=get_user_model(); u=os.getenv('DJANGO_SUPERUSER_USERNAME'); e=os.getenv('DJANGO_SUPERUSER_EMAIL'); p=os.getenv('DJANGO_SUPERUSER_PASSWORD'); (u and e and p) and (U.objects.filter(username=u).exists() or U.objects.create_superuser(u,e,p))
```

**To use this build command, you must set these environment variables** (see [Step 3](#step-3-configure-environment-variables) below):
- `DJANGO_SUPERUSER_USERNAME` - Username for the admin account
- `DJANGO_SUPERUSER_EMAIL` - Email for the admin account
- `DJANGO_SUPERUSER_PASSWORD` - Password for the admin account

#### Start Command
```bash
gunicorn backend.wsgi:application
```

---

## Environment Variables

### Step 3: Configure Environment Variables

In Render dashboard, go to **Environment** tab and add these variables:

#### Required Variables

```env
# Django Settings
SECRET_KEY=your-very-secure-random-key-here
DEBUG=False
ENVIRONMENT=production

# Database (provided by Render PostgreSQL service)
DATABASE_URL=postgresql://user:password@host:5432/dbname

# Security
ALLOWED_HOSTS=ese-booking-backend.onrender.com,your-domain.com
CSRF_TRUSTED_ORIGINS=https://your-frontend.onrender.com
CORS_ALLOWED_ORIGINS=https://your-frontend.onrender.com

# Email (SendGrid)
SENDGRID_API_KEY=SG.xxxxxxxxxxxxx
SENDGRID_FROM_EMAIL=noreply@yourdomain.com
FROM_EMAIL=noreply@yourdomain.com

# Frontend URL (for password reset links)
FRONTEND_URL=https://your-frontend.onrender.com
```

#### Generate SECRET_KEY

```bash
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

Copy the output and paste it in `SECRET_KEY` environment variable.

---

## Database Setup

### Step 4: Create PostgreSQL Database

In Render dashboard:

1. Click **"New+"** → **"PostgreSQL"**
2. Configure:
   - **Name**: `ese-booking-db` (or preferred name)
   - **Database**: `ese_booking`
   - **User**: (auto-generated)
   - **Region**: Same as web service (optimal)
3. Create the database
4. Copy **Internal Database URL** from credentials

### Step 5: Link Database to Web Service

1. Go to your Web Service settings
2. Click **"Environment"**
3. Add `DATABASE_URL` variable with the PostgreSQL internal URL

### Step 6: Run Migrations

After the first deployment:

1. Go to Web Service → **"Shell"** tab
2. Run migrations manually:
   ```bash
   python manage.py migrate
   ```

Or migrations run automatically during build via build command.

---

## Deploying to Render

### Initial Deployment (First Time)

**Step 1: Trigger Build**
- Render automatically detects GitHub pushes
- Your first deployment starts automatically after pushing to `main`
- Check build logs in **Render Dashboard** → **Logs** tab

**Step 2: Monitor Deployment**
```
Stages:
1. Building image (~2 minutes)
2. Installing dependencies (~3 minutes)
3. Running migrations (~1 minute)
4. Collecting static files (~30 seconds)
5. Starting Gunicorn (~30 seconds)
```

**Step 3: Verify Deployment**

Once build completes and app is running:

```bash
# Test API root endpoint
curl https://ese-booking-backend.onrender.com/api/

# Expected response:
# { "message": "Authentication API root", ... }
```

### Subsequent Deployments

**Option A: Automatic (Recommended)**
- Push to `main` branch
- Render automatically rebuilds and deploys

```bash
git push origin main
```

**Option B: Manual Redeploy**
- Go to Render Dashboard
- Click **"Deploy"** → **"Deploy latest commit"**

---

## Post-Deployment Verification

### Step 7: Test Critical Endpoints

```bash
BASE_URL="https://ese-booking-backend.onrender.com/api"

# 1. Test API root
curl $BASE_URL/

# 2. Test registration
curl -X POST $BASE_URL/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "TestPass123!",
    "first_name": "Test",
    "last_name": "User"
  }'

# 3. Test login
curl -X POST $BASE_URL/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "TestPass123!"
  }'
```

### Step 8: Create Admin User

Connect to production database and create superuser:

**Via Render Shell:**
1. Go to Web Service → **Shell** tab
2. Run:
   ```bash
   python manage.py createsuperuser
   ```
3. Follow prompts to create admin user

**Or via SSH (if enabled):**
```bash
ssh user@hostname
python manage.py createsuperuser
```

### Step 9: Verify Admin Access

Test admin endpoints:

```bash
BASE_URL="https://ese-booking-backend.onrender.com/api"
ADMIN_TOKEN="your-admin-access-token"

# Get admin activity logs
curl -X GET $BASE_URL/auth/admin/activity-logs/ \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

---

## Monitoring & Maintenance

### Regular Health Checks

Setup monitoring using Render's built-in tools:

1. **Health Check Endpoint** (automatic)
   - Render pings `/health/` every 30 seconds
   - If unhealthy, service restarts automatically

2. **View Logs**
   - Render Dashboard → **Logs** tab
   - Real-time logs as requests come in
   - Search for errors: filter by log level

3. **Monitor Resource Usage**
   - Render Dashboard → **Metrics** tab
   - CPU usage
   - Memory usage
   - Request count
   - Response times

### Performance Optimization

**If response times increase:**

1. Check number of concurrent connections
2. Increase Gunicorn workers:
   ```bash
   # Modify start command to:
   gunicorn backend.wsgi:application --workers 4 --worker-class sync --timeout 120
   ```

3. Enable caching layer (Redis)
4. Optimize database queries

**If database is slow:**

1. Add database indexes
2. Upgrade PostgreSQL plan
3. Review slow query logs

### Backup Strategy

**PostgreSQL Backups:**
- Render provides automatic daily backups (7-day retention)
- Manual backups via Render Dashboard
- Backups stored in multiple regions

**Application Code Backups:**
- GitHub automatically backs up all code
- All commits are version-controlled

### Regular Maintenance Tasks

**Weekly:**
- Review error logs for exceptions
- Check admin activity logs for suspicious actions
- Monitor database size

**Monthly:**
- Run `django-admin cleanupsessions` to remove old sessions
- Review rate limiting stats
- Update dependencies in requirements.txt

```bash
# Update dependencies locally and test
pip install --upgrade pip
pip install -r requirements.txt --upgrade
pytest  # Run tests to verify
git push origin main  # Will trigger new deployment
```

---

## Troubleshooting

### Issue: Build Fails with Missing Dependencies

**Error:**
```
ERROR: Could not find a version that satisfies the requirement ...
```

**Solution:**
1. Update requirements.txt
2. Test locally: `pip install -r requirements.txt`
3. Push changes: `git push origin main`
4. Render will retry build

### Issue: "SECRET_KEY is missing" Error

**Error:**
```
ImproperlyConfigured: SECRET_KEY setting is missing
```

**Solution:**
1. Go to Render Dashboard
2. Check Environment tab
3. Ensure `SECRET_KEY` variable is set
4. Redeploy: Click **Deploy** → **Deploy latest commit**

### Issue: Database Connection Error

**Error:**
```
OperationalError: could not connect to server: Connection refused
```

**Solution:**
1. Verify DATABASE_URL is set correctly in Environment
2. Ensure PostgreSQL service is running (check Render Dashboard)
3. Verify internal URL format (not external URL)
4. Check if database service is in same region as web service

### Issue: Static Files Not Serving (404 on CSS/JS)

**Error:**
```
404 Not Found for /static/admin/css/base.css
```

**Solution:**
1. Ensure build command includes `collectstatic`:
   ```bash
   pip install -r requirements.txt && python manage.py migrate && python manage.py collectstatic --noinput
   ```
2. Verify WhiteNoise is in MIDDLEWARE (settings.py)
3. Redeploy: `git push origin main`

### Issue: CORS Errors from Frontend

**Error:**
```
Access to XMLHttpRequest blocked by CORS policy
```

**Solution:**
1. Set `CORS_ALLOWED_ORIGINS` to frontend URL:
   ```env
   CORS_ALLOWED_ORIGINS=https://your-frontend.onrender.com
   ```
2. Ensure no wildcard (`*`) in production
3. Redeploy

### Issue: Password Reset Emails Not Sent

**Error:**
```
Failed to send email: ...
```

**Solution:**
1. Check `SENDGRID_API_KEY` is set and valid
2. Verify `SENDGRID_FROM_EMAIL` is authorized in SendGrid
3. Check SendGrid dashboard for bounce/spam reports
4. Test locally with your actual email:
   ```bash
   python manage.py shell
   >>> from backend.send_email import send_password_reset_email
   >>> send_password_reset_email('your@email.com', 'test-token-123')
   ```

### Issue: Slow Response Times

**Diagnosis:**
1. Check database query performance
2. Profile Django with django-debug-toolbar locally
3. Check Gunicorn worker count

**Solution:**
1. Optimize database queries (use `.select_related()`)
2. Add database indexes
3. Increase Gunicorn workers
4. Enable Redis caching

---

## Rollback Procedures

### Rollback to Previous Deployment

If new deployment causes issues:

**Option 1: Via Render Dashboard**
1. Go to **Deployments** tab
2. Find previous successful deployment
3. Click **"Deploy"** on that specific commit

**Option 2: Via Git (Recommended)**
1. Identify last stable commit: `git log --oneline`
2. Reset to stable version: `git revert HEAD`
3. Create new commit: `git commit -m "Rollback to stable version"`
4. Push: `git push origin main`
5. Render automatically rebuilds from this commit

**Option 3: Emergency Revert**
If unable to push:
1. Contact Render support for immediate rollback
2. They can restore from previous deployment snapshot

### Database Rollback

If a migration causes issues:

1. **Identify problematic migration:**
   ```bash
   python manage.py showmigrations
   ```

2. **Create rollback migration:**
   ```bash
   python manage.py makemigrations --name rollback_<issue>
   ```

3. **Apply rollback:**
   ```bash
   python manage.py migrate <app> <previous_migration_number>
   ```

4. **Commit and push:**
   ```bash
   git commit -m "Rollback migration: <reason>"
   git push origin main
   ```

---

## Scaling Considerations

### When to Scale

- Response times exceed 1 second
- Database connection pool exhausted
- CPU usage consistently >80%
- Memory usage consistently >90%

### Scaling Options

1. **Upgrade Render Plan** (Web Service)
   - Pro plan: More resources, better performance
   - Private environment: Dedicated resources

2. **Upgrade Database Plan**
   - Standard plan: Better performance
   - Add read replicas for read-heavy workloads

3. **Add Caching Layer**
   - Render Redis service for session/query caching
   - Reduces database load

4. **Load Balancing**
   - Deploy multiple web service instances
   - Render provides automatic load balancing

---

## Security Checklist

Before deploying to production:

- [ ] `DEBUG=False` (not `True`)
- [ ] `SECRET_KEY` is long and random
- [ ] `ALLOWED_HOSTS` configured correctly
- [ ] `CORS_ALLOWED_ORIGINS` restricted to frontend domain
- [ ] `CSRF_TRUSTED_ORIGINS` configured
- [ ] `SENDGRID_API_KEY` is valid
- [ ] All sensitive data in environment variables (not in code)
- [ ] HTTPS enforced (Render default)
- [ ] Database backups enabled
- [ ] Admin user created
- [ ] No test data in production

---

## Post-Deployment Deployment Checklist

- [ ] All endpoints responding with 200/201/etc. (not 500)
- [ ] User registration works
- [ ] Login returns tokens
- [ ] Password reset emails send
- [ ] Bookings can be created/read/updated/deleted
- [ ] Admin endpoints accessible to superusers only
- [ ] Static files (favicon, CSS if applicable) serve correctly
- [ ] Logs show no errors
- [ ] Database migrations completed successfully
- [ ] Admin user created
- [ ] Team notified of deployment

---

## Contact & Support

For deployment issues:
1. Check logs in Render Dashboard
2. Review this guide's troubleshooting section
3. Check Django documentation
4. Contact Render support: support@render.com
5. Contact project maintainer

---

## Appendix: Common Commands

```bash
# View production logs (tail last 50 lines)
render logs -l 50

# SSH into production (if enabled)
ssh user@ese-booking-backend.onrender.com

# Run migration on production
python manage.py migrate

# Create superuser on production
python manage.py createsuperuser

# View database statistics
python manage.py dbshell
SELECT COUNT(*) FROM auth_user;

# Clear old sessions
python manage.py cleanupsessions
```
