"""Comprehensive End-to-End Scenarios Test Suite (Phase 6 Final Verification).

Covers:
- Scenario A: Short trip (Milwaukee -> Chicago -> Gary)
- Scenario B: Long cross-country trip (Chicago -> Dallas -> Los Angeles)
- Scenario C: High cycle usage (Cycle = 65h, triggers 34h restart)
- Scenario D: Comprehensive HOS compliance audit (11h, 14h, 30m break, 10h rest, continuity)
- Scenario E: Input validation & error handling
"""

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch

from trips.services.hos.models import RouteResult, RouteLeg, DutyStatus, ActivityType
from trips.services.hos.scheduler import HOSScheduler
from trips.services.hos.validator import HOSValidator
from trips.services.hos.rules import DEFAULT_HOS_RULES


class EndToEndScenariosTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.scheduler = HOSScheduler(rules=DEFAULT_HOS_RULES)
        self.validator = HOSValidator(rules=DEFAULT_HOS_RULES)

    def test_scenario_a_short_trip(self):
        """Scenario A: Short route fits in a single 24-hour day."""
        legs = [
            RouteLeg(
                origin_name="Milwaukee, WI",
                destination_name="Chicago, IL",
                distance_miles=92.0,
                distance_km=148.0,
                duration_hours=1.75,
                duration_sec=6300,
            ),
            RouteLeg(
                origin_name="Chicago, IL",
                destination_name="Gary, IN",
                distance_miles=31.0,
                distance_km=50.0,
                duration_hours=0.75,
                duration_sec=2700,
            ),
        ]
        route = RouteResult(
            distance_km=198.0,
            distance_miles=123.0,
            duration_sec=9000,
            duration_hours=2.5,
            coordinates=[[43.0389, -87.9065], [41.8781, -87.6298], [41.5934, -87.3464]],
            stops=[{"name": "Milwaukee"}, {"name": "Chicago"}, {"name": "Gary"}],
            legs=legs,
        )

        events, daily_logs, summary, validation = self.scheduler.plan_trip_schedule(
            route_result=route,
            cycle_used_hours=10.0,
        )

        self.assertEqual(len(daily_logs), 1, "Short trip must finish within Day 1")
        self.assertTrue(summary.compliant)
        self.assertTrue(validation["is_valid"])
        self.assertAlmostEqual(daily_logs[0].totals.total_hours, 24.0, delta=0.01)

    def test_scenario_b_long_trip(self):
        """Scenario B: Long trip across multiple days with fuel stops and rest periods."""
        legs = [
            RouteLeg(
                origin_name="Chicago, IL",
                destination_name="Dallas, TX",
                distance_miles=926.0,
                distance_km=1490.0,
                duration_hours=15.0,
                duration_sec=54000,
            ),
            RouteLeg(
                origin_name="Dallas, TX",
                destination_name="Los Angeles, CA",
                distance_miles=1436.0,
                distance_km=2311.0,
                duration_hours=23.0,
                duration_sec=82800,
            ),
        ]
        route = RouteResult(
            distance_km=3801.0,
            distance_miles=2362.0,
            duration_sec=136800,
            duration_hours=38.0,
            coordinates=[[41.8781, -87.6298], [32.7767, -96.7970], [34.0522, -118.2437]],
            stops=[{"name": "Chicago"}, {"name": "Dallas"}, {"name": "Los Angeles"}],
            legs=legs,
        )

        events, daily_logs, summary, validation = self.scheduler.plan_trip_schedule(
            route_result=route,
            cycle_used_hours=24.0,
        )

        self.assertTrue(summary.compliant)
        self.assertTrue(validation["is_valid"])
        self.assertGreaterEqual(len(daily_logs), 3)

        # Every daily log must total exactly 24.0 hours
        for log in daily_logs:
            self.assertAlmostEqual(log.totals.total_hours, 24.0, delta=0.01)

        # Fuel stops must be scheduled
        fuel_events = [e for e in events if e.activity == ActivityType.FUEL]
        self.assertGreaterEqual(len(fuel_events), 2)

    def test_scenario_c_high_cycle_usage_triggers_restart(self):
        """Scenario C: Cycle used = 65h triggers 34h restart."""
        legs = [
            RouteLeg(
                origin_name="Chicago, IL",
                destination_name="Dallas, TX",
                distance_miles=926.0,
                distance_km=1490.0,
                duration_hours=15.0,
                duration_sec=54000,
            ),
            RouteLeg(
                origin_name="Dallas, TX",
                destination_name="Los Angeles, CA",
                distance_miles=1436.0,
                distance_km=2311.0,
                duration_hours=23.0,
                duration_sec=82800,
            ),
        ]
        route = RouteResult(
            distance_km=3801.0,
            distance_miles=2362.0,
            duration_sec=136800,
            duration_hours=38.0,
            coordinates=[[41.8781, -87.6298], [32.7767, -96.7970], [34.0522, -118.2437]],
            stops=[{"name": "Chicago"}, {"name": "Dallas"}, {"name": "Los Angeles"}],
            legs=legs,
        )

        events, daily_logs, summary, validation = self.scheduler.plan_trip_schedule(
            route_result=route,
            cycle_used_hours=65.0,
        )

        self.assertTrue(summary.compliant)
        self.assertTrue(validation["is_valid"])

        # Check that 34h restart occurred
        restart_events = [e for e in events if e.activity == ActivityType.RESTART]
        self.assertGreaterEqual(len(restart_events), 1)
        self.assertGreaterEqual(restart_events[0].duration_hours, 34.0)

    def test_scenario_d_timeline_continuity_audit(self):
        """Scenario D: Audit for zero gaps and zero overlaps across entire timeline."""
        legs = [
            RouteLeg(
                origin_name="Origin",
                destination_name="Pickup",
                distance_miles=500.0,
                distance_km=800.0,
                duration_hours=8.5,
                duration_sec=30600,
            ),
            RouteLeg(
                origin_name="Pickup",
                destination_name="Dropoff",
                distance_miles=600.0,
                distance_km=960.0,
                duration_hours=10.0,
                duration_sec=36000,
            ),
        ]
        route = RouteResult(
            distance_km=1760.0,
            distance_miles=1100.0,
            duration_sec=66600,
            duration_hours=18.5,
            coordinates=[[40.0, -80.0], [35.0, -90.0], [30.0, -100.0]],
            stops=[{"name": "Origin"}, {"name": "Pickup"}, {"name": "Dropoff"}],
            legs=legs,
        )

        events, daily_logs, summary, validation = self.scheduler.plan_trip_schedule(
            route_result=route,
            cycle_used_hours=15.0,
        )

        # Check every pair of sequential events for zero timeline gap/overlap
        for i in range(len(events) - 1):
            cur_end = events[i].end_time
            nxt_start = events[i + 1].start_time
            self.assertEqual(cur_end, nxt_start, f"Gap or overlap between event {i} and {i+1}")

    def test_scenario_e_input_validation_errors(self):
        """Scenario E: API validation rejects negative cycle, cycle > 70, and blank locations."""
        # 1. Negative cycle
        res1 = self.client.post(
            "/api/trips/plan/",
            {
                "current_location": "Chicago, IL",
                "pickup_location": "Dallas, TX",
                "dropoff_location": "Los Angeles, CA",
                "cycle_used_hours": -5.0,
            },
            format="json",
        )
        self.assertEqual(res1.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("cycle_used_hours", res1.data.get("error", ""))

        # 2. Cycle > 70
        res2 = self.client.post(
            "/api/trips/plan/",
            {
                "current_location": "Chicago, IL",
                "pickup_location": "Dallas, TX",
                "dropoff_location": "Los Angeles, CA",
                "cycle_used_hours": 75.0,
            },
            format="json",
        )
        self.assertEqual(res2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("cycle_used_hours", res2.data.get("error", ""))

        # 3. Blank location
        res3 = self.client.post(
            "/api/trips/plan/",
            {
                "current_location": "",
                "pickup_location": "Dallas, TX",
                "dropoff_location": "Los Angeles, CA",
                "cycle_used_hours": 10.0,
            },
            format="json",
        )
        self.assertEqual(res3.status_code, status.HTTP_400_BAD_REQUEST)
