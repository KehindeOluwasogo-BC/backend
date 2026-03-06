from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from .serializers import BookingSerializer
from .models import Booking

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
        """
        user_id = self.request.data.get('user_id')
        
        # If admin and user_id is provided, create booking for that user
        if self.request.user.is_superuser and user_id:
            try:
                target_user = User.objects.get(id=user_id)
                serializer.save(user=target_user)
            except User.DoesNotExist:
                # If user not found, fall back to request user
                serializer.save(user=self.request.user)
        else:
            # Regular users or admin without user_id
            serializer.save(user=self.request.user)
