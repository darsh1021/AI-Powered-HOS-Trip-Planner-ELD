"""Geocoding Service with Multi-Provider Fallback and Local Caching.

Uses:
1. Static lookup & LRU memory cache for major freight hubs / US cities (instant, 0 network, no 429).
2. Photon (Komoot OSM Geocoder API) - high limit free OSM search.
3. Open-Meteo Geocoding API - reliable fallback for worldwide cities/places.
4. OpenStreetMap Nominatim with retry as final fallback.
"""

import functools
import re
import time
import requests
from typing import Tuple, Optional

# Static coordinates for major US trucking hubs & cities (normalized lowercase)
COMMON_CITIES = {
    "chicago, il": (41.8781, -87.6298),
    "chicago": (41.8781, -87.6298),
    "dallas, tx": (32.7767, -96.7970),
    "dallas": (32.7767, -96.7970),
    "houston, tx": (29.7604, -95.3698),
    "houston": (29.7604, -95.3698),
    "atlanta, ga": (33.7490, -84.3880),
    "atlanta": (33.7490, -84.3880),
    "los angeles, ca": (34.0522, -118.2437),
    "los angeles": (34.0522, -118.2437),
    "new york, ny": (40.7128, -74.0060),
    "new york": (40.7128, -74.0060),
    "nyc": (40.7128, -74.0060),
    "seattle, wa": (47.6062, -122.3321),
    "seattle": (47.6062, -122.3321),
    "denver, co": (39.7392, -104.9903),
    "denver": (39.7392, -104.9903),
    "miami, fl": (25.7617, -80.1918),
    "miami": (25.7617, -80.1918),
    "phoenix, az": (33.4484, -112.0740),
    "phoenix": (33.4484, -112.0740),
    "nashville, tn": (36.1627, -86.7816),
    "nashville": (36.1627, -86.7816),
    "memphis, tn": (35.1495, -90.0490),
    "memphis": (35.1495, -90.0490),
    "indianapolis, in": (39.7684, -86.1581),
    "indianapolis": (39.7684, -86.1581),
    "columbus, oh": (39.9612, -82.9988),
    "columbus": (39.9612, -82.9988),
    "kansas city, mo": (39.0997, -94.5786),
    "kansas city": (39.0997, -94.5786),
    "st. louis, mo": (38.6270, -90.1994),
    "st louis, mo": (38.6270, -90.1994),
    "st louis": (38.6270, -90.1994),
    "detroit, mi": (42.3314, -83.0458),
    "detroit": (42.3314, -83.0458),
    "philadelphia, pa": (39.9526, -75.1652),
    "philadelphia": (39.9526, -75.1652),
    "san antonio, tx": (29.4241, -98.4936),
    "san antonio": (29.4241, -98.4936),
    "san diego, ca": (32.7157, -117.1611),
    "san diego": (32.7157, -117.1611),
    "san francisco, ca": (37.7749, -122.4194),
    "san francisco": (37.7749, -122.4194),
    "charlotte, nc": (35.2271, -80.8431),
    "charlotte": (35.2271, -80.8431),
    "austin, tx": (30.2672, -97.7431),
    "austin": (30.2672, -97.7431),
    "jacksonville, fl": (30.3322, -81.6557),
    "jacksonville": (30.3322, -81.6557),
    "fort worth, tx": (32.7555, -97.3308),
    "fort worth": (32.7555, -97.3308),
    "san jose, ca": (37.3382, -121.8863),
    "san jose": (37.3382, -121.8863),
    "boston, ma": (42.3601, -71.0589),
    "boston": (42.3601, -71.0589),
    "las vegas, nv": (36.1699, -115.1398),
    "las vegas": (36.1699, -115.1398),
    "portland, or": (45.5152, -122.6784),
    "portland": (45.5152, -122.6784),
    "louisville, ky": (38.2527, -85.7585),
    "louisville": (38.2527, -85.7585),
    "baltimore, md": (39.2904, -76.6122),
    "baltimore": (39.2904, -76.6122),
    "milwaukee, wi": (43.0389, -87.9065),
    "milwaukee": (43.0389, -87.9065),
    "albuquerque, nm": (35.0844, -106.6504),
    "albuquerque": (35.0844, -106.6504),
    "tucson, az": (32.2226, -110.9747),
    "tucson": (32.2226, -110.9747),
    "fresno, ca": (36.7468, -119.7726),
    "fresno": (36.7468, -119.7726),
    "sacramento, ca": (38.5816, -121.4944),
    "sacramento": (38.5816, -121.4944),
    "mesa, az": (33.4152, -111.8315),
    "mesa": (33.4152, -111.8315),
    "omaha, ne": (41.2565, -95.9345),
    "omaha": (41.2565, -95.9345),
    "raleigh, nc": (35.7796, -78.6382),
    "raleigh": (35.7796, -78.6382),
    "minneapolis, mn": (44.9778, -93.2650),
    "minneapolis": (44.9778, -93.2650),
    "cleveland, oh": (41.4993, -81.6944),
    "cleveland": (41.4993, -81.6944),
    "tulsa, ok": (36.1540, -95.9928),
    "tulsa": (36.1540, -95.9928),
    "oklahoma city, ok": (35.4676, -97.5164),
    "oklahoma city": (35.4676, -97.5164),
    "salt lake city, ut": (40.7608, -111.8910),
    "salt lake city": (40.7608, -111.8910),
    "pittsburgh, pa": (40.4406, -79.9959),
    "pittsburgh": (40.4406, -79.9959),
    "cincinnati, oh": (39.1031, -84.5120),
    "cincinnati": (39.1031, -84.5120),
    "orlando, fl": (28.5383, -81.3792),
    "orlando": (28.5383, -81.3792),
    "tampa, fl": (27.9506, -82.4572),
    "tampa": (27.9506, -82.4572),
    "birmingham, al": (33.5186, -86.8104),
    "birmingham": (33.5186, -86.8104),
    "little rock, ar": (34.7465, -92.2896),
    "little rock": (34.7465, -92.2896),
    "des moines, ia": (41.5868, -93.6250),
    "des moines": (41.5868, -93.6250),
}

HEADERS = {"User-Agent": "SpotterTMS-HOS-Planner/2.5 (contact@spotter-tms.app)"}


def _clean_key(address: str) -> str:
    """Normalize address for cache key."""
    return re.sub(r"\s+", " ", address.strip().lower())


def _geocode_photon(address: str, timeout: int = 8) -> Optional[Tuple[float, float]]:
    """Geocode using Komoot Photon API (OSM data, high rate limit)."""
    try:
        url = "https://photon.komoot.io/api/"
        resp = requests.get(url, params={"q": address, "limit": 1}, headers=HEADERS, timeout=timeout)
        if resp.status_code == 200:
            data = resp.json()
            features = data.get("features", [])
            if features:
                coords = features[0]["geometry"]["coordinates"]
                # Photon returns [lon, lat]
                return float(coords[1]), float(coords[0])
    except Exception:
        pass
    return None


def _geocode_openmeteo(address: str, timeout: int = 8) -> Optional[Tuple[float, float]]:
    """Geocode using Open-Meteo Geocoding API (free, fast worldwide)."""
    try:
        # Extract main city name for open-meteo
        city_name = address.split(",")[0].strip()
        url = "https://geocoding-api.open-meteo.com/v1/search"
        resp = requests.get(url, params={"name": city_name, "count": 1, "language": "en", "format": "json"}, headers=HEADERS, timeout=timeout)
        if resp.status_code == 200:
            data = resp.json()
            results = data.get("results", [])
            if results:
                return float(results[0]["latitude"]), float(results[0]["longitude"])
    except Exception:
        pass
    return None


def _geocode_nominatim(address: str, timeout: int = 8) -> Optional[Tuple[float, float]]:
    """Geocode using OpenStreetMap Nominatim API."""
    try:
        url = "https://nominatim.openstreetmap.org/search"
        resp = requests.get(url, params={"q": address, "format": "json", "limit": 1}, headers=HEADERS, timeout=timeout)
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, list) and len(data) > 0:
                return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception:
        pass
    return None


@functools.lru_cache(maxsize=1024)
def geocode_address(address: str, timeout: int = 10) -> Tuple[float, float]:
    """Return (latitude, longitude) for a given address string.

    Uses layered lookup:
    1. Static lookup table
    2. Photon API
    3. Open-Meteo Geocoding API
    4. Nominatim API

    Raises ValueError if location cannot be found.
    """
    if not address or not address.strip():
        raise ValueError("Address cannot be empty")

    clean_addr = address.strip()
    norm_key = _clean_key(clean_addr)

    # 1. Check local static dictionary
    if norm_key in COMMON_CITIES:
        return COMMON_CITIES[norm_key]

    # 2. Try Photon API (OSM backed, no 429 on cloud servers)
    res = _geocode_photon(clean_addr, timeout=timeout)
    if res:
        return res

    # 3. Try Open-Meteo API
    res = _geocode_openmeteo(clean_addr, timeout=timeout)
    if res:
        return res

    # 4. Try Nominatim API
    res = _geocode_nominatim(clean_addr, timeout=timeout)
    if res:
        return res

    raise ValueError(f"Unable to geocode address: '{clean_addr}'. Please verify the city or address.")
