"""Tests for HOS Rules Configuration."""

from django.test import SimpleTestCase
from trips.services.hos.rules import HOSRules, DEFAULT_HOS_RULES


class TestHOSRules(SimpleTestCase):
    def test_default_rules_constants(self):
        rules = DEFAULT_HOS_RULES
        self.assertEqual(rules.MAX_DRIVING_HOURS_PER_SHIFT, 11.0)
        self.assertEqual(rules.MAX_DUTY_WINDOW_HOURS, 14.0)
        self.assertEqual(rules.MANDATORY_BREAK_THRESHOLD_DRIVING_HOURS, 8.0)
        self.assertEqual(rules.MANDATORY_BREAK_DURATION_HOURS, 0.5)
        self.assertEqual(rules.DAILY_REST_HOURS, 10.0)
        self.assertEqual(rules.MAX_CYCLE_HOURS, 70.0)
        self.assertEqual(rules.CYCLE_RESTART_HOURS, 34.0)
        self.assertTrue(rules.ALLOW_34_HOUR_RESTART)
        self.assertEqual(rules.MAX_MILES_BETWEEN_FUEL, 1000.0)
        self.assertEqual(rules.FUELING_DURATION_HOURS, 0.5)
        self.assertEqual(rules.PICKUP_DURATION_HOURS, 1.0)
        self.assertEqual(rules.DROPOFF_DURATION_HOURS, 1.0)

    def test_custom_rule_overrides(self):
        custom = HOSRules(MAX_DRIVING_HOURS_PER_SHIFT=10.0, ALLOW_34_HOUR_RESTART=False)
        self.assertEqual(custom.MAX_DRIVING_HOURS_PER_SHIFT, 10.0)
        self.assertFalse(custom.ALLOW_34_HOUR_RESTART)
        self.assertEqual(custom.DAILY_REST_HOURS, 10.0)
