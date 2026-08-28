"""Trip Planner Orchestration Service.

Coordinates Geocoding -> OSRM Routing -> HOS Scheduler -> HOS Validator -> Final API Payload.
"""

from typing import Dict, Any, Optional
from datetime import datetime

from .geocode import geocode_address
from .routing import get_route
from .hos.scheduler import HOSScheduler
from .hos.rules import DEFAULT_HOS_RULES


def plan_trip(
    current_location: str,
    pickup_location: str,
    dropoff_location: str,
    cycle_used_hours: float = 0.0,
    start_time: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Orchestrate entire Trip Planning workflow.

    1. Geocode current, pickup, dropoff locations
    2. Request OSRM multi-waypoint road route
    3. Run HOS scheduling engine
    4. Validate and construct consolidated API payload
    """
    # 1. Geocode all locations
    cur_lat, cur_lng = geocode_address(current_location)
    pick_lat, pick_lng = geocode_address(pickup_location)
    drop_lat, drop_lng = geocode_address(dropoff_location)

    stops_metadata = [
        {"name": "Current", "address": current_location, "lat": cur_lat, "lng": cur_lng},
        {"name": "Pickup", "address": pickup_location, "lat": pick_lat, "lng": pick_lng},
        {"name": "Dropoff", "address": dropoff_location, "lat": drop_lat, "lng": drop_lng},
    ]

    coordinates = [(cur_lat, cur_lng), (pick_lat, pick_lng), (drop_lat, drop_lng)]

    # 2. Compute Road Route
    route_result = get_route(coordinates=coordinates, stops_metadata=stops_metadata)

    # 3. Schedule HOS Multi-Day Timeline
    scheduler = HOSScheduler(rules=DEFAULT_HOS_RULES)
    master_events, daily_logs, hos_summary, validation = scheduler.plan_trip_schedule(
        route_result=route_result,
        cycle_used_hours=cycle_used_hours,
        start_time=start_time,
    )

    # 4. Assemble Final Consolidated Payload
    return {
        "trip": {
            "current_location": current_location,
            "pickup_location": pickup_location,
            "dropoff_location": dropoff_location,
            "cycle_used_hours": round(cycle_used_hours, 2),
        },
        # Backwards compatible route fields for Phase 2 frontend + Phase 3 extensions
        "route": {
            "distance_km": route_result.distance_km,
            "distance_miles": route_result.distance_miles,
            "duration_sec": route_result.duration_sec,
            "duration_hours": route_result.duration_hours,
            "duration_min": round(route_result.duration_sec / 60.0, 2),
            "coordinates": route_result.coordinates,
            "stops": route_result.stops,
            "legs": [
                {
                    "origin": leg.origin_name,
                    "destination": leg.destination_name,
                    "distance_miles": leg.distance_miles,
                    "distance_km": leg.distance_km,
                    "duration_hours": leg.duration_hours,
                }
                for leg in route_result.legs
            ],
        },
        # Flat legacy helpers so Phase 2 components continue rendering without breaking
        "coordinates": route_result.coordinates,
        "distance_km": route_result.distance_km,
        "duration_min": round(route_result.duration_sec / 60.0, 2),
        "stops": route_result.stops,
        # Phase 3/5/6 HOS Intelligence Payload
        "hos": hos_summary.to_dict(),
        "hos_summary": hos_summary.to_dict(),
        "events": [ev.to_dict() for ev in master_events],
        "master_events": [ev.to_dict() for ev in master_events],
        "daily_logs": [log.to_dict() for log in daily_logs],
        "validation": validation,
    }
