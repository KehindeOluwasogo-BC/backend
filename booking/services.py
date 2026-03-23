"""
Service catalog with durations and details
"""
from datetime import timedelta

# Service catalog with durations in minutes
SERVICE_CATALOG = {
    'Haircut': {
        'duration': 60,  # minutes
        'description': 'Basic haircut service',
        'buffer_before': 15,  # minutes buffer before
        'buffer_after': 15,   # minutes buffer after
    },
    'Hair Coloring': {
        'duration': 120,
        'description': 'Full hair coloring service',
        'buffer_before': 15,
        'buffer_after': 30,
    },
    'Massage': {
        'duration': 90,
        'description': 'Relaxation massage therapy',
        'buffer_before': 10,
        'buffer_after': 20,
    },
    'Facial': {
        'duration': 75,
        'description': 'Facial treatment',
        'buffer_before': 15,
        'buffer_after': 15,
    },
    'Manicure': {
        'duration': 45,
        'description': 'Manicure service',
        'buffer_before': 10,
        'buffer_after': 10,
    },
    'Pedicure': {
        'duration': 60,
        'description': 'Pedicure service',
        'buffer_before': 10,
        'buffer_after': 15,
    },
    'Spa Package': {
        'duration': 180,
        'description': 'Full spa experience',
        'buffer_before': 20,
        'buffer_after': 30,
    },
    'Consultation': {
        'duration': 30,
        'description': 'Initial consultation',
        'buffer_before': 5,
        'buffer_after': 10,
    },
}


def get_service_duration(service_name):
    """
    Get the duration of a service in minutes.
    Returns default of 60 minutes if service not found.
    """
    service = SERVICE_CATALOG.get(service_name)
    if service:
        return service['duration']
    return 60  # default 1 hour


def get_service_buffer(service_name):
    """
    Get the buffer time (before and after) for a service.
    Returns (buffer_before, buffer_after) in minutes.
    """
    service = SERVICE_CATALOG.get(service_name)
    if service:
        return service.get('buffer_before', 15), service.get('buffer_after', 15)
    return 15, 15  # default 15 minutes before and after


def get_service_total_time(service_name):
    """
    Get total time needed including buffers in minutes.
    """
    duration = get_service_duration(service_name)
    buffer_before, buffer_after = get_service_buffer(service_name)
    return duration + buffer_before + buffer_after


def get_all_services():
    """
    Get list of all available services with their details.
    """
    return [
        {
            'name': name,
            'duration': details['duration'],
            'description': details['description'],
            'buffer_before': details['buffer_before'],
            'buffer_after': details['buffer_after'],
            'total_time': details['duration'] + details['buffer_before'] + details['buffer_after']
        }
        for name, details in SERVICE_CATALOG.items()
    ]


def time_ranges_overlap(start1, end1, start2, end2):
    """
    Check if two time ranges overlap.
    Times should be datetime.time objects or datetime objects.
    """
    return start1 < end2 and end1 > start2
