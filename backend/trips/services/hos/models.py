"""Data models and data structures for HOS events, daily logs, and route objects."""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Dict, Optional, Any


class DutyStatus:
    OFF = "OFF"  # Off Duty
    SB = "SB"    # Sleeper Berth
    D = "D"      # Driving
    ON = "ON"    # On Duty Not Driving

    ALL = {OFF, SB, D, ON}


class ActivityType:
    DRIVING = "DRIVING"
    BREAK = "BREAK"
    REST = "REST"
    RESTART = "RESTART"
    FUEL = "FUEL"
    PICKUP = "PICKUP"
    DROPOFF = "DROPOFF"
    INITIAL_OFF_DUTY = "INITIAL_OFF_DUTY"


@dataclass
class HOSEvent:
    status: str  # OFF, SB, D, ON
    activity: str  # DRIVING, BREAK, REST, RESTART, FUEL, PICKUP, DROPOFF, etc.
    start_time: datetime
    end_time: datetime
    duration_hours: float
    id: str = ""  # e.g. "ev-1", "ev-2"
    start_mile: float = 0.0
    end_mile: float = 0.0
    location: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.id:
            self.id = f"ev-{self.status.lower()}-{int(self.start_time.timestamp())}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "status": self.status,
            "activity": self.activity,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "duration_hours": round(self.duration_hours, 2),
            "start_mile": round(self.start_mile, 1),
            "end_mile": round(self.end_mile, 1),
            "location": self.location,
            "metadata": self.metadata,
        }


@dataclass
class DailyTotals:
    driving_hours: float = 0.0
    on_duty_hours: float = 0.0
    sleeper_hours: float = 0.0
    off_duty_hours: float = 0.0
    total_hours: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "driving_hours": round(self.driving_hours, 2),
            "on_duty_hours": round(self.on_duty_hours, 2),
            "sleeper_hours": round(self.sleeper_hours, 2),
            "off_duty_hours": round(self.off_duty_hours, 2),
            "total_hours": round(self.total_hours, 2),
        }


@dataclass
class DailyLog:
    day: int
    date: str  # YYYY-MM-DD
    events: List[HOSEvent] = field(default_factory=list)
    totals: DailyTotals = field(default_factory=DailyTotals)
    cumulative_cycle_used: float = 0.0
    cycle_remaining: float = 70.0
    miles_today: float = 0.0
    total_miles_to_date: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "day": self.day,
            "date": self.date,
            "events": [event.to_dict() for event in self.events],
            "totals": self.totals.to_dict(),
            "cumulative_cycle_used": round(self.cumulative_cycle_used, 2),
            "cycle_remaining": round(self.cycle_remaining, 2),
            "miles_today": round(self.miles_today, 1),
            "total_miles_to_date": round(self.total_miles_to_date, 1),
        }


@dataclass
class HOSSummary:
    cycle_used_hours_initial: float
    cycle_hours_consumed_trip: float
    cycle_remaining_hours: float
    trip_days: int
    driving_hours: float
    on_duty_hours: float
    sleeper_hours: float
    off_duty_hours: float
    compliant: bool
    violations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cycle_used_hours_initial": round(self.cycle_used_hours_initial, 2),
            "cycle_hours_consumed_trip": round(self.cycle_hours_consumed_trip, 2),
            "cycle_remaining_hours": round(self.cycle_remaining_hours, 2),
            "trip_days": self.trip_days,
            "driving_hours": round(self.driving_hours, 2),
            "on_duty_hours": round(self.on_duty_hours, 2),
            "sleeper_hours": round(self.sleeper_hours, 2),
            "off_duty_hours": round(self.off_duty_hours, 2),
            "compliant": self.compliant,
            "violations": self.violations,
        }


@dataclass
class RouteLeg:
    origin_name: str
    destination_name: str
    distance_miles: float
    distance_km: float
    duration_hours: float
    duration_sec: float
    coordinates: List[List[float]] = field(default_factory=list)


@dataclass
class RouteResult:
    distance_km: float
    distance_miles: float
    duration_sec: float
    duration_hours: float
    coordinates: List[List[float]]
    stops: List[Dict[str, Any]]
    legs: List[RouteLeg] = field(default_factory=list)
