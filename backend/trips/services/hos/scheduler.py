"""HOS Deterministic State Machine Scheduler (49 CFR Part 395).

Generates a continuous master timeline of compliant HOSEvent objects from route legs
and initial cycle hours, then splits them into 24-hour DailyLogs.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional, Tuple, Dict, Any

from .models import (
    DutyStatus,
    ActivityType,
    HOSEvent,
    DailyLog,
    HOSSummary,
    RouteResult,
    RouteLeg,
)
from .rules import HOSRules, DEFAULT_HOS_RULES
from .calculator import split_events_by_calendar_day, calculate_daily_totals
from .validator import HOSValidator


@dataclass
class HOSState:
    """Streamlined scheduler simulation state."""

    current_time: datetime
    shift_start_time: Optional[datetime] = None
    driving_hours_in_shift: float = 0.0
    driving_hours_since_break: float = 0.0
    cycle_hours_used: float = 0.0
    miles_since_fuel: float = 0.0
    current_mile: float = 0.0
    consecutive_rest_hours: float = 0.0

    def shift_window_elapsed(self) -> float:
        if self.shift_start_time is None:
            return 0.0
        return (self.current_time - self.shift_start_time).total_seconds() / 3600.0

    def shift_window_remaining(self, max_window: float) -> float:
        if self.shift_start_time is None:
            return max_window
        return max(0.0, max_window - self.shift_window_elapsed())

    def driving_shift_remaining(self, max_driving: float) -> float:
        return max(0.0, max_driving - self.driving_hours_in_shift)

    def break_driving_remaining(self, max_until_break: float) -> float:
        return max(0.0, max_until_break - self.driving_hours_since_break)

    def fuel_miles_remaining(self, max_fuel_interval: float) -> float:
        return max(0.0, max_fuel_interval - self.miles_since_fuel)

    def cycle_remaining(self, max_cycle: float) -> float:
        return max(0.0, max_cycle - self.cycle_hours_used)


class HOSScheduler:
    """Deterministic scheduler for commercial motor vehicle property carriers."""

    def __init__(self, rules: HOSRules = DEFAULT_HOS_RULES):
        self.rules = rules
        self.validator = HOSValidator(rules=rules)

    def plan_trip_schedule(
        self,
        route_result: RouteResult,
        cycle_used_hours: float = 0.0,
        start_time: Optional[datetime] = None,
    ) -> Tuple[List[HOSEvent], List[DailyLog], HOSSummary, Dict[str, Any]]:
        """Main entry point: Generate master timeline, daily logs, summary, and validation."""
        if start_time is None:
            # Default to today at 08:00:00 AM UTC
            now = datetime.utcnow()
            start_time = datetime(now.year, now.month, now.day, 8, 0, 0)

        state = HOSState(
            current_time=start_time,
            cycle_hours_used=cycle_used_hours,
        )

        master_events: List[HOSEvent] = []

        stops = route_result.stops
        origin_name = (stops[0].get("address") or stops[0].get("name", "Origin")) if stops else "Origin"
        pickup_name = (stops[1].get("address") or stops[1].get("name", "Pickup Location")) if len(stops) > 1 else "Pickup Location"
        dropoff_name = (stops[2].get("address") or stops[2].get("name", "Dropoff Destination")) if len(stops) > 2 else "Dropoff Destination"

        # If route legs were not explicitly built, divide overall route into 2 logical legs
        legs = route_result.legs
        if not legs:
            total_dist_mi = route_result.distance_miles
            total_dur_hr = route_result.duration_hours
            # Approximate 40% Leg 1, 60% Leg 2 if intermediate not provided
            leg1_mi = total_dist_mi * 0.4
            leg1_dur = total_dur_hr * 0.4
            leg2_mi = total_dist_mi - leg1_mi
            leg2_dur = total_dur_hr - leg1_dur

            legs = [
                RouteLeg(
                    origin_name=origin_name,
                    destination_name=pickup_name,
                    distance_miles=leg1_mi,
                    distance_km=leg1_mi * 1.60934,
                    duration_hours=leg1_dur,
                    duration_sec=leg1_dur * 3600.0,
                ),
                RouteLeg(
                    origin_name=pickup_name,
                    destination_name=dropoff_name,
                    distance_miles=leg2_mi,
                    distance_km=leg2_mi * 1.60934,
                    duration_hours=leg2_dur,
                    duration_sec=leg2_dur * 3600.0,
                ),
            ]

        # -------------------------------------------------------------
        # STEP 1: Execute Leg 1 (Origin -> Pickup)
        # -------------------------------------------------------------
        self._schedule_driving_leg(legs[0], state, master_events, destination_name=pickup_name)

        # -------------------------------------------------------------
        # STEP 2: Execute Pickup Event (1.0 hour ON duty)
        # -------------------------------------------------------------
        self._schedule_on_duty_event(
            state=state,
            master_events=master_events,
            activity=ActivityType.PICKUP,
            duration=self.rules.PICKUP_DURATION_HOURS,
            location=pickup_name,
        )

        # If 14-hour window or 11-hour driving was reached during/after pickup, take 10h rest
        if (
            state.shift_window_remaining(self.rules.MAX_DUTY_WINDOW_HOURS) <= 1e-4
            or state.driving_shift_remaining(self.rules.MAX_DRIVING_HOURS_PER_SHIFT) <= 1e-4
        ):
            self._schedule_rest(state, master_events, duration=self.rules.DAILY_REST_HOURS, location=pickup_name)

        # -------------------------------------------------------------
        # STEP 3: Execute Leg 2 (Pickup -> Dropoff)
        # -------------------------------------------------------------
        self._schedule_driving_leg(legs[1], state, master_events, destination_name=dropoff_name)

        # -------------------------------------------------------------
        # STEP 4: Execute Dropoff Event (1.0 hour ON duty)
        # -------------------------------------------------------------
        self._schedule_on_duty_event(
            state=state,
            master_events=master_events,
            activity=ActivityType.DROPOFF,
            duration=self.rules.DROPOFF_DURATION_HOURS,
            location=dropoff_name,
        )

        # -------------------------------------------------------------
        # STEP 5: Split into Discrete 24.0h Daily Logs
        # -------------------------------------------------------------
        daily_logs = split_events_by_calendar_day(master_events, initial_cycle_used=cycle_used_hours)

        # -------------------------------------------------------------
        # STEP 6: Run Independent Validator
        # -------------------------------------------------------------
        is_valid, violations = self.validator.validate_schedule(
            master_events=master_events,
            initial_cycle_used=cycle_used_hours,
            daily_logs=daily_logs,
        )

        # -------------------------------------------------------------
        # STEP 7: Calculate Overall Summary
        # -------------------------------------------------------------
        total_driving = sum(e.duration_hours for e in master_events if e.status == DutyStatus.D)
        total_on_duty = sum(e.duration_hours for e in master_events if e.status == DutyStatus.ON)
        total_sleeper = sum(e.duration_hours for e in master_events if e.status == DutyStatus.SB)
        total_off_duty = sum(e.duration_hours for e in master_events if e.status == DutyStatus.OFF)
        cycle_consumed_trip = total_driving + total_on_duty

        summary = HOSSummary(
            cycle_used_hours_initial=cycle_used_hours,
            cycle_hours_consumed_trip=cycle_consumed_trip,
            cycle_remaining_hours=max(0.0, self.rules.MAX_CYCLE_HOURS - (cycle_used_hours + cycle_consumed_trip)),
            trip_days=len(daily_logs),
            driving_hours=total_driving,
            on_duty_hours=total_on_duty,
            sleeper_hours=total_sleeper,
            off_duty_hours=total_off_duty,
            compliant=is_valid,
            violations=violations,
        )

        validation_result = {
            "is_valid": is_valid,
            "violations": violations,
        }

        return master_events, daily_logs, summary, validation_result

    def _schedule_driving_leg(
        self,
        leg: RouteLeg,
        state: HOSState,
        master_events: List[HOSEvent],
        destination_name: str,
    ) -> None:
        """Segment and schedule a continuous driving leg subject to all HOS and fuel limits."""
        rem_dur = leg.duration_hours
        rem_miles = leg.distance_miles
        speed = rem_miles / rem_dur if rem_dur > 0 else 55.0

        while rem_dur > 1e-4:
            # 1. Check Cycle Capacity
            if state.cycle_remaining(self.rules.MAX_CYCLE_HOURS) <= 1e-4:
                if self.rules.ALLOW_34_HOUR_RESTART:
                    self._schedule_restart(state, master_events)
                else:
                    # Cycle capacity exhausted and no restart allowed
                    break

            # 2. Check 11h Driving Limit & 14h Duty Window
            if (
                state.driving_shift_remaining(self.rules.MAX_DRIVING_HOURS_PER_SHIFT) <= 1e-4
                or state.shift_window_remaining(self.rules.MAX_DUTY_WINDOW_HOURS) <= 1e-4
            ):
                self._schedule_rest(state, master_events, duration=self.rules.DAILY_REST_HOURS)

            # 3. Determine max drivable chunk before any constraint is reached
            dur_shift = state.driving_shift_remaining(self.rules.MAX_DRIVING_HOURS_PER_SHIFT)
            dur_window = state.shift_window_remaining(self.rules.MAX_DUTY_WINDOW_HOURS)
            dur_break = state.break_driving_remaining(self.rules.MANDATORY_BREAK_THRESHOLD_DRIVING_HOURS)
            dur_cycle = state.cycle_remaining(self.rules.MAX_CYCLE_HOURS)

            miles_fuel_rem = state.fuel_miles_remaining(self.rules.MAX_MILES_BETWEEN_FUEL)
            dur_fuel = (miles_fuel_rem / speed) if speed > 0 else 999.0

            drive_chunk = min(rem_dur, dur_shift, dur_window, dur_break, dur_fuel, dur_cycle)

            if drive_chunk <= 1e-4:
                # Force rest if stuck in window boundary
                self._schedule_rest(state, master_events, duration=self.rules.DAILY_REST_HOURS)
                continue

            chunk_miles = min(rem_miles, drive_chunk * speed) if rem_dur > drive_chunk else rem_miles

            # 4. Insert Driving Event
            start_m = state.current_mile
            end_m = start_m + chunk_miles
            ev_start = state.current_time
            ev_end = ev_start + timedelta(hours=drive_chunk)
            ev_id = f"ev-{len(master_events) + 1}"

            self._append_event(
                state=state,
                master_events=master_events,
                event=HOSEvent(
                    id=ev_id,
                    status=DutyStatus.D,
                    activity=ActivityType.DRIVING,
                    start_time=ev_start,
                    end_time=ev_end,
                    duration_hours=drive_chunk,
                    start_mile=start_m,
                    end_mile=end_m,
                    location=f"En route to {destination_name}",
                    metadata={"speed_mph": round(speed, 1)},
                ),
            )

            rem_dur -= drive_chunk
            rem_miles -= chunk_miles

            # 5. Check what triggered the chunk boundary
            if state.miles_since_fuel >= (self.rules.MAX_MILES_BETWEEN_FUEL - 1e-4):
                # Mandatory Fuel Event
                self._schedule_fuel(state, master_events)
            elif (
                state.break_driving_remaining(self.rules.MANDATORY_BREAK_THRESHOLD_DRIVING_HOURS) <= 1e-4
                and rem_dur > 1e-4
            ):
                # 30-minute break needed
                self._schedule_break(state, master_events)

    def _schedule_on_duty_event(
        self,
        state: HOSState,
        master_events: List[HOSEvent],
        activity: str,
        duration: float,
        location: str,
    ) -> None:
        """Schedule an on-duty non-driving event (Pickup or Dropoff)."""
        # Check cycle capacity
        if state.cycle_remaining(self.rules.MAX_CYCLE_HOURS) < duration:
            if self.rules.ALLOW_34_HOUR_RESTART:
                self._schedule_restart(state, master_events, location=location)

        ev_start = state.current_time
        ev_end = ev_start + timedelta(hours=duration)
        ev_id = f"ev-{len(master_events) + 1}"

        self._append_event(
            state=state,
            master_events=master_events,
            event=HOSEvent(
                id=ev_id,
                status=DutyStatus.ON,
                activity=activity,
                start_time=ev_start,
                end_time=ev_end,
                duration_hours=duration,
                start_mile=state.current_mile,
                end_mile=state.current_mile,
                location=location,
            ),
        )

    def _schedule_fuel(self, state: HOSState, master_events: List[HOSEvent]) -> None:
        """Schedule a 30-minute fueling stop (status ON, qualifies as 30m break)."""
        dur = self.rules.FUELING_DURATION_HOURS
        ev_start = state.current_time
        ev_end = ev_start + timedelta(hours=dur)
        ev_id = f"ev-{len(master_events) + 1}"

        self._append_event(
            state=state,
            master_events=master_events,
            event=HOSEvent(
                id=ev_id,
                status=DutyStatus.ON,
                activity=ActivityType.FUEL,
                start_time=ev_start,
                end_time=ev_end,
                duration_hours=dur,
                start_mile=state.current_mile,
                end_mile=state.current_mile,
                location=f"Fuel Stop at Mile {round(state.current_mile, 1)}",
            ),
        )
        # Reset miles since fuel
        state.miles_since_fuel = 0.0

    def _schedule_break(self, state: HOSState, master_events: List[HOSEvent]) -> None:
        """Schedule a 30-minute qualifying break (status OFF)."""
        dur = self.rules.MANDATORY_BREAK_DURATION_HOURS
        ev_start = state.current_time
        ev_end = ev_start + timedelta(hours=dur)
        ev_id = f"ev-{len(master_events) + 1}"

        self._append_event(
            state=state,
            master_events=master_events,
            event=HOSEvent(
                id=ev_id,
                status=DutyStatus.OFF,
                activity=ActivityType.BREAK,
                start_time=ev_start,
                end_time=ev_end,
                duration_hours=dur,
                start_mile=state.current_mile,
                end_mile=state.current_mile,
                location=f"Rest Area at Mile {round(state.current_mile, 1)}",
            ),
        )

    def _schedule_rest(
        self,
        state: HOSState,
        master_events: List[HOSEvent],
        duration: float = 10.0,
        location: Optional[str] = None,
    ) -> None:
        """Schedule a qualifying 10-hour daily rest period (status SB)."""
        ev_start = state.current_time
        ev_end = ev_start + timedelta(hours=duration)
        loc = location or f"Rest Stop at Mile {round(state.current_mile, 1)}"
        ev_id = f"ev-{len(master_events) + 1}"

        self._append_event(
            state=state,
            master_events=master_events,
            event=HOSEvent(
                id=ev_id,
                status=DutyStatus.SB,
                activity=ActivityType.REST,
                start_time=ev_start,
                end_time=ev_end,
                duration_hours=duration,
                start_mile=state.current_mile,
                end_mile=state.current_mile,
                location=loc,
            ),
        )

    def _schedule_restart(
        self,
        state: HOSState,
        master_events: List[HOSEvent],
        location: Optional[str] = None,
    ) -> None:
        """Schedule a 34-hour restart period (status OFF) and reset cycle accounting."""
        dur = self.rules.CYCLE_RESTART_HOURS
        ev_start = state.current_time
        ev_end = ev_start + timedelta(hours=dur)
        loc = location or f"34-Hour Restart at Mile {round(state.current_mile, 1)}"
        ev_id = f"ev-{len(master_events) + 1}"

        self._append_event(
            state=state,
            master_events=master_events,
            event=HOSEvent(
                id=ev_id,
                status=DutyStatus.OFF,
                activity=ActivityType.RESTART,
                start_time=ev_start,
                end_time=ev_end,
                duration_hours=dur,
                start_mile=state.current_mile,
                end_mile=state.current_mile,
                location=loc,
            ),
        )

    def _append_event(
        self,
        state: HOSState,
        master_events: List[HOSEvent],
        event: HOSEvent,
    ) -> None:
        """Update continuous state machine upon inserting an event."""
        master_events.append(event)
        dur = event.duration_hours

        if event.status in (DutyStatus.D, DutyStatus.ON):
            if state.shift_start_time is None:
                state.shift_start_time = event.start_time
            state.cycle_hours_used += dur
            state.consecutive_rest_hours = 0.0

        if event.status == DutyStatus.D:
            state.driving_hours_in_shift += dur
            state.driving_hours_since_break += dur
            state.miles_since_fuel += (event.end_mile - event.start_mile)
            state.current_mile = event.end_mile
        elif dur >= (self.rules.MANDATORY_BREAK_DURATION_HOURS - 1e-4):
            # Qualifying interruption of >= 30m resets break clock!
            state.driving_hours_since_break = 0.0

        if event.status in (DutyStatus.OFF, DutyStatus.SB):
            state.consecutive_rest_hours += dur
            if state.consecutive_rest_hours >= (self.rules.DAILY_REST_HOURS - 1e-4):
                # 10h rest resets shift!
                state.shift_start_time = None
                state.driving_hours_in_shift = 0.0
                state.driving_hours_since_break = 0.0
            if state.consecutive_rest_hours >= (self.rules.CYCLE_RESTART_HOURS - 1e-4):
                # 34h restart resets cycle!
                state.cycle_hours_used = 0.0

        state.current_time = event.end_time
