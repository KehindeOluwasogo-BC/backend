from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from .views import (
    AuthRootView,
    RegisterView, 
    UserInfoView,
    RequestPasswordResetView,
    ValidateResetTokenView,
    ResetPasswordView,
    UpdateProfilePictureView,
    CreateAdminView,
    ListAdminsView,
    RevokeAdminPrivilegesView,
    AdminActivityLogView,
    ListUsersView,
    CreateUserAccountView,
    ChangeUserPasswordView,
    SendResetLinkView,
    ToggleUserActiveView
)

urlpatterns = [
    path('', AuthRootView.as_view(), name='auth_root'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', RegisterView.as_view(), name='register'),
    path('user/', UserInfoView.as_view(), name='user_info'),
    path('profile/picture/', UpdateProfilePictureView.as_view(), name='update_profile_picture'),
    path('password-reset/request/', RequestPasswordResetView.as_view(), name='password_reset_request'),
    path('password-reset/validate/', ValidateResetTokenView.as_view(), name='password_reset_validate'),
    path('password-reset/confirm/', ResetPasswordView.as_view(), name='password_reset_confirm'),
    # Admin management endpoints
    path('admin/create/', CreateAdminView.as_view(), name='create_admin'),
    path('admin/list/', ListAdminsView.as_view(), name='list_admins'),
    path('admin/revoke/', RevokeAdminPrivilegesView.as_view(), name='revoke_admin'),
    path('admin/activity-logs/', AdminActivityLogView.as_view(), name='admin_activity_logs'),
    # User management endpoints
    path('users/list/', ListUsersView.as_view(), name='list_users'),
    path('users/create/', CreateUserAccountView.as_view(), name='create_user'),
    path('users/change-password/', ChangeUserPasswordView.as_view(), name='change_user_password'),
    path('users/send-reset-link/', SendResetLinkView.as_view(), name='send_reset_link'),
    path('users/toggle-active/', ToggleUserActiveView.as_view(), name='toggle_user_active'),
]