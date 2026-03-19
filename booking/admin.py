from django.contrib import admin
from .models import Booking
# Register your models here.


class BookingAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'service', 'booking_date', 'booking_time', 'status', 'created_at', 'updated_at')
    list_filter = ('status', 'booking_date')
    search_fields = ('full_name', 'email', 'service')

admin.site.register(Booking, BookingAdmin)
