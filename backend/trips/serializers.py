"""Serializers for Trip Planning API."""

from rest_framework import serializers


class PlanTripRequestSerializer(serializers.Serializer):
    current_location = serializers.CharField(
        required=True,
        allow_blank=False,
        max_length=300,
        error_messages={
            "required": "Origin location (current_location) is required.",
            "blank": "Origin location cannot be blank.",
        },
        help_text="Origin location address (e.g. 'Chicago, IL')",
    )
    pickup_location = serializers.CharField(
        required=True,
        allow_blank=False,
        max_length=300,
        error_messages={
            "required": "Pickup location is required.",
            "blank": "Pickup location cannot be blank.",
        },
        help_text="Pickup location address (e.g. 'Dallas, TX')",
    )
    dropoff_location = serializers.CharField(
        required=True,
        allow_blank=False,
        max_length=300,
        error_messages={
            "required": "Dropoff location is required.",
            "blank": "Dropoff location cannot be blank.",
        },
        help_text="Dropoff location address (e.g. 'Los Angeles, CA')",
    )
    cycle_used_hours = serializers.FloatField(
        required=False,
        default=0.0,
        min_value=0.0,
        max_value=70.0,
        error_messages={
            "min_value": "cycle_used_hours must be between 0 and 70.",
            "max_value": "cycle_used_hours must be between 0 and 70.",
            "invalid": "cycle_used_hours must be a valid number between 0 and 70.",
        },
        help_text="Initial consumed hours in 70h/8d cycle (default: 0.0)",
    )
    start_time = serializers.DateTimeField(
        required=False,
        allow_null=True,
        help_text="Optional simulation start timestamp (ISO 8601)",
    )
