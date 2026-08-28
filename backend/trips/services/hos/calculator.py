"""HOS Calculator and Midnight Event Splitter.

Calculates exact daily status totals and splits master timeline events at 00:00:00
midnight boundaries into standard 24.0-hour ELD daily logs.
"""

from datetime import datetime, time, timedelta
from typing import List, Dict
import copy

from .models import HOSEvent, DailyLog, DailyTotals, DutyStatus, ActivityType


def calculate_daily_totals(events: List[HOSEvent]) -> DailyTotals:
    """Sum hours for each duty status in a given list of events."""
    driving = 0.0
    on_duty = 0.0
    sleeper = 0.0
    off_duty = 0.0

    for ev in events:
        dur = ev.duration_hours
        if ev.status == DutyStatus.D:
            driving += dur
        elif ev.status == DutyStatus.ON:
            on_duty += dur
        elif ev.status == DutyStatus.SB:
            sleeper += dur
        elif ev.status == DutyStatus.OFF:
            off_duty += dur

    total = driving + on_duty + sleeper + off_duty
    return DailyTotals(
        driving_hours=driving,
        on_duty_hours=on_duty,
        sleeper_hours=sleeper,
        off_duty_hours=off_duty,
        total_hours=total,
    )


def split_events_by_calendar_day(master_events: List[HOSEvent], initial_cycle_used: float = 0.0) -> List[DailyLog]:
    """Slice master timeline events across midnight boundaries (00:00:00)

    and organize them into discrete calendar-day DailyLogs where each complete
    day totals exactly 24.0 hours, with accurate cumulative cycle and mileage metrics.
    """
    if not master_events:
        return []

    first_event = master_events[0]
    last_event = master_events[-1]

    # Overall start and end dates
    start_date = first_event.start_time.date()
    end_date = last_event.end_time.date()

    # Step 1: Prepend initial OFF-duty on start_date if trip begins after 00:00
    all_events: List[HOSEvent] = []
    day1_midnight = datetime.combine(start_date, time(0, 0, 0))
    if first_event.start_time > day1_midnight:
        init_dur = (first_event.start_time - day1_midnight).total_seconds() / 3600.0
        all_events.append(
            HOSEvent(
                id="ev-init-off",
                status=DutyStatus.OFF,
                activity=ActivityType.INITIAL_OFF_DUTY,
                start_time=day1_midnight,
                end_time=first_event.start_time,
                duration_hours=init_dur,
                start_mile=0.0,
                end_mile=0.0,
                location=first_event.location,
            )
        )

    all_events.extend(copy.deepcopy(master_events))

    # Step 2: Append trailing OFF-duty on end_date if trip finishes before 24:00
    final_midnight = datetime.combine(end_date + timedelta(days=1), time(0, 0, 0))
    if last_event.end_time < final_midnight:
        trail_dur = (final_midnight - last_event.end_time).total_seconds() / 3600.0
        all_events.append(
            HOSEvent(
                id="ev-trail-off",
                status=DutyStatus.OFF,
                activity=ActivityType.REST,
                start_time=last_event.end_time,
                end_time=final_midnight,
                duration_hours=trail_dur,
                start_mile=last_event.end_mile,
                end_mile=last_event.end_mile,
                location=last_event.location,
            )
        )

    # Step 3: Slice any event that crosses midnight
    sliced_events: List[HOSEvent] = []
    for ev in all_events:
        cur_start = ev.start_time
        cur_end = ev.end_time
        total_dur = ev.duration_hours
        total_miles = ev.end_mile - ev.start_mile
        part_idx = 1

        while cur_start.date() < cur_end.date():
            # Next midnight boundary
            next_midnight = datetime.combine(cur_start.date() + timedelta(days=1), time(0, 0, 0))
            slice_dur = (next_midnight - cur_start).total_seconds() / 3600.0

            # Interpolate mileage proportion if moving
            slice_miles = 0.0
            if total_dur > 0 and total_miles > 0:
                slice_miles = total_miles * (slice_dur / total_dur)

            sliced_events.append(
                HOSEvent(
                    id=f"{ev.id}-p{part_idx}",
                    status=ev.status,
                    activity=ev.activity,
                    start_time=cur_start,
                    end_time=next_midnight,
                    duration_hours=slice_dur,
                    start_mile=ev.start_mile,
                    end_mile=ev.start_mile + slice_miles,
                    location=ev.location,
                    metadata=ev.metadata,
                )
            )

            # Advance
            ev.start_mile += slice_miles
            total_dur -= slice_dur
            total_miles -= slice_miles
            cur_start = next_midnight
            part_idx += 1

        # Remainder within the final single date
        rem_dur = (cur_end - cur_start).total_seconds() / 3600.0
        if rem_dur > 1e-6:  # ignore tiny epsilon
            ev_id = f"{ev.id}-p{part_idx}" if part_idx > 1 else ev.id
            sliced_events.append(
                HOSEvent(
                    id=ev_id,
                    status=ev.status,
                    activity=ev.activity,
                    start_time=cur_start,
                    end_time=cur_end,
                    duration_hours=rem_dur,
                    start_mile=ev.start_mile,
                    end_mile=ev.end_mile,
                    location=ev.location,
                    metadata=ev.metadata,
                )
            )

    # Step 4: Group sliced events by calendar date
    events_by_date: Dict[str, List[HOSEvent]] = {}
    for ev in sliced_events:
        d_str = ev.start_time.strftime("%Y-%m-%d")
        if d_str not in events_by_date:
            events_by_date[d_str] = []
        events_by_date[d_str].append(ev)

    # Step 5: Build DailyLogs with running cumulative totals
    daily_logs: List[DailyLog] = []
    sorted_dates = sorted(events_by_date.keys())
    running_cycle = initial_cycle_used

    for idx, d_str in enumerate(sorted_dates, start=1):
        day_evs = events_by_date[d_str]
        totals = calculate_daily_totals(day_evs)

        # Check for 34h restart in day events
        for ev in day_evs:
            if ev.activity == ActivityType.RESTART and ev.duration_hours >= 34.0:
                running_cycle = 0.0

        # Day on-duty hours
        day_on_duty = totals.driving_hours + totals.on_duty_hours
        running_cycle += day_on_duty
        rem_cycle = max(0.0, 70.0 - running_cycle)

        # Miles driven today
        day_miles = sum(
            max(0.0, e.end_mile - e.start_mile) for e in day_evs if e.status == DutyStatus.D
        )
        last_ev_mile = day_evs[-1].end_mile if day_evs else 0.0

        daily_logs.append(
            DailyLog(
                day=idx,
                date=d_str,
                events=day_evs,
                totals=totals,
                cumulative_cycle_used=running_cycle,
                cycle_remaining=rem_cycle,
                miles_today=day_miles,
                total_miles_to_date=last_ev_mile,
            )
        )

    return daily_logs
