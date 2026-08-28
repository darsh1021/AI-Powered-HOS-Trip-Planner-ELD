"""Geocoding Service using OpenStreetMap Nominatim API."""

import requests
from typing import Tuple

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "spotter-tms/2.4 (hos-planner-engine)"


def geocode_address(address: str, timeout: int = 10) -> Tuple[float, float]:
    """Return (latitude, longitude) for a given address string.

    Raises ValueError if geocoding fails or location is not found.
    """
    if not address or not address.strip():
        raise ValueError("Address cannot be empty")

    params = {"q": address.strip(), "format": "json", "limit": 1}
    headers = {"User-Agent": USER_AGENT}

    try:
        resp = requests.get(NOMINATIM_URL, params=params, headers=headers, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        raise ValueError(f"Geocoding network error for '{address}': {e}")

    if not data or not isinstance(data, list):
        raise ValueError(f"Unable to geocode address: '{address}'")

    try:
        lat = float(data[0]["lat"])
        lng = float(data[0]["lon"])
        return lat, lng
    except (KeyError, ValueError, IndexError):
        raise ValueError(f"Invalid geocoding response coordinates for '{address}'")
