"""HOS Rules Configuration for Property-Carrying Commercial Motor Vehicles (49 CFR Part 395).

All constants are configurable parameters.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class HOSRules:
    """Configurable HOS Rule Set."""

    # 11-Hour Driving Limit (§ 395.3(a)(1))
    MAX_DRIVING_HOURS_PER_SHIFT: float = 11.0

    # 14-Hour Consecutive Duty Window (§ 395.3(a)(2))
    MAX_DUTY_WINDOW_HOURS: float = 14.0

    # 30-Minute Break Threshold (§ 395.3(a)(3)(ii))
    # Driving is prohibited if >= 8 cumulative driving hours have passed
    # without at least one 30-minute qualifying interruption.
    MANDATORY_BREAK_THRESHOLD_DRIVING_HOURS: float = 8.0

    # Qualifying Break Duration in hours (30 minutes = 0.5 hours)
    MANDATORY_BREAK_DURATION_HOURS: float = 0.5

    # 10 Consecutive Hours Daily Rest (§ 395.3(a)(1))
    DAILY_REST_HOURS: float = 10.0

    # 70-Hour / 8-Day Cycle Limit (§ 395.3(b)(2))
    MAX_CYCLE_HOURS: float = 70.0

    # 34-Hour Restart (§ 395.3(d))
    ALLOW_34_HOUR_RESTART: bool = True
    CYCLE_RESTART_HOURS: float = 34.0

    # Fuel Stop Interval & Duration (Assessment specification: every <= 1,000 miles)
    MAX_MILES_BETWEEN_FUEL: float = 1000.0
    FUELING_DURATION_HOURS: float = 0.5  # 30 minutes ON-duty (qualifies as break)

    # Pickup & Dropoff Durations
    PICKUP_DURATION_HOURS: float = 1.0  # 1 hour ON-duty (qualifies as break)
    DROPOFF_DURATION_HOURS: float = 1.0  # 1 hour ON-duty (qualifies as break)


# Default rules instance
DEFAULT_HOS_RULES = HOSRules()
