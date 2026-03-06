from rest_framework import serializers
from .models import Booking

class BookingSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = Booking
        fields = ('id', 'user', 'username', 'full_name', 'email', 'service', 'booking_date', 'booking_time', 'notes', 'status', 'created_at', 'updated_at')
        read_only_fields = ('user', 'username')
    
    def update(self, instance, validated_data):
        # Prevent regular users from updating status
        request = self.context.get('request')
        if request and not request.user.is_superuser:
            # Remove status from validated_data if user is not a superuser
            validated_data.pop('status', None)
            # If the booking was previously confirmed/completed/cancelled, reset to pending
            if instance.status != 'pending':
                instance.status = 'pending'
        return super().update(instance, validated_data)