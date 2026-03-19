from django.contrib.auth.models import User
from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status
from rest_framework.views import APIView

from .serializers import (
    RegisterSerializer, 
    UserSerializer, 
    PasswordResetRequestSerializer, 
    PasswordResetConfirmSerializer,
    UpdateProfilePictureSerializer
)
from .models import PasswordResetToken, PasswordResetAttempt, UserProfile, AccountHistory
from .utils import generate_reset_token, send_password_reset_email


class AuthRootView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        return Response(
            {
                'message': 'Authentication API root',
                'endpoints': {
                    'token': '/api/auth/token/',
                    'token_refresh': '/api/auth/token/refresh/',
                    'register': '/api/auth/register/',
                    'user': '/api/auth/user/',
                    'password_reset_request': '/api/auth/password-reset/request/',
                },
            },
            status=status.HTTP_200_OK,
        )


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Log account creation in AccountHistory
        AccountHistory.objects.create(
            user=user,
            event_type='CREATED',
            performed_by=None,  # Self-registration
            description="Self-registered account",
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)


class UserInfoView(APIView):
    permission_classes = (IsAuthenticated,)
    
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class RequestPasswordResetView(APIView):
    permission_classes = (AllowAny,)
    
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            
            # Check rate limiting
            is_limited, seconds_remaining = PasswordResetAttempt.is_rate_limited(email)
            if is_limited:
                minutes_remaining = seconds_remaining // 60
                seconds_in_minute = seconds_remaining % 60
                return Response({
                    'error': 'Too many reset attempts. Please try again later.',
                    'rate_limited': True,
                    'seconds_remaining': seconds_remaining,
                    'retry_message': f'Please wait {minutes_remaining} minutes and {seconds_in_minute} seconds before trying again.'
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)
            
            # Log this attempt
            PasswordResetAttempt.objects.create(email=email)
            
            # Clean up old attempts (optional optimization)
            PasswordResetAttempt.cleanup_old_attempts()
            
            user = User.objects.get(email=email)
            
            # Generate token
            token = generate_reset_token()
            
            # Create password reset token record
            PasswordResetToken.objects.create(
                user=user,
                token=token
            )
            
            # Send email
            email_sent = send_password_reset_email(user.email, token)
            
            if email_sent:
                return Response({
                    'message': 'Password reset email sent successfully. Please check your inbox.'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'error': 'Failed to send email. Please try again later.'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ValidateResetTokenView(APIView):
    permission_classes = (AllowAny,)
    
    def post(self, request):
        token = request.data.get('token')
        
        if not token:
            return Response({
                'error': 'Token is required.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            reset_token = PasswordResetToken.objects.get(token=token)
            
            if reset_token.is_valid():
                return Response({
                    'valid': True,
                    'message': 'Token is valid.'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'valid': False,
                    'error': 'Token has expired or already been used.'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        except PasswordResetToken.DoesNotExist:
            return Response({
                'valid': False,
                'error': 'Invalid token.'
            }, status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordView(APIView):
    permission_classes = (AllowAny,)
    
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        
        if serializer.is_valid():
            token = serializer.validated_data['token']
            new_password = serializer.validated_data['new_password']
            
            try:
                reset_token = PasswordResetToken.objects.get(token=token)
                
                if not reset_token.is_valid():
                    return Response({
                        'error': 'Token has expired or already been used.'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Update user's password
                user = reset_token.user
                user.set_password(new_password)
                user.save()
                
                # Mark token as used
                reset_token.is_used = True
                reset_token.save()
                
                return Response({
                    'message': 'Password has been reset successfully. You can now login with your new password.'
                }, status=status.HTTP_200_OK)
            
            except PasswordResetToken.DoesNotExist:
                return Response({
                    'error': 'Invalid token.'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UpdateProfilePictureView(APIView):
    permission_classes = (IsAuthenticated,)
    
    def post(self, request):
        serializer = UpdateProfilePictureSerializer(data=request.data)
        
        if serializer.is_valid():
            profile_picture_url = serializer.validated_data['profile_picture']
            
            # Get or create user profile
            profile, created = UserProfile.objects.get_or_create(user=request.user)
            profile.profile_picture = profile_picture_url
            profile.save()
            
            return Response({
                'message': 'Profile picture updated successfully',
                'profile_picture': profile_picture_url
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CreateAdminView(APIView):
    """Allow super users to create other admin users"""
    permission_classes = (IsAuthenticated,)
    
    def get_client_ip(self, request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def post(self, request):
        # Check if requesting user is a superuser
        if not request.user.is_superuser:
            return Response({
                'error': 'Only super users can create admin accounts.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        from .serializers import CreateAdminSerializer
        serializer = CreateAdminSerializer(data=request.data)
        
        if serializer.is_valid():
            new_admin = serializer.save()
            
            # Log the activity in AdminActivityLog
            from .models import AdminActivityLog, AccountHistory
            AdminActivityLog.objects.create(
                admin_user=request.user,
                action='CREATE_ADMIN',
                target_user=new_admin,
                description=f"Created admin user: {new_admin.username}",
                ip_address=self.get_client_ip(request)
            )
            
            # Log in AccountHistory
            AccountHistory.objects.create(
                user=new_admin,
                event_type='CREATED',
                performed_by=request.user,
                description=f"Admin account created by {request.user.username}",
                ip_address=self.get_client_ip(request)
            )
            
            return Response({
                'message': f'Admin user {new_admin.username} created successfully.',
                'user': {
                    'id': new_admin.id,
                    'username': new_admin.username,
                    'email': new_admin.email,
                    'first_name': new_admin.first_name,
                    'last_name': new_admin.last_name
                }
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ListAdminsView(APIView):
    """List all admin users - only accessible by super users"""
    permission_classes = (IsAuthenticated,)
    
    def get(self, request):
        if not request.user.is_superuser:
            return Response({
                'error': 'Only super users can view admin list.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        from .serializers import AdminUserSerializer
        admins = User.objects.filter(is_superuser=True).order_by('-date_joined')
        serializer = AdminUserSerializer(admins, many=True)
        
        return Response({
            'admins': serializer.data,
            'count': admins.count()
        }, status=status.HTTP_200_OK)


class RevokeAdminPrivilegesView(APIView):
    """Revoke admin privileges from a user"""
    permission_classes = (IsAuthenticated,)
    
    def get_client_ip(self, request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def post(self, request):
        if not request.user.is_superuser:
            return Response({
                'error': 'Only super users can revoke admin privileges.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Check if the requesting admin has permission to revoke
        if hasattr(request.user, 'profile') and not request.user.profile.can_revoke_admins:
            return Response({
                'error': 'You do not have permission to revoke admin privileges.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response({
                'error': 'user_id is required.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            target_user = User.objects.get(id=user_id)
            
            # Prevent self-revocation
            if target_user.id == request.user.id:
                return Response({
                    'error': 'You cannot revoke your own admin privileges.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if target is actually an admin
            if not target_user.is_superuser:
                return Response({
                    'error': 'This user is not an admin.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Revoke privileges
            target_user.is_superuser = False
            target_user.is_staff = False
            target_user.save()
            
            # Log the activity in AdminActivityLog
            from .models import AdminActivityLog
            AdminActivityLog.objects.create(
                admin_user=request.user,
                action='REVOKE_ADMIN',
                target_user=target_user,
                description=f"Revoked admin privileges from: {target_user.username}",
                ip_address=self.get_client_ip(request)
            )
            
            # Log in AccountHistory
            AccountHistory.objects.create(
                user=target_user,
                event_type='REVOKED',
                performed_by=request.user,
                description=f"Admin privileges revoked by {request.user.username}",
                ip_address=self.get_client_ip(request)
            )
            
            return Response({
                'message': f'Admin privileges revoked from {target_user.username}.'
            }, status=status.HTTP_200_OK)
        
        except User.DoesNotExist:
            return Response({
                'error': 'User not found.'
            }, status=status.HTTP_404_NOT_FOUND)


class AdminActivityLogView(APIView):
    """View admin activity logs - only accessible by super users"""
    permission_classes = (IsAuthenticated,)
    
    def get(self, request):
        if not request.user.is_superuser:
            return Response({
                'error': 'Only super users can view activity logs.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        from .models import AdminActivityLog
        from .serializers import AdminActivityLogSerializer
        
        # Get optional filters
        limit = request.query_params.get('limit', 50)
        action = request.query_params.get('action', None)
        
        logs = AdminActivityLog.objects.all()
        
        # Filter by action if specified
        if action:
            logs = logs.filter(action=action)
        
        # Limit results
        try:
            limit = int(limit)
            if limit > 500:
                limit = 500  # Max limit
        except ValueError:
            limit = 50
        
        logs = logs[:limit]
        serializer = AdminActivityLogSerializer(logs, many=True)
        
        return Response({
            'logs': serializer.data,
            'count': len(serializer.data)
        }, status=status.HTTP_200_OK)


class ListUsersView(APIView):
    """List all regular (non-admin) users - only accessible by super users"""
    permission_classes = (IsAuthenticated,)
    
    def get(self, request):
        if not request.user.is_superuser:
            return Response({
                'error': 'Only super users can view user list.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get all regular users (not superusers)
        users = User.objects.filter(is_superuser=False).order_by('-date_joined')
        
        from .serializers import UserSerializer
        serializer = UserSerializer(users, many=True)
        
        return Response({
            'users': serializer.data,
            'count': users.count()
        }, status=status.HTTP_200_OK)


class CreateUserAccountView(APIView):
    """Allow admins to create regular user accounts"""
    permission_classes = (IsAuthenticated,)
    
    def get_client_ip(self, request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def post(self, request):
        # Check if requesting user is a superuser
        if not request.user.is_superuser:
            return Response({
                'error': 'Only super users can create user accounts.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = RegisterSerializer(data=request.data)
        
        if serializer.is_valid():
            new_user = serializer.save()
            
            # Log in AccountHistory
            AccountHistory.objects.create(
                user=new_user,
                event_type='CREATED',
                performed_by=request.user,
                description=f"User account created by admin {request.user.username}",
                ip_address=self.get_client_ip(request)
            )
            
            # Log admin activity
            from .models import AdminActivityLog
            AdminActivityLog.objects.create(
                admin_user=request.user,
                action='OTHER',
                target_user=new_user,
                description=f"Created user account: {new_user.username}",
                ip_address=self.get_client_ip(request)
            )
            
            return Response({
                'message': f'User account {new_user.username} created successfully.',
                'user': {
                    'id': new_user.id,
                    'username': new_user.username,
                    'email': new_user.email,
                    'first_name': new_user.first_name,
                    'last_name': new_user.last_name
                }
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangeUserPasswordView(APIView):
    """Allow admins to change any user's password"""
    permission_classes = (IsAuthenticated,)
    
    def get_client_ip(self, request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def post(self, request):
        # Only superusers can change passwords
        if not request.user.is_superuser:
            return Response({
                'error': 'Only super users can change user passwords.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        user_id = request.data.get('user_id')
        new_password = request.data.get('new_password')
        
        if not user_id or not new_password:
            return Response({
                'error': 'user_id and new_password are required.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            target_user = User.objects.get(id=user_id)
            
            # Validate password
            from django.contrib.auth.password_validation import validate_password
            try:
                validate_password(new_password, target_user)
            except Exception as e:
                return Response({
                    'error': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Set new password
            target_user.set_password(new_password)
            target_user.save()
            
            # Log admin activity
            from .models import AdminActivityLog
            AdminActivityLog.objects.create(
                admin_user=request.user,
                action='OTHER',
                target_user=target_user,
                description=f"Changed password for user: {target_user.username}",
                ip_address=self.get_client_ip(request)
            )
            
            return Response({
                'message': f'Password changed successfully for {target_user.username}.'
            }, status=status.HTTP_200_OK)
        
        except User.DoesNotExist:
            return Response({
                'error': 'User not found.'
            }, status=status.HTTP_404_NOT_FOUND)


class SendResetLinkView(APIView):
    """Allow admins to send password reset link to a user"""
    permission_classes = (IsAuthenticated,)
    
    def get_client_ip(self, request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def post(self, request):
        # Only superusers can send reset links to other users
        if not request.user.is_superuser:
            return Response({
                'error': 'Only super users can send reset links to users.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response({
                'error': 'user_id is required.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            target_user = User.objects.get(id=user_id)
            
            # Check if user has an email
            if not target_user.email:
                return Response({
                    'error': 'User does not have an email address.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Generate reset token
            token = generate_reset_token()
            PasswordResetToken.objects.create(
                user=target_user,
                token=token
            )
            
            # Send reset email
            send_password_reset_email(target_user.email, token)
            
            # Log admin activity
            from .models import AdminActivityLog
            AdminActivityLog.objects.create(
                admin_user=request.user,
                action='OTHER',
                target_user=target_user,
                description=f"Sent password reset link to user: {target_user.username}",
                ip_address=self.get_client_ip(request)
            )
            
            # Log in AccountHistory
            AccountHistory.objects.create(
                user=target_user,
                event_type='PASSWORD_RESET_INITIATED',
                performed_by=request.user,
                description=f"Admin {request.user.username} sent password reset link",
                ip_address=self.get_client_ip(request)
            )
            
            return Response({
                'message': f'Password reset link sent successfully to {target_user.email}.'
            }, status=status.HTTP_200_OK)
        
        except User.DoesNotExist:
            return Response({
                'error': 'User not found.'
            }, status=status.HTTP_404_NOT_FOUND)


class ToggleUserActiveView(APIView):
    """Allow admins to restrict/unrestrict user accounts"""
    permission_classes = (IsAuthenticated,)
    
    def get_client_ip(self, request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def post(self, request):
        # Only superusers can restrict/unrestrict accounts
        if not request.user.is_superuser:
            return Response({
                'error': 'Only super users can restrict/unrestrict user accounts.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response({
                'error': 'user_id is required.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            target_user = User.objects.get(id=user_id)
            
            # Don't allow restricting yourself
            if target_user.id == request.user.id:
                return Response({
                    'error': 'You cannot restrict your own account.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Toggle active status
            target_user.is_active = not target_user.is_active
            target_user.save()
            
            action_description = "restricted" if not target_user.is_active else "unrestricted"
            event_type = "RESTRICTED" if not target_user.is_active else "UNRESTRICTED"
            
            # Log admin activity
            from .models import AdminActivityLog
            AdminActivityLog.objects.create(
                admin_user=request.user,
                action='OTHER',
                target_user=target_user,
                description=f"{action_description.capitalize()} user account: {target_user.username}",
                ip_address=self.get_client_ip(request)
            )
            
            # Log in AccountHistory
            AccountHistory.objects.create(
                user=target_user,
                event_type=event_type,
                performed_by=request.user,
                description=f"Admin {request.user.username} {action_description} the account",
                ip_address=self.get_client_ip(request)
            )
            
            return Response({
                'message': f'User {target_user.username} has been {action_description} successfully.',
                'is_active': target_user.is_active
            }, status=status.HTTP_200_OK)
        
        except User.DoesNotExist:
            return Response({
                'error': 'User not found.'
            }, status=status.HTTP_404_NOT_FOUND)
