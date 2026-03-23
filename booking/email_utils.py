"""
Email utilities for booking notifications
"""
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def send_booking_confirmation(booking):
    """
    Send booking confirmation email to the user
    """
    if not settings.SENDGRID_API_KEY:
        logger.warning("SendGrid API key not configured. Email not sent.")
        return False
    
    subject = f"Booking Confirmation - {booking.service}"
    
    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #4CAF50;">Booking Confirmed!</h2>
        
        <p>Dear {booking.full_name},</p>
        
        <p>Your booking has been successfully created. Here are the details:</p>
        
        <div style="background-color: #f5f5f5; padding: 20px; border-radius: 5px; margin: 20px 0;">
            <p><strong>Service:</strong> {booking.service}</p>
            <p><strong>Date:</strong> {booking.booking_date.strftime('%B %d, %Y')}</p>
            <p><strong>Time:</strong> {booking.booking_time.strftime('%I:%M %p')}</p>
            <p><strong>Status:</strong> {booking.get_status_display()}</p>
            {f'<p><strong>Notes:</strong> {booking.notes}</p>' if booking.notes else ''}
        </div>
        
        <p>If you need to make any changes to your booking, please log in to your account.</p>
        
        <p style="color: #666; font-size: 12px; margin-top: 30px;">
            This is an automated message. Please do not reply to this email.
        </p>
    </div>
    """
    
    try:
        message = Mail(
            from_email=settings.FROM_EMAIL,
            to_emails=booking.email,
            subject=subject,
            html_content=html_content
        )
        
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(message)
        
        logger.info(f"Booking confirmation email sent to {booking.email}. Status: {response.status_code}")
        return True
    
    except Exception as e:
        logger.error(f"Failed to send booking confirmation email: {str(e)}")
        return False


def send_booking_update(booking, old_status=None):
    """
    Send email notification when booking is updated
    """
    if not settings.SENDGRID_API_KEY:
        logger.warning("SendGrid API key not configured. Email not sent.")
        return False
    
    # Determine the subject based on status change
    if old_status and old_status != booking.status:
        status_messages = {
            'confirmed': 'Booking Confirmed',
            'cancelled': 'Booking Cancelled', 
            'completed': 'Booking Completed',
            'pending': 'Booking Updated'
        }
        subject = f"{status_messages.get(booking.status, 'Booking Updated')} - {booking.service}"
    else:
        subject = f"Booking Updated - {booking.service}"
    
    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #2196F3;">Booking Updated</h2>
        
        <p>Dear {booking.full_name},</p>
        
        <p>Your booking has been updated. Here are the current details:</p>
        
        <div style="background-color: #f5f5f5; padding: 20px; border-radius: 5px; margin: 20px 0;">
            <p><strong>Service:</strong> {booking.service}</p>
            <p><strong>Date:</strong> {booking.booking_date.strftime('%B %d, %Y')}</p>
            <p><strong>Time:</strong> {booking.booking_time.strftime('%I:%M %p')}</p>
            <p><strong>Status:</strong> <span style="color: {'#4CAF50' if booking.status == 'confirmed' else '#FF9800' if booking.status == 'pending' else '#F44336'};">{booking.get_status_display()}</span></p>
            {f'<p><strong>Notes:</strong> {booking.notes}</p>' if booking.notes else ''}
        </div>
        
        {f'<p style="color: #4CAF50; font-weight: bold;">Your booking has been confirmed!</p>' if booking.status == 'confirmed' else ''}
        {f'<p style="color: #F44336;">Your booking has been cancelled. If this was not requested by you, please contact us immediately.</p>' if booking.status == 'cancelled' else ''}
        
        <p>If you have any questions, please contact us.</p>
        
        <p style="color: #666; font-size: 12px; margin-top: 30px;">
            This is an automated message. Please do not reply to this email.
        </p>
    </div>
    """
    
    try:
        message = Mail(
            from_email=settings.FROM_EMAIL,
            to_emails=booking.email,
            subject=subject,
            html_content=html_content
        )
        
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(message)
        
        logger.info(f"Booking update email sent to {booking.email}. Status: {response.status_code}")
        return True
    
    except Exception as e:
        logger.error(f"Failed to send booking update email: {str(e)}")
        return False


def send_booking_cancellation(booking):
    """
    Send cancellation confirmation email
    """
    if not settings.SENDGRID_API_KEY:
        logger.warning("SendGrid API key not configured. Email not sent.")
        return False
    
    subject = f"Booking Cancelled - {booking.service}"
    
    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #F44336;">Booking Cancelled</h2>
        
        <p>Dear {booking.full_name},</p>
        
        <p>Your booking has been cancelled:</p>
        
        <div style="background-color: #ffebee; padding: 20px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #F44336;">
            <p><strong>Service:</strong> {booking.service}</p>
            <p><strong>Date:</strong> {booking.booking_date.strftime('%B %d, %Y')}</p>
            <p><strong>Time:</strong> {booking.booking_time.strftime('%I:%M %p')}</p>
        </div>
        
        <p>If you did not request this cancellation, please contact us immediately.</p>
        
        <p>We hope to see you again soon!</p>
        
        <p style="color: #666; font-size: 12px; margin-top: 30px;">
            This is an automated message. Please do not reply to this email.
        </p>
    </div>
    """
    
    try:
        message = Mail(
            from_email=settings.FROM_EMAIL,
            to_emails=booking.email,
            subject=subject,
            html_content=html_content
        )
        
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(message)
        
        logger.info(f"Booking cancellation email sent to {booking.email}. Status: {response.status_code}")
        return True
    
    except Exception as e:
        logger.error(f"Failed to send booking cancellation email: {str(e)}")
        return False
