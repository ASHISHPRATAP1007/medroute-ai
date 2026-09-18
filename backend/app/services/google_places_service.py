"""
Phase 2 — concrete Google Places integration.

NOTE: this has not been exercised against the real Google Places API —
the development environment that produced it had no outbound network
access. The request params and response field names follow Google's
documented Places API (legacy "Place Details"/"Find Place"/"Nearby
Search" endpoints) as of Claude's training data, but Google does
change field names and API versions periodically — verify against
https://developers.google.com/maps/documentation/places/web-service
before relying on this in production, and add integration tests that
hit a real (or recorded/VCR-style) response.

Callers should go through app/services/external_data_service.py, which
adds caching, quota-aware on-demand sync, and graceful degradation —
never call this class directly from a router.
"""
from typing import Any

import httpx

from app.services.future_interfaces import GooglePlacesService


class GooglePlacesUnavailableError(Exception):
    """Raised when Google Places is not configured or an API call fails."""


class HttpxGooglePlacesService(GooglePlacesService):
    FIND_PLACE_URL = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
    DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"
    NEARBY_URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"

    def __init__(self, api_key: str, timeout_seconds: float = 8.0):
        if not api_key:
            raise GooglePlacesUnavailableError("Google Places API key is not configured.")
        self._api_key = api_key
        self._timeout = timeout_seconds

    async def find_place_id(self, text_query: str) -> str | None:
        """Resolve a free-text address/name (e.g. 'Dr. X, Clinic Name, City') into a place_id."""
        params = {"input": text_query, "inputtype": "textquery", "fields": "place_id", "key": self._api_key}
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.get(self.FIND_PLACE_URL, params=params)
                resp.raise_for_status()
                data = resp.json()
        except Exception as exc:  # network error, timeout, non-2xx, bad JSON
            raise GooglePlacesUnavailableError(f"Google Places lookup failed: {exc}") from exc

        if data.get("status") != "OK" or not data.get("candidates"):
            return None
        return data["candidates"][0].get("place_id")

    async def fetch_place_details(self, place_id: str) -> dict[str, Any]:
        params = {
            "place_id": place_id,
            "fields": "rating,user_ratings_total,opening_hours,photos,reviews",
            "key": self._api_key,
        }
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.get(self.DETAILS_URL, params=params)
                resp.raise_for_status()
                data = resp.json()
        except Exception as exc:
            raise GooglePlacesUnavailableError(f"Google Places details fetch failed: {exc}") from exc

        if data.get("status") != "OK":
            raise GooglePlacesUnavailableError(f"Google Places returned status={data.get('status')}")
        return data.get("result", {})

    async def search_nearby(self, lat: float, lng: float, radius_m: int) -> list[dict[str, Any]]:
        params = {"location": f"{lat},{lng}", "radius": radius_m, "type": "doctor", "key": self._api_key}
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.get(self.NEARBY_URL, params=params)
                resp.raise_for_status()
                data = resp.json()
        except Exception as exc:
            raise GooglePlacesUnavailableError(f"Google Places nearby search failed: {exc}") from exc

        if data.get("status") not in ("OK", "ZERO_RESULTS"):
            raise GooglePlacesUnavailableError(f"Google Places returned status={data.get('status')}")
        return data.get("results", [])
