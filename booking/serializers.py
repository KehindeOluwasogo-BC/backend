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
        # Create a temporary booking instance to check availability
        booking = Booking(**data)
        
        # If updating, set the pk
        if self.instance:
            booking.pk = self.instance.pk
            booking.user = self.instance.user
        
        # Check if the slot is available
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
            # If the booking was previously confirmed/completed/cancelled, reset to pending
            if instance.status != 'pending':
                instance.status = 'pending'
        
        # Store the old status in the instance for email notification
        instance._old_status = old_status
        
        return super().update(instance, validated_data)
