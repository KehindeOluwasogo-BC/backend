from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    profile_picture = models.URLField(max_length=500, blank=True, null=True)
    bio = models.TextField(blank=True)
    memorable_information = models.TextField(blank=True, help_text="Memorable information for account recovery")
    can_revoke_admins = models.BooleanField(default=True, help_text="Can this admin revoke other admin privileges")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}'s profile"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Automatically create a profile when a user is created"""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save the profile when the user is saved"""
    if hasattr(instance, 'profile'):
        instance.profile.save()


class PasswordResetToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_reset_tokens')
    token = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        # Set expiration to 1 hour from now if not set
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=1)
        super().save(*args, **kwargs)
    
    def is_valid(self):
        """Check if token is valid (not expired and not used)"""
        return not self.is_used and timezone.now() < self.expires_at
    
    def __str__(self):
        return f"Password reset token for {self.user.username}"


class PasswordResetAttempt(models.Model):
    email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    @staticmethod
    def is_rate_limited(email):
        """
        Check if an email is rate limited (3+ attempts in last 10 minutes)
        Returns (is_limited, seconds_remaining)
        """
        time_threshold = timezone.now() - timedelta(minutes=10)
        recent_attempts = PasswordResetAttempt.objects.filter(
            email=email,
            created_at__gte=time_threshold
        ).order_by('-created_at')
        
        if recent_attempts.count() >= 3:
            # Calculate time remaining until rate limit expires
            oldest_attempt = recent_attempts.last()
            time_until_retry = (oldest_attempt.created_at + timedelta(minutes=10)) - timezone.now()
            seconds_remaining = int(time_until_retry.total_seconds())
            return True, max(0, seconds_remaining)
        
        return False, 0
    
    @staticmethod
    def cleanup_old_attempts():
        """Remove attempts older than 10 minutes"""
        time_threshold = timezone.now() - timedelta(minutes=10)
        PasswordResetAttempt.objects.filter(created_at__lt=time_threshold).delete()
    
    def __str__(self):
        return f"Reset attempt for {self.email} at {self.created_at}"


class AdminActivityLog(models.Model):
    """Track activities performed by admin users"""
    ACTION_CHOICES = [
        ('CREATE_ADMIN', 'Created Admin User'),
        ('REVOKE_ADMIN', 'Revoked Admin Privileges'),
        ('LOGIN', 'Logged In'),
        ('CREATE_BOOKING', 'Created Booking'),
        ('UPDATE_BOOKING', 'Updated Booking'),
        ('DELETE_BOOKING', 'Deleted Booking'),
        ('OTHER', 'Other Action'),
    ]
    
    admin_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='admin_actions')
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    target_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='targeted_by_admin')
    description = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Admin Activity Log'
        verbose_name_plural = 'Admin Activity Logs'
    
    def __str__(self):
        return f"{self.admin_user.username} - {self.get_action_display()} at {self.timestamp}"


class AccountHistory(models.Model):
    """Track account lifecycle events (creation, revocation, deletion)"""
    EVENT_CHOICES = [
        ('CREATED', 'Account Created'),
        ('REVOKED', 'Admin Privileges Revoked'),
        ('DELETED', 'Account Deleted'),
        ('REACTIVATED', 'Account Reactivated'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='account_history')
    event_type = models.CharField(max_length=20, choices=EVENT_CHOICES)
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='performed_account_actions')
    description = models.TextField(blank=True)
    event_timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        ordering = ['-event_timestamp']
        verbose_name = 'Account History'
        verbose_name_plural = 'Account Histories'
    
    def __str__(self):
        return f"{self.user.username} - {self.get_event_type_display()} at {self.event_timestamp}"
