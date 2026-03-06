from django.contrib import admin
from .models import PasswordResetToken, PasswordResetAttempt, UserProfile, AdminActivityLog, AccountHistory


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'profile_picture', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('user__username', 'user__email', 'bio')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'token', 'created_at', 'expires_at', 'is_used')
    list_filter = ('is_used', 'created_at')
    search_fields = ('user__username', 'user__email', 'token')
    readonly_fields = ('created_at',)


@admin.register(PasswordResetAttempt)
class PasswordResetAttemptAdmin(admin.ModelAdmin):
    list_display = ('email', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('email',)
    readonly_fields = ('created_at',)


@admin.register(AdminActivityLog)
class AdminActivityLogAdmin(admin.ModelAdmin):
    list_display = ('admin_user', 'action', 'target_user', 'timestamp', 'ip_address')
    list_filter = ('action', 'timestamp')
    search_fields = ('admin_user__username', 'target_user__username', 'description')
    readonly_fields = ('timestamp',)
    date_hierarchy = 'timestamp'


@admin.register(AccountHistory)
class AccountHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'event_type', 'performed_by', 'event_timestamp', 'ip_address')
    list_filter = ('event_type', 'event_timestamp')
    search_fields = ('user__username', 'performed_by__username', 'description')
    readonly_fields = ('event_timestamp',)
    date_hierarchy = 'event_timestamp'
