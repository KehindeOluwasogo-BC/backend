from django.contrib.auth.models import User
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import UserProfile, AdminActivityLog


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    memorable_information = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ('username', 'password', 'email', 'first_name', 'last_name', 'memorable_information')

    def create(self, validated_data):
        memorable_info = validated_data.pop('memorable_information', '')
        
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        
        # Set memorable information on profile
        if hasattr(user, 'profile'):
            user.profile.memorable_information = memorable_info
            user.profile.save()
        
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ('profile_picture', 'bio', 'memorable_information', 'created_at', 'updated_at')
        read_only_fields = ('created_at', 'updated_at')


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    profile_picture = serializers.SerializerMethodField()
    can_revoke_admins = serializers.SerializerMethodField()
    memorable_information = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'full_name', 'is_superuser', 'is_active', 'profile_picture', 'can_revoke_admins', 'memorable_information')
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()
    
    def get_profile_picture(self, obj):
        if hasattr(obj, 'profile') and obj.profile.profile_picture:
            return obj.profile.profile_picture
        return None
    
    def get_can_revoke_admins(self, obj):
        if hasattr(obj, 'profile'):
            return obj.profile.can_revoke_admins
        return True  # Default to True for backwards compatibility
    
    def get_memorable_information(self, obj):
        if hasattr(obj, 'profile'):
            return obj.profile.memorable_information
        return ""


class UpdateProfilePictureSerializer(serializers.Serializer):
    profile_picture = serializers.URLField(max_length=500)


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()
    
    def validate_email(self, value):
        """Check if user with this email exists"""
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("No user found with this email address.")
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    
    def validate_new_password(self, value):
        """Validate the new password"""
        return value

class CreateAdminSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    can_revoke_admins = serializers.BooleanField(default=True)
    memorable_information = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = User
        fields = ('username', 'password', 'email', 'first_name', 'last_name', 'can_revoke_admins', 'memorable_information')
    
    def create(self, validated_data):
        can_revoke_admins = validated_data.pop('can_revoke_admins', True)
        memorable_info = validated_data.pop('memorable_information', '')
        
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            is_superuser=True,
            is_staff=True
        )
        
        # Set the can_revoke_admins permission and memorable info on user profile
        if hasattr(user, 'profile'):
            user.profile.can_revoke_admins = can_revoke_admins
            user.profile.memorable_information = memorable_info
            user.profile.save()
        
        return user


class AdminUserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    date_joined = serializers.DateTimeField(read_only=True)
    last_login = serializers.DateTimeField(read_only=True)
    can_revoke_admins = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'full_name', 
                  'is_superuser', 'is_staff', 'date_joined', 'last_login', 'can_revoke_admins')
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username
    
    def get_can_revoke_admins(self, obj):
        if hasattr(obj, 'profile'):
            return obj.profile.can_revoke_admins
        return True  # Default to True for backwards compatibility


class AdminActivityLogSerializer(serializers.ModelSerializer):
    admin_username = serializers.CharField(source='admin_user.username', read_only=True)
    admin_full_name = serializers.SerializerMethodField()
    target_username = serializers.CharField(source='target_user.username', read_only=True, allow_null=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    
    class Meta:
        model = AdminActivityLog
        fields = ('id', 'admin_user', 'admin_username', 'admin_full_name', 
                  'action', 'action_display', 'target_user', 'target_username', 
                  'description', 'timestamp', 'ip_address')
        read_only_fields = ('timestamp',)
    
    def get_admin_full_name(self, obj):
        return f"{obj.admin_user.first_name} {obj.admin_user.last_name}".strip() or obj.admin_user.username
