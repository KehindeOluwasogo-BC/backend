from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import Booking
from .services import SERVICE_CATALOG

class BookingSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    service_duration = serializers.SerializerMethodField()
    estimated_end_time = serializers.SerializerMethodField()
    
    class Meta:
        model = Booking
        fields = ('id', 'user', 'username', 'full_name', 'email', 'service', 
                 'booking_date', 'booking_time', 'notes', 'status', 
                 'created_at', 'updated_at', 'service_duration', 'estimated_end_time')
        read_only_fields = ('user', 'username', 'service_duration', 'estimated_end_time')
    
    def get_service_duration(self, obj):
        """Return the duration of the service in minutes"""
        return obj.get_service_duration_minutes()
    
    def get_estimated_end_time(self, obj):
        """Calculate and return the estimated end time of the booking"""
        from datetime import datetime, timedelta
        start_datetime = datetime.combine(obj.booking_date, obj.booking_time)
        duration = obj.get_service_duration_minutes()
        end_datetime = start_datetime + timedelta(minutes=duration)
        return end_datetime.time().strftime('%H:%M')
    
    def validate_service(self, value):
        """Validate that the service exists in the catalog"""
        if value not in SERVICE_CATALOG:
            valid_services = ', '.join(SERVICE_CATALOG.keys())
            raise serializers.ValidationError(
                f"'{value}' is not a valid service. Valid services are: {valid_services}"
            )
        return value
    
    def validate(self, data):
        """
        Check for booking conflicts before creating/updating
        """
        # If updating, use instance values for fields not being changed
        if self.instance:
            # Check if only status is being updated (skip time validation in this case)
            only_status_update = len(data) == 1 and 'status' in data
            
            if only_status_update:
                # Skip validation for status-only updates
                return data
            
            # Merge with existing instance data
            booking_data = {
                'user': self.instance.user,
                'full_name': data.get('full_name', self.instance.full_name),
                'email': data.get('email', self.instance.email),
                'service': data.get('service', self.instance.service),
                'booking_date': data.get('booking_date', self.instance.booking_date),
                'booking_time': data.get('booking_time', self.instance.booking_time),
                'notes': data.get('notes', self.instance.notes),
                'status': data.get('status', self.instance.status),
            }
            booking = Booking(**booking_data)
            booking.pk = self.instance.pk
        else:
            # Creating new booking
            booking = Booking(**data)
        
        # Check if the slot is available (only validate time-related fields if they changed)
        try:
            booking.clean()
        except DjangoValidationError as e:
            # Convert Django validation error to DRF validation error
            raise serializers.ValidationError(e.message_dict if hasattr(e, 'message_dict') else str(e))
        
        return data
    
    def update(self, instance, validated_data):
        # Store old status for email notifications
        old_status = instance.status
        
        # Prevent regular users from updating status
        request = self.context.get('request')
        if request and not request.user.is_superuser:
            # Remove status from validated_data if user is not a superuser
            validated_data.pop('status', None)
        
        # Update all provided fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Store the old status in the instance for email notification
        instance._old_status = old_status
        
        # Save the instance to persist changes to database
        instance.save()
        
        return instance
