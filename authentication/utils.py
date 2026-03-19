import secrets
from django.conf import settings
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


def generate_reset_token():
    """Generate a secure random token for password reset"""
    return secrets.token_urlsafe(32)


def send_password_reset_email(user_email, reset_token):
    """
    Send password reset email using SendGrid
    
    Args:
        user_email: Email address of the user
        reset_token: The password reset token
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    # Build the reset URL
    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
    
    # Create email content
    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #333;">Password Reset Request</h2>
        <p style="color: #666; line-height: 1.6;">
            You requested to reset your password. Click the button below to proceed:
        </p>
        <div style="text-align: center; margin: 30px 0;">
            <a href="{reset_url}" 
               style="display: inline-block; padding: 12px 24px; background-color: #007bff; 
                      color: white; text-decoration: none; border-radius: 4px; font-weight: bold;">
                Reset Password
            </a>
        </div>
        <p style="color: #666; line-height: 1.6;">
            Or copy and paste this link in your browser:
        </p>
        <p style="background-color: #f5f5f5; padding: 10px; border-radius: 4px; word-break: break-all;">
            <a href="{reset_url}" style="color: #007bff;">{reset_url}</a>
        </p>
        <p style="color: #999; font-size: 14px; margin-top: 30px;">
            <strong>This link will expire in 1 hour.</strong>
        </p>
        <p style="color: #999; font-size: 14px;">
            If you didn't request this, please ignore this email.
        </p>
    </div>
    """
    
    message = Mail(
        from_email=settings.FROM_EMAIL,
        to_emails=user_email,
        subject='Reset Your Password',
        html_content=html_content
    )
    
    try:
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(message)
        return response.status_code == 202  # SendGrid returns 202 for success
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False
