from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta
from .services import get_service_duration, get_service_buffer, SERVICE_CATALOG

class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    full_name = models.CharField(max_length=120)
    email = models.EmailField()
    service = models.CharField(max_length=120) # e.g., "Haircut", "Massage", etc.
    booking_date = models.DateField()
    booking_time = models.TimeField()
    notes = models.TextField(blank=True)

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("cancelled", "Cancelled"),
        ("completed", "Completed"),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-booking_date', '-booking_time']
        indexes = [
            models.Index(fields=['booking_date', 'booking_time']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.full_name} - {self.service} ({self.booking_date} {self.booking_time})"
    
    def get_service_duration_minutes(self):
        """Get duration of this booking's service in minutes"""
        return get_service_duration(self.service)
    
    def get_booking_time_range(self):
        """
        Get the time range for this booking including buffers.
        Returns (start_time, end_time) as datetime objects.
        """
        buffer_before, buffer_after = get_service_buffer(self.service)
        duration = get_service_duration(self.service)
        
        # Convert to datetime for calculations
        booking_datetime = datetime.combine(self.booking_date, self.booking_time)
        
        # Calculate actual start and end with buffers
        start_with_buffer = booking_datetime - timedelta(minutes=buffer_before)
        end_with_buffer = booking_datetime + timedelta(minutes=duration + buffer_after)
        
        return start_with_buffer, end_with_buffer
    
    def check_availability(self, exclude_self=True):
        """
        Check if this time slot is available considering service duration.
        Returns True if available, False if there's a conflict.
        """
        start_time, end_time = self.get_booking_time_range()
        
        # Query for bookings on the same date that are active
        same_day_bookings = Booking.objects.filter(
            booking_date=self.booking_date,
            status__in=['pending', 'confirmed']
        )
        
        # Exclude current booking when updating
        if exclude_self and self.pk:
            same_day_bookings = same_day_bookings.exclude(pk=self.pk)
        
        # Check each booking for time overlap
        for booking in same_day_bookings:
            other_start, other_end = booking.get_booking_time_range()
            
            # Check if time ranges overlap
            if start_time < other_end and end_time > other_start:
                return False
        
        return True
    
    def clean(self):
        """Validate booking before saving"""
        super().clean()
        
        # Validate service exists in catalog
        if self.service and self.service not in SERVICE_CATALOG:
            raise ValidationError({
                'service': f"'{self.service}' is not a valid service. Valid services are: {', '.join(SERVICE_CATALOG.keys())}"
            })
        
        # Check for past bookings
        from django.utils import timezone
        today = timezone.now().date()
        if self.booking_date < today:
            raise ValidationError({
                'booking_date': "Cannot create bookings for past dates."
            })
        
        # Check if booking time is within business hours (9 AM - 7:30 PM)
        start_time, end_time = self.get_booking_time_range()
        business_start = datetime.combine(self.booking_date, datetime.strptime('09:00', '%H:%M').time())
        business_end = datetime.combine(self.booking_date, datetime.strptime('19:30', '%H:%M').time())
        
        if start_time < business_start:
            raise ValidationError({
                'booking_time': f"Booking starts before business hours. Earliest time for {self.service} is {business_start.strftime('%I:%M %p')}."
            })
        
        if end_time > business_end:
            raise ValidationError({
                'booking_time': f"Booking extends beyond business hours. Latest time for {self.service} is {(business_end - timedelta(minutes=get_service_duration(self.service))).strftime('%I:%M %p')}."
            })
        
        # Check availability for new bookings or when date/time/service changes
        if not self.pk or self._state.adding:
            # New booking
            if not self.check_availability(exclude_self=False):
                raise ValidationError({
                    'booking_time': f"This time slot is not available for {self.service}. Please choose a different time."
                })
        else:
            # Updating existing booking - check if critical fields changed
            old_booking = Booking.objects.get(pk=self.pk)
            if (old_booking.booking_date != self.booking_date or 
                old_booking.booking_time != self.booking_time or
                old_booking.service != self.service):
                if not self.check_availability(exclude_self=True):
                    raise ValidationError({
                        'booking_time': f"This time slot is not available for {self.service}. Please choose a different time."
                    })
    
    def save(self, *args, **kwargs):
        """Override save to trigger validation"""
        self.full_clean()
        super().save(*args, **kwargs)
