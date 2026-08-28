"""Independent HOS Compliance Validator (49 CFR Part 395).

Validates generated master timeline events and daily logs against all FMCSA rules.
Decoupled from scheduler internals; accepts only (events, rules, initial_cycle_used).
"""

from datetime import datetime, timedelta
from typing import List, Tuple, Dict, Any, Optional

from .models import HOSEvent, DailyLog, DutyStatus, ActivityType
from .rules import HOSRules, DEFAULT_HOS_RULES


class HOSValidator:
    """Independent validator checking FMCSA compliance and timeline integrity."""

    def __init__(self, rules: HOSRules = DEFAULT_HOS_RULES):
        self.rules = rules

    def validate_schedule(
        self,
        master_events: List[HOSEvent],
        initial_cycle_used: float = 0.0,
        daily_logs: Optional[List[DailyLog]] = None,
    ) -> Tuple[bool, List[str]]:
        """Run all validation checks over master events.

        Returns (is_valid, list_of_violations).
        """
        violations: List[str] = []

        if not master_events:
            violations.append("Empty master events schedule.")
            return False, violations

        # 1. Timeline Continuity & Status Schema Check
        self._check_timeline_continuity_and_schema(master_events, violations)

        # 2. Shift Constraints (11h Driving, 14h Duty Window, 10h Rest)
        self._check_shift_limits(master_events, violations)

        # 3. 30-Minute Break Rule Check
        self._check_30_min_break_rule(master_events, violations)

        # 4. Fuel Interval Check (<= 1,000 miles)
        self._check_fuel_intervals(master_events, violations)

        # 5. Pickup & Dropoff Requirements
        self._check_pickup_dropoff(master_events, violations)

        # 6. 70-Hour Cycle Ceiling Check
        self._check_70_hour_cycle(master_events, initial_cycle_used, violations)

        # 7. Daily Logs 24.0h Consistency Check (if provided)
        if daily_logs:
            self._check_daily_logs_totals(daily_logs, violations)

        is_valid = len(violations) == 0
        return is_valid, violations

    def _check_timeline_continuity_and_schema(
        self, events: List[HOSEvent], violations: List[str]
    ) -> None:
        """Verify that every event has a valid status and events are strictly contiguous."""
        for idx, ev in enumerate(events):
            if ev.status not in DutyStatus.ALL:
                violations.append(
                    f"Event {idx} ('{ev.activity}') has invalid status '{ev.status}'. Must be one of {DutyStatus.ALL}."
                )

            if ev.end_time <= ev.start_time:
                violations.append(
                    f"Event {idx} ('{ev.activity}') has invalid duration: start {ev.start_time} >= end {ev.end_time}."
                )

            if idx > 0:
                prev_ev = events[idx - 1]
                gap_sec = (ev.start_time - prev_ev.end_time).total_seconds()
                if abs(gap_sec) > 1.0:  # more than 1 second discrepancy
                    if gap_sec > 0:
                        violations.append(
                            f"Timeline gap detected between event {idx-1} (ended {prev_ev.end_time}) and event {idx} (started {ev.start_time}). Gap = {gap_sec}s."
                        )
                    else:
                        violations.append(
                            f"Timeline overlap detected between event {idx-1} (ended {prev_ev.end_time}) and event {idx} (started {ev.start_time}). Overlap = {abs(gap_sec)}s."
                        )

    def _check_shift_limits(
        self, events: List[HOSEvent], violations: List[str]
    ) -> None:
        """Verify 11-hour driving limit and 14-hour duty window between qualifying 10h rest periods."""
        shift_start_time: Optional[datetime] = None
        driving_in_shift = 0.0
        consecutive_rest_hours = 0.0

        for idx, ev in enumerate(events):
            # Check if this is off-duty/sleeper rest
            if ev.status in (DutyStatus.OFF, DutyStatus.SB):
                consecutive_rest_hours += ev.duration_hours
            else:
                # Coming on duty or driving
                if consecutive_rest_hours >= self.rules.DAILY_REST_HOURS:
                    # Previous shift was properly reset by >= 10h rest
                    shift_start_time = None
                    driving_in_shift = 0.0
                consecutive_rest_hours = 0.0

            # If driving or on-duty and shift has not started, start shift window
            if ev.status in (DutyStatus.D, DutyStatus.ON) and shift_start_time is None:
                shift_start_time = ev.start_time
                driving_in_shift = 0.0

            if ev.status == DutyStatus.D:
                driving_in_shift += ev.duration_hours

                # 11-Hour Driving Limit
                if driving_in_shift > (self.rules.MAX_DRIVING_HOURS_PER_SHIFT + 0.01):
                    violations.append(
                        f"11-Hour Driving Rule Violation at event {idx} ({ev.start_time.isoformat()}): Shift driving reached {driving_in_shift:.2f}h (Limit: {self.rules.MAX_DRIVING_HOURS_PER_SHIFT}h)."
                    )

                # 14-Hour Consecutive Duty Window Limit
                if shift_start_time is not None:
                    window_elapsed = (ev.end_time - shift_start_time).total_seconds() / 3600.0
                    if window_elapsed > (self.rules.MAX_DUTY_WINDOW_HOURS + 0.01):
                        violations.append(
                            f"14-Hour Duty Window Violation at event {idx} ({ev.start_time.isoformat()}): Driving occurred at window hour {window_elapsed:.2f}h from shift start {shift_start_time.isoformat()} (Limit: {self.rules.MAX_DUTY_WINDOW_HOURS}h)."
                        )

    def _check_30_min_break_rule(
        self, events: List[HOSEvent], violations: List[str]
    ) -> None:
        """Verify that driving does not occur after >8.0 cumulative driving hours without >=30m interruption."""
        driving_since_break = 0.0
        consecutive_non_driving = 0.0

        for idx, ev in enumerate(events):
            if ev.status != DutyStatus.D:
                # Non-driving event (OFF, SB, ON)
                consecutive_non_driving += ev.duration_hours
                if consecutive_non_driving >= (self.rules.MANDATORY_BREAK_DURATION_HOURS - 1e-4):
                    # Qualifying >= 30-min break achieved!
                    driving_since_break = 0.0
            else:
                # Driving event
                consecutive_non_driving = 0.0
                if driving_since_break > (self.rules.MANDATORY_BREAK_THRESHOLD_DRIVING_HOURS + 0.01):
                    violations.append(
                        f"30-Minute Break Rule Violation at event {idx} ({ev.start_time.isoformat()}): Driving exceeded 8 hours ({driving_since_break:.2f}h) without a qualifying 30m break."
                    )
                driving_since_break += ev.duration_hours
                if driving_since_break > (self.rules.MANDATORY_BREAK_THRESHOLD_DRIVING_HOURS + 0.01):
                    violations.append(
                        f"30-Minute Break Rule Violation at event {idx} ({ev.end_time.isoformat()}): Driving reached {driving_since_break:.2f}h without a qualifying 30m break."
                    )

    def _check_fuel_intervals(
        self, events: List[HOSEvent], violations: List[str]
    ) -> None:
        """Verify that driving distance between fuel events never exceeds 1,000 miles."""
        last_fuel_mile = 0.0

        for idx, ev in enumerate(events):
            if ev.activity == ActivityType.FUEL:
                last_fuel_mile = ev.start_mile

            if ev.status == DutyStatus.D:
                miles_driven = ev.end_mile - last_fuel_mile
                if miles_driven > (self.rules.MAX_MILES_BETWEEN_FUEL + 1.0):
                    violations.append(
                        f"Fuel Interval Violation at event {idx} ({ev.start_time.isoformat()}): Miles since fuel reached {miles_driven:.1f} mi (Limit: {self.rules.MAX_MILES_BETWEEN_FUEL} mi)."
                    )

    def _check_pickup_dropoff(
        self, events: List[HOSEvent], violations: List[str]
    ) -> None:
        """Verify Pickup and Dropoff events are ON duty and at least 1.0 hour."""
        for idx, ev in enumerate(events):
            if ev.activity == ActivityType.PICKUP:
                if ev.status != DutyStatus.ON:
                    violations.append(f"Pickup event {idx} must have status 'ON', got '{ev.status}'.")
                if ev.duration_hours < (self.rules.PICKUP_DURATION_HOURS - 1e-4):
                    violations.append(
                        f"Pickup event {idx} duration is {ev.duration_hours:.2f}h (expected >= {self.rules.PICKUP_DURATION_HOURS}h)."
                    )
            elif ev.activity == ActivityType.DROPOFF:
                if ev.status != DutyStatus.ON:
                    violations.append(f"Dropoff event {idx} must have status 'ON', got '{ev.status}'.")
                if ev.duration_hours < (self.rules.DROPOFF_DURATION_HOURS - 1e-4):
                    violations.append(
                        f"Dropoff event {idx} duration is {ev.duration_hours:.2f}h (expected >= {self.rules.DROPOFF_DURATION_HOURS}h)."
                    )

    def _check_70_hour_cycle(
        self, events: List[HOSEvent], initial_cycle_used: float, violations: List[str]
    ) -> None:
        """Verify total on-duty (D + ON) hours does not exceed 70.0 hours without a 34h restart."""
        cycle_used = initial_cycle_used
        consecutive_off = 0.0

        for idx, ev in enumerate(events):
            if ev.status in (DutyStatus.OFF, DutyStatus.SB):
                consecutive_off += ev.duration_hours
                if consecutive_off >= self.rules.CYCLE_RESTART_HOURS:
                    # 34-hour restart achieved
                    cycle_used = 0.0
            else:
                consecutive_off = 0.0
                cycle_used += ev.duration_hours
                if cycle_used > (self.rules.MAX_CYCLE_HOURS + 0.01):
                    violations.append(
                        f"70-Hour Cycle Rule Violation at event {idx} ({ev.start_time.isoformat()}): Cumulative cycle on-duty time reached {cycle_used:.2f}h (Limit: {self.rules.MAX_CYCLE_HOURS}h)."
                    )

    def _check_daily_logs_totals(
        self, daily_logs: List[DailyLog], violations: List[str]
    ) -> None:
        """Verify that every daily log totals exactly 24.0 hours."""
        for log in daily_logs:
            tot = log.totals.total_hours
            if abs(tot - 24.0) > 0.01:
                violations.append(
                    f"Daily Log Day {log.day} ({log.date}) total status hours = {tot:.2f}h (Must equal exactly 24.0h)."
                )
