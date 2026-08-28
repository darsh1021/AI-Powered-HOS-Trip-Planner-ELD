"""Routing Service using Project OSRM API."""

import requests
from typing import Tuple, List, Dict, Any

from .hos.models import RouteResult, RouteLeg

OSRM_URL = "https://router.project-osrm.org/route/v1/driving"


def get_route(
    coordinates: List[Tuple[float, float]],
    stops_metadata: List[Dict[str, Any]],
    timeout: int = 15,
) -> RouteResult:
    """Call OSRM routing API with an ordered list of (lat, lon) coordinates.

    Returns a RouteResult dataclass with total distance, duration, geometry,
    stops, and segmented RouteLeg objects.
    """
    if len(coordinates) < 2:
        raise ValueError("At least two coordinates are required for routing")

    coord_str = ";".join([f"{lon},{lat}" for lat, lon in coordinates])
    url = f"{OSRM_URL}/{coord_str}"
    params = {
        "overview": "full",
        "geometries": "geojson",
        "steps": "false",
    }

    try:
        resp = requests.get(url, params=params, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        raise ValueError(f"OSRM routing request failed: {e}")

    if data.get("code") != "Ok" or not data.get("routes"):
        raise ValueError(f"OSRM route calculation failed: {data.get('message', 'No route found')}")

    route = data["routes"][0]
    geometry_coords = route["geometry"]["coordinates"]  # [lon, lat] pairs from GeoJSON
    latlng_geometry = [[lat, lon] for lon, lat in geometry_coords]

    total_dist_km = route["distance"] / 1000.0
    total_dist_mi = total_dist_km * 0.621371
    total_dur_sec = float(route["duration"])
    total_dur_hr = total_dur_sec / 3600.0

    # Parse route legs from OSRM response if available
    osrm_legs = route.get("legs", [])
    legs: List[RouteLeg] = []

    if osrm_legs and len(osrm_legs) == len(stops_metadata) - 1:
        for idx, leg_data in enumerate(osrm_legs):
            orig_meta = stops_metadata[idx]
            dest_meta = stops_metadata[idx + 1]
            leg_km = leg_data["distance"] / 1000.0
            leg_mi = leg_km * 0.621371
            leg_sec = float(leg_data["duration"])
            leg_hr = leg_sec / 3600.0

            legs.append(
                RouteLeg(
                    origin_name=orig_meta.get("address", orig_meta.get("name", "Origin")),
                    destination_name=dest_meta.get("address", dest_meta.get("name", "Destination")),
                    distance_miles=round(leg_mi, 2),
                    distance_km=round(leg_km, 2),
                    duration_hours=round(leg_hr, 3),
                    duration_sec=round(leg_sec, 1),
                )
            )

    return RouteResult(
        distance_km=round(total_dist_km, 2),
        distance_miles=round(total_dist_mi, 2),
        duration_sec=round(total_dur_sec, 1),
        duration_hours=round(total_dur_hr, 2),
        coordinates=latlng_geometry,
        stops=stops_metadata,
        legs=legs,
    )
