"""Tests for Geocoding and Routing Services."""

from unittest.mock import patch, MagicMock
from django.test import SimpleTestCase

from trips.services.geocode import geocode_address
from trips.services.routing import get_route


class TestGeocodeAndRouting(SimpleTestCase):
    @patch("trips.services.geocode.requests.get")
    def test_geocode_address_success(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = [{"lat": "41.8781", "lon": "-87.6298"}]
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        lat, lng = geocode_address("Chicago, IL")
        self.assertEqual(lat, 41.8781)
        self.assertEqual(lng, -87.6298)

    def test_geocode_empty_address_raises(self):
        with self.assertRaises(ValueError):
            geocode_address("")

    @patch("trips.services.routing.requests.get")
    def test_get_route_success(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "code": "Ok",
            "routes": [
                {
                    "distance": 500000.0,  # 500 km
                    "duration": 18000.0,   # 5 hours
                    "geometry": {
                        "coordinates": [[-87.6298, 41.8781], [-96.7970, 32.7767]]
                    },
                    "legs": [
                        {
                            "distance": 500000.0,
                            "duration": 18000.0,
                        }
                    ],
                }
            ],
        }
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        coords = [(41.8781, -87.6298), (32.7767, -96.7970)]
        stops = [{"address": "Chicago, IL"}, {"address": "Dallas, TX"}]

        result = get_route(coords, stops)
        self.assertEqual(result.distance_km, 500.0)
        self.assertEqual(result.duration_hours, 5.0)
        self.assertEqual(len(result.legs), 1)
        self.assertEqual(result.legs[0].origin_name, "Chicago, IL")
        self.assertEqual(result.legs[0].destination_name, "Dallas, TX")
