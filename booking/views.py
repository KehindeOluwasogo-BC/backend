from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from django.contrib.auth.models import User
from .serializers import BookingSerializer
from .models import Booking
from .email_utils import send_booking_confirmation, send_booking_update, send_booking_cancellation
from .services import (
    get_all_services, 
    get_service_duration, 
    get_service_buffer,
    get_service_total_time
)
from datetime import datetime, timedelta, time as dt_time
import logging

logger = logging.getLogger(__name__)


class BookingView(viewsets.ModelViewSet):
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return all bookings for superusers, only user's own bookings for regular users"""
        user = self.request.user
        if user.is_superuser:
            return Booking.objects.all()
        return Booking.objects.filter(user=user)
    
    def perform_create(self, serializer):
        """
        Allow admins to create bookings for other users by providing user_id.
        Regular users can only create bookings for themselves.
        Send confirmation email after booking is created.
        """
        user_id = self.request.data.get('user_id')
        
        # If admin and user_id is provided, create booking for that user
        if self.request.user.is_superuser and user_id:
            try:
                target_user = User.objects.get(id=user_id)
                booking = serializer.save(user=target_user)
            except User.DoesNotExist:
                # If user not found, fall back to request user
                booking = serializer.save(user=self.request.user)
        else:
            # Regular users or admin without user_id
            booking = serializer.save(user=self.request.user)
        
        # Send confirmation email
        try:
            send_booking_confirmation(booking)
        except Exception as e:
            logger.error(f"Failed to send booking confirmation for booking {booking.id}: {str(e)}")
    
    def perform_update(self, serializer):
        """
        Update booking and send notification email if status changed
        """
        try:
            old_status = serializer.instance.status if serializer.instance else None
            booking = serializer.save()
            
            # Send update email if status changed
            if old_status and old_status != booking.status:
                try:
                    if booking.status == 'cancelled':
                        send_booking_cancellation(booking)
                    else:
                        send_booking_update(booking, old_status=old_status)
                except Exception as e:
                    logger.error(f"Failed to send booking update email for booking {booking.id}: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to update booking {serializer.instance.id}: {str(e)}")
            raise
    
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def services(self, request):
        """
        Get list of all available services with their details.
        Usage: /api/bookings/services/
        """
        services = get_all_services()
        return Response({'services': services})
    
    @action(detail=False, methods=['get'])
    def available_slots(self, request):
        """
        Check available time slots for a specific date and service.
        Usage: /api/bookings/available_slots/?date=2024-01-15&service=Haircut
        
        If service is not provided, shows general availability.
        """
        date_str = request.query_params.get('date')
        service_name = request.query_params.get('service')
        
        if not date_str:
            return Response(
                {"error": "Date parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            booking_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {"error": "Invalid date format. Use YYYY-MM-DD"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if date is in the past
        from django.utils import timezone
        if booking_date < timezone.now().date():
            return Response(
                {"error": "Cannot check availability for past dates"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Business hours: 9:00 AM - 7:30 PM
        business_start_hour = 9
        business_end_hour = 19
        business_end_minute = 30
        
        # If service is specified, use its duration
        if service_name:
            service_duration = get_service_duration(service_name)
            buffer_before, buffer_after = get_service_buffer(service_name)
        else:
            # Default for general availability
            service_duration = 60
            buffer_before, buffer_after = 15, 15
        
        # Calculate how many slots we can check (every 30 minutes)
        slot_interval = 30  # minutes
        available_slots = []
        
        current_time = datetime.combine(booking_date, dt_time(business_start_hour, 0))
        end_time = datetime.combine(booking_date, dt_time(business_end_hour, business_end_minute))
        
        # Subtract service duration to ensure we don't suggest slots that extend beyond business hours
        last_slot_time = end_time - timedelta(minutes=service_duration + buffer_after)
        
        while current_time <= last_slot_time:
            # Create a temporary booking to check availability
            temp_booking = Booking(
                booking_date=booking_date,
                booking_time=current_time.time(),
                service=service_name or 'Haircut',  # Use Haircut as default
                status='pending'
            )
            
            # Check if this slot is available
            is_available = temp_booking.check_availability(exclude_self=False)
            
            slot_info = {
                'time': current_time.strftime('%H:%M'),
                'display_time': current_time.strftime('%I:%M %p'),
                'available': is_available,
            }
            
            # Add service-specific information if service was provided
            if service_name:
                end_datetime = current_time + timedelta(minutes=service_duration)
                slot_info['end_time'] = end_datetime.strftime('%H:%M')
                slot_info['end_display_time'] = end_datetime.strftime('%I:%M %p')
                slot_info['duration_minutes'] = service_duration
            
            available_slots.append(slot_info)
            
            # Move to next slot
            current_time += timedelta(minutes=slot_interval)
        
        response_data = {
            'date': date_str,
            'business_hours': {
                'start': f'{business_start_hour:02d}:00',
                'end': f'{business_end_hour:02d}:{business_end_minute:02d}'
            },
            'slots': available_slots
        }
        
        if service_name:
            response_data['service'] = service_name
            response_data['service_duration'] = service_duration
        
        # Add summary
        available_count = sum(1 for slot in available_slots if slot['available'])
        response_data['summary'] = {
            'total_slots': len(available_slots),
            'available_slots': available_count,
            'booked_slots': len(available_slots) - available_count
        }
        
        return Response(response_data)
    
    @action(detail=False, methods=['post'])
    def check_availability(self, request):
        """
        Check if a specific time slot is available for a service.
        POST body: {
            "date": "2024-01-15",
            "time": "10:00",
            "service": "Haircut"
        }
        """
        date_str = request.data.get('date')
        time_str = request.data.get('time')
        service_name = request.data.get('service')
        
        if not all([date_str, time_str, service_name]):
            return Response(
                {"error": "date, time, and service are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            booking_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            booking_time = datetime.strptime(time_str, '%H:%M').time()
        except ValueError:
            return Response(
                {"error": "Invalid date or time format. Use YYYY-MM-DD for date and HH:MM for time"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create temporary booking to check
        temp_booking = Booking(
            booking_date=booking_date,
            booking_time=booking_time,
            service=service_name,
            status='pending'
        )
        
        try:
            # This will check all validation rules including availability
            temp_booking.clean()
            
            # Get service details
            duration = get_service_duration(service_name)
            buffer_before, buffer_after = get_service_buffer(service_name)
            
            booking_datetime = datetime.combine(booking_date, booking_time)
            end_datetime = booking_datetime + timedelta(minutes=duration)
            
            return Response({
                'available': True,
                'message': f'This time slot is available for {service_name}',
                'details': {
                    'service': service_name,
                    'date': date_str,
                    'start_time': booking_time.strftime('%I:%M %p'),
                    'end_time': end_datetime.strftime('%I:%M %p'),
                    'duration_minutes': duration,
                    'buffer_before_minutes': buffer_before,
                    'buffer_after_minutes': buffer_after
                }
            })
        except Exception as e:
            return Response({
                'available': False,
                'message': str(e),
                'details': {
                    'service': service_name,
                    'date': date_str,
                    'time': time_str
                }
            }, status=status.HTTP_200_OK)
