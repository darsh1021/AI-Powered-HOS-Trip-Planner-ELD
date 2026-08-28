"""Tests for Independent HOS Validator."""

from datetime import datetime, timedelta
from django.test import SimpleTestCase

from trips.services.hos.rules import DEFAULT_HOS_RULES
from trips.services.hos.models import HOSEvent, DutyStatus, ActivityType
from trips.services.hos.validator import HOSValidator


class TestHOSValidator(SimpleTestCase):
    def setUp(self):
        self.validator = HOSValidator(rules=DEFAULT_HOS_RULES)
        self.base_time = datetime(2026, 8, 27, 8, 0, 0)

    def test_valid_schedule_passes(self):
        t0 = self.base_time
        t1 = t0 + timedelta(hours=4.0)
        t2 = t1 + timedelta(hours=1.0)
        t3 = t2 + timedelta(hours=4.0)

        events = [
            HOSEvent(status=DutyStatus.D, activity=ActivityType.DRIVING, start_time=t0, end_time=t1, duration_hours=4.0, start_mile=0, end_mile=200),
            HOSEvent(status=DutyStatus.ON, activity=ActivityType.PICKUP, start_time=t1, end_time=t2, duration_hours=1.0, start_mile=200, end_mile=200),
            HOSEvent(status=DutyStatus.D, activity=ActivityType.DRIVING, start_time=t2, end_time=t3, duration_hours=4.0, start_mile=200, end_mile=400),
        ]

        is_valid, violations = self.validator.validate_schedule(events, initial_cycle_used=10.0)
        self.assertTrue(is_valid)
        self.assertEqual(len(violations), 0)

    def test_11_hour_driving_violation_caught(self):
        """12 consecutive hours of driving in a single shift must be flagged."""
        t0 = self.base_time
        t1 = t0 + timedelta(hours=12.0)

        events = [
            HOSEvent(status=DutyStatus.D, activity=ActivityType.DRIVING, start_time=t0, end_time=t1, duration_hours=12.0, start_mile=0, end_mile=600),
        ]

        is_valid, violations = self.validator.validate_schedule(events, initial_cycle_used=0.0)
        self.assertFalse(is_valid)
        self.assertTrue(any("11-Hour Driving Rule Violation" in v for v in violations))

    def test_14_hour_window_violation_caught(self):
        """Driving at hour 15 from shift start must be flagged."""
        t0 = self.base_time
        t1 = t0 + timedelta(hours=5.0)   # 5h driving
        t2 = t1 + timedelta(hours=8.0)   # 8h off (not 10h rest, so window didn't reset)
        t3 = t2 + timedelta(hours=3.0)   # 3h driving -> ends at hour 16 from shift start!

        events = [
            HOSEvent(status=DutyStatus.D, activity=ActivityType.DRIVING, start_time=t0, end_time=t1, duration_hours=5.0, start_mile=0, end_mile=250),
            HOSEvent(status=DutyStatus.OFF, activity=ActivityType.BREAK, start_time=t1, end_time=t2, duration_hours=8.0, start_mile=250, end_mile=250),
            HOSEvent(status=DutyStatus.D, activity=ActivityType.DRIVING, start_time=t2, end_time=t3, duration_hours=3.0, start_mile=250, end_mile=400),
        ]

        is_valid, violations = self.validator.validate_schedule(events, initial_cycle_used=0.0)
        self.assertFalse(is_valid)
        self.assertTrue(any("14-Hour Duty Window Violation" in v for v in violations))

    def test_30_min_break_violation_caught(self):
        """9 continuous hours of driving without any 30m break must be flagged."""
        t0 = self.base_time
        t1 = t0 + timedelta(hours=9.0)

        events = [
            HOSEvent(status=DutyStatus.D, activity=ActivityType.DRIVING, start_time=t0, end_time=t1, duration_hours=9.0, start_mile=0, end_mile=450),
        ]

        is_valid, violations = self.validator.validate_schedule(events, initial_cycle_used=0.0)
        self.assertFalse(is_valid)
        self.assertTrue(any("30-Minute Break Rule Violation" in v for v in violations))

    def test_timeline_gap_caught(self):
        """A 15-minute gap between Event 1 end and Event 2 start must be flagged."""
        t0 = self.base_time
        t1 = t0 + timedelta(hours=2.0)
        t2 = t1 + timedelta(minutes=15)  # 15 min gap
        t3 = t2 + timedelta(hours=2.0)

        events = [
            HOSEvent(status=DutyStatus.D, activity=ActivityType.DRIVING, start_time=t0, end_time=t1, duration_hours=2.0),
            HOSEvent(status=DutyStatus.D, activity=ActivityType.DRIVING, start_time=t2, end_time=t3, duration_hours=2.0),
        ]

        is_valid, violations = self.validator.validate_schedule(events)
        self.assertFalse(is_valid)
        self.assertTrue(any("Timeline gap detected" in v for v in violations))

    def test_fuel_interval_violation_caught(self):
        """Driving 1,100 miles without a fuel event must be flagged."""
        t0 = self.base_time
        t1 = t0 + timedelta(hours=4.0)

        events = [
            HOSEvent(status=DutyStatus.D, activity=ActivityType.DRIVING, start_time=t0, end_time=t1, duration_hours=4.0, start_mile=0, end_mile=1100.0),
        ]

        is_valid, violations = self.validator.validate_schedule(events)
        self.assertFalse(is_valid)
        self.assertTrue(any("Fuel Interval Violation" in v for v in violations))

    def test_invalid_duty_status_caught(self):
        """Invalid duty status like 'INVALID_STATUS' must be flagged."""
        t0 = self.base_time
        t1 = t0 + timedelta(hours=1.0)

        events = [
            HOSEvent(status="UNKNOWN", activity=ActivityType.DRIVING, start_time=t0, end_time=t1, duration_hours=1.0),
        ]

        is_valid, violations = self.validator.validate_schedule(events)
        self.assertFalse(is_valid)
        self.assertTrue(any("invalid status" in v for v in violations))
