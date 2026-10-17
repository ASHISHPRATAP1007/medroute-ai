"""
Phase 2 — concrete Google Places integration, on **Places API (New)**.

Why "New": Google no longer lets new Google Cloud projects enable the
legacy Places API (maps.googleapis.com/maps/api/place/...). A freshly
created API key would get REQUEST_DENIED from the legacy endpoints, so
this client talks to https://places.googleapis.com/v1 instead.

Enable "Places API (New)" on the key's project. Place IDs are the same
in both APIs, so IDs already cached in `place_enrichments` keep working.

The rest of the codebase (external_data_service, discovery_service, the
frontend) was written against the legacy response shape — `name`,
`formatted_address`, `geometry.location`, `opening_hours.weekday_text`,
`reviews[].author_name`… — so every public method here normalizes the
New API response back into that shape. Callers don't need to change.

Cost note: Places (New) bills by the fields in X-Goog-FieldMask. We only
ask for what each call needs; rating/reviews/opening hours sit in the
pricier SKUs, so they are only requested where they're actually used.

Callers should go through external_data_service / discovery_service,
never call this class directly from a router.
"""
from typing import Any

import httpx

from app.services.future_interfaces import GooglePlacesService


class GooglePlacesUnavailableError(Exception):
    """Raised when Google Places is not configured or an API call fails."""


BASE_URL = "https://places.googleapis.com/v1"

# Field masks (no spaces allowed by the API).
_SEARCH_FIELDS = ",".join([
    "places.id", "places.displayName", "places.formattedAddress", "places.location",
    "places.rating", "places.userRatingCount",
])
_ENRICHMENT_FIELDS = ",".join([
    "id", "rating", "userRatingCount", "regularOpeningHours", "photos", "reviews",
])
_BASIC_FIELDS = ",".join([
    "id", "displayName", "formattedAddress", "nationalPhoneNumber", "internationalPhoneNumber", "location",
])


# ---------- New API -> legacy-shaped dicts ----------

def _normalize_place(p: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {"place_id": p.get("id")}

    if "displayName" in p:
        out["name"] = (p.get("displayName") or {}).get("text")
    if "formattedAddress" in p:
        out["formatted_address"] = p.get("formattedAddress")
    if "nationalPhoneNumber" in p or "internationalPhoneNumber" in p:
        out["formatted_phone_number"] = p.get("nationalPhoneNumber") or p.get("internationalPhoneNumber")
    if "location" in p:
        loc = p.get("location") or {}
        out["geometry"] = {"location": {"lat": loc.get("latitude"), "lng": loc.get("longitude")}}
    if "rating" in p:
        out["rating"] = p.get("rating")
    if "userRatingCount" in p:
        out["user_ratings_total"] = p.get("userRatingCount")
    if "regularOpeningHours" in p:
        hours = p.get("regularOpeningHours") or {}
        out["opening_hours"] = {
            "open_now": hours.get("openNow"),
            "weekday_text": hours.get("weekdayDescriptions") or [],
        }
    if "photos" in p:
        out["photos"] = [
            # `photo_reference` now holds the New API photo resource name
            # ("places/<id>/photos/<ref>"), usable with GET {BASE_URL}/<name>/media.
            {"photo_reference": ph.get("name"), "width": ph.get("widthPx"), "height": ph.get("heightPx")}
            for ph in (p.get("photos") or [])
        ]
    if "reviews" in p:
        out["reviews"] = [
            {
                "author_name": (r.get("authorAttribution") or {}).get("displayName"),
                "rating": r.get("rating"),
                "text": (r.get("text") or r.get("originalText") or {}).get("text"),
                "time": r.get("publishTime"),
            }
            for r in (p.get("reviews") or [])
        ]
    return out


class HttpxGooglePlacesService(GooglePlacesService):
    def __init__(self, api_key: str, timeout_seconds: float = 8.0):
        if not api_key:
            raise GooglePlacesUnavailableError("Google Places API key is not configured.")
        self._api_key = api_key
        self._timeout = timeout_seconds

    def _headers(self, field_mask: str) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self._api_key,
            "X-Goog-FieldMask": field_mask,
        }

    async def _request(self, method: str, url: str, *, field_mask: str, json: dict | None = None) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.request(method, url, headers=self._headers(field_mask), json=json)
        except Exception as exc:  # network error, timeout
            raise GooglePlacesUnavailableError(f"could not reach Google Places: {exc}") from exc

        if resp.status_code >= 400:
            # Google returns {"error": {"code", "message", "status"}} — surface
            # its message (e.g. "API key not valid", "Places API (New) has not
            # been used in project ...") so admins know what to fix.
            try:
                err = resp.json().get("error", {})
                message = err.get("message") or err.get("status") or resp.text[:200]
            except Exception:
                message = resp.text[:200]
            raise GooglePlacesUnavailableError(f"Google Places returned HTTP {resp.status_code}: {message}")

        try:
            return resp.json()
        except Exception as exc:
            raise GooglePlacesUnavailableError(f"invalid JSON from Google Places: {exc}") from exc

    # ---------- public API (legacy-shaped results) ----------

    async def find_place_id(self, text_query: str) -> str | None:
        """Resolve a free-text address/name (e.g. 'Dr. X, Clinic Name, City') into a place_id."""
        data = await self._request(
            "POST", f"{BASE_URL}/places:searchText", field_mask="places.id",
            json={"textQuery": text_query, "pageSize": 1},
        )
        places = data.get("places") or []
        return places[0].get("id") if places else None

    async def fetch_place_details(self, place_id: str, *, include_basic: bool = False) -> dict[str, Any]:
        """
        Rating, review count, opening hours, photos and reviews for a place.
        With include_basic=True also returns name, address, phone and
        location in the same call (used when importing a new doctor).
        """
        mask = _ENRICHMENT_FIELDS + ("," + _BASIC_FIELDS if include_basic else "")
        data = await self._request("GET", f"{BASE_URL}/places/{place_id}", field_mask=mask)
        return _normalize_place(data)

    async def search_nearby(self, lat: float, lng: float, radius_m: int) -> list[dict[str, Any]]:
        data = await self._request(
            "POST", f"{BASE_URL}/places:searchNearby", field_mask=_SEARCH_FIELDS,
            json={
                "includedTypes": ["doctor"],
                "maxResultCount": 20,
                "locationRestriction": {
                    "circle": {"center": {"latitude": lat, "longitude": lng}, "radius": float(min(radius_m, 50000))}
                },
            },
        )
        return [_normalize_place(p) for p in data.get("places") or []]

    async def text_search(self, query: str) -> list[dict[str, Any]]:
        """
        Free-text discovery search, e.g. "cardiologist in Gomti Nagar, Lucknow".
        Used by the doctor-discovery admin feature to find *new* real-world
        doctors to import — distinct from find_place_id, which resolves a
        single known doctor's address to a place_id for enrichment sync.
        """
        data = await self._request(
            "POST", f"{BASE_URL}/places:searchText", field_mask=_SEARCH_FIELDS,
            json={"textQuery": query, "includedType": "doctor", "pageSize": 20, "regionCode": "IN"},
        )
        return [_normalize_place(p) for p in data.get("places") or []]
