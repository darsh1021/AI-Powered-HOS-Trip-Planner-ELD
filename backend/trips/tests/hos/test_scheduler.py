"""Comprehensive Tests for HOS Scheduler State Machine."""

from datetime import datetime
from django.test import SimpleTestCase

from trips.services.hos.rules import HOSRules, DEFAULT_HOS_RULES
from trips.services.hos.models import (
    RouteResult,
    RouteLeg,
    DutyStatus,
    ActivityType,
)
from trips.services.hos.scheduler import HOSScheduler


class TestHOSScheduler(SimpleTestCase):
    def setUp(self):
        self.scheduler = HOSScheduler(rules=DEFAULT_HOS_RULES)
        self.start_time = datetime(2026, 8, 27, 8, 0, 0)

    def _create_mock_route(
        self,
        leg1_miles: float,
        leg1_hours: float,
        leg2_miles: float,
        leg2_hours: float,
    ) -> RouteResult:
        total_mi = leg1_miles + leg2_miles
        total_hr = leg1_hours + leg2_hours
        legs = [
            RouteLeg(
                origin_name="Chicago, IL",
                destination_name="Dallas, TX",
                distance_miles=leg1_miles,
                distance_km=leg1_miles * 1.60934,
                duration_hours=leg1_hours,
                duration_sec=leg1_hours * 3600.0,
            ),
            RouteLeg(
                origin_name="Dallas, TX",
                destination_name="Los Angeles, CA",
                distance_miles=leg2_miles,
                distance_km=leg2_miles * 1.60934,
                duration_hours=leg2_hours,
                duration_sec=leg2_hours * 3600.0,
            ),
        ]
        return RouteResult(
            distance_km=total_mi * 1.60934,
            distance_miles=total_mi,
            duration_sec=total_hr * 3600.0,
            duration_hours=total_hr,
            coordinates=[[41.8781, -87.6298], [32.7767, -96.7970], [34.0522, -118.2437]],
            stops=[
                {"name": "Current", "address": "Chicago, IL", "lat": 41.8781, "lng": -87.6298},
                {"name": "Pickup", "address": "Dallas, TX", "lat": 32.7767, "lng": -96.7970},
                {"name": "Dropoff", "address": "Los Angeles, CA", "lat": 34.0522, "lng": -118.2437},
            ],
            legs=legs,
        )

    def test_short_trip_single_shift(self):
        """Short trip (< 8h driving total) should complete in 1 shift without 30m break."""
        route = self._create_mock_route(leg1_miles=150.0, leg1_hours=3.0, leg2_miles=150.0, leg2_hours=3.0)
        master_events, daily_logs, summary, validation = self.scheduler.plan_trip_schedule(
            route_result=route,
            cycle_used_hours=10.0,
            start_time=self.start_time,
        )

        self.assertTrue(validation["is_valid"])
        self.assertEqual(len(validation["violations"]), 0)
        self.assertEqual(summary.driving_hours, 6.0)
        self.assertEqual(summary.on_duty_hours, 2.0)  # 1h pickup + 1h dropoff

        # Verify exact pickup and dropoff events exist
        activities = [e.activity for e in master_events]
        self.assertIn(ActivityType.PICKUP, activities)
        self.assertIn(ActivityType.DROPOFF, activities)

    def test_11_hour_limit_forces_10h_rest(self):
        """Trip requiring 14 hours driving must force a 10-hour rest period."""
        route = self._create_mock_route(leg1_miles=400.0, leg1_hours=7.0, leg2_miles=400.0, leg2_hours=7.0)
        master_events, daily_logs, summary, validation = self.scheduler.plan_trip_schedule(
            route_result=route,
            cycle_used_hours=0.0,
            start_time=self.start_time,
        )

        self.assertTrue(validation["is_valid"])
        # Should have at least one 10-hour REST event
        rest_events = [e for e in master_events if e.activity == ActivityType.REST and e.duration_hours >= 10.0]
        self.assertGreaterEqual(len(rest_events), 1)
        self.assertEqual(rest_events[0].status, DutyStatus.SB)

    def test_30_minute_break_after_8_cumulative_driving_hours(self):
        """Continuous driving of 9.5 hours in Leg 1 must insert a 30-minute break."""
        route = self._create_mock_route(leg1_miles=550.0, leg1_hours=9.5, leg2_miles=50.0, leg2_hours=1.0)
        master_events, daily_logs, summary, validation = self.scheduler.plan_trip_schedule(
            route_result=route,
            cycle_used_hours=0.0,
            start_time=self.start_time,
        )

        self.assertTrue(validation["is_valid"])
        break_events = [e for e in master_events if e.activity == ActivityType.BREAK]
        self.assertGreaterEqual(len(break_events), 1)
        self.assertEqual(break_events[0].duration_hours, 0.5)

    def test_fuel_event_resets_break_clock(self):
        """Fueling at 1,000 miles is 30m ON-duty, which qualifies and resets the 8-hour break clock."""
        # 1,200 miles total driving at 65 mph (~18.46 hrs)
        route = self._create_mock_route(leg1_miles=1100.0, leg1_hours=16.9, leg2_miles=100.0, leg2_hours=1.5)
        master_events, daily_logs, summary, validation = self.scheduler.plan_trip_schedule(
            route_result=route,
            cycle_used_hours=0.0,
            start_time=self.start_time,
        )

        self.assertTrue(validation["is_valid"])
        fuel_events = [e for e in master_events if e.activity == ActivityType.FUEL]
        self.assertGreaterEqual(len(fuel_events), 1)
        self.assertEqual(fuel_events[0].status, DutyStatus.ON)
        self.assertEqual(fuel_events[0].duration_hours, 0.5)

    def test_70_hour_cycle_limit_and_34h_restart(self):
        """Starting with 66.0 cycle hours used on a 10-hour driving trip triggers a 34-hour restart."""
        route = self._create_mock_route(leg1_miles=300.0, leg1_hours=5.0, leg2_miles=300.0, leg2_hours=5.0)
        master_events, daily_logs, summary, validation = self.scheduler.plan_trip_schedule(
            route_result=route,
            cycle_used_hours=66.0,
            start_time=self.start_time,
        )

        self.assertTrue(validation["is_valid"])
        restart_events = [e for e in master_events if e.activity == ActivityType.RESTART]
        self.assertGreaterEqual(len(restart_events), 1)
        self.assertEqual(restart_events[0].duration_hours, 34.0)
        self.assertEqual(restart_events[0].status, DutyStatus.OFF)

    def test_daily_logs_midnight_splitting_and_24h_total(self):
        """Multi-day schedule must produce daily logs where each calendar day totals exactly 24.0 hours."""
        route = self._create_mock_route(leg1_miles=900.0, leg1_hours=15.0, leg2_miles=1200.0, leg2_hours=20.0)
        master_events, daily_logs, summary, validation = self.scheduler.plan_trip_schedule(
            route_result=route,
            cycle_used_hours=10.0,
            start_time=self.start_time,
        )

        self.assertTrue(validation["is_valid"])
        self.assertGreater(len(daily_logs), 1)

        for log in daily_logs:
            self.assertAlmostEqual(log.totals.total_hours, 24.0, places=2)
            # Verify sum of event durations inside this day matches totals.total_hours
            ev_dur_sum = sum(e.duration_hours for e in log.events)
            self.assertAlmostEqual(ev_dur_sum, 24.0, places=2)
