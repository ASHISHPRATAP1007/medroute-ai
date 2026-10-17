"""
Free "Explore" — find doctors, clinics, hospitals and medical stores anywhere,
using OpenStreetMap data. No API key, no billing.

- Nominatim (nominatim.openstreetmap.org) turns a typed place ("Gomti Nagar,
  Lucknow") into coordinates.
- Overpass (overpass-api.de) returns the healthcare places around them.

Both are free public services with fair-use rules: identify the app with a
User-Agent, keep request volume low, and cache. Results are cached in memory
(1 h for searches, 24 h for geocoding) and the endpoint is rate-limited.

OpenStreetMap has fewer listings than Google and no ratings or reviews, so the
frontend also offers a free deep link that opens the same search in Google Maps.
"""
import asyncio
import math
import time
from typing import Any

from urllib.parse import quote_plus

import httpx
from fastapi import HTTPException, status

from app.core.config import get_settings

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]

# category -> Overpass tag filters (each becomes one `nwr[...]` clause)
CATEGORIES: dict[str, list[str]] = {
    "doctor": ['["amenity"~"^(doctors|clinic)$"]', '["healthcare"~"^(doctor|clinic|centre)$"]'],
    "hospital": ['["amenity"="hospital"]', '["healthcare"="hospital"]'],
    "pharmacy": ['["amenity"="pharmacy"]', '["healthcare"="pharmacy"]', '["shop"="chemist"]'],
    "distributor": ['["shop"="medical_supply"]', '["wholesale"~"pharma|medical"]'],
}
CATEGORY_LABELS = {"doctor": "Doctor / Clinic", "hospital": "Hospital", "pharmacy": "Medical store", "distributor": "Medical supplier"}

_SEARCH_TTL = 3600
_GEOCODE_TTL = 86400
_cache: dict[tuple, tuple[float, Any]] = {}
_nominatim_lock = asyncio.Lock()  # Nominatim policy: at most 1 request/second
_last_nominatim_call = 0.0


def _cache_get(key):
    hit = _cache.get(key)
    if hit and hit[0] > time.monotonic():
        return hit[1]
    return None


def _cache_set(key, value, ttl):
    if len(_cache) > 2000:  # keep memory bounded
        _cache.clear()
    _cache[key] = (time.monotonic() + ttl, value)


def _headers() -> dict[str, str]:
    s = get_settings()
    return {"User-Agent": f"{s.APP_NAME.replace(' ', '')}/1.0 (field-force app; contact: {s.OSM_CONTACT_EMAIL or 'admin'})"}


def _haversine_km(lat1, lng1, lat2, lng2) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = math.sin(math.radians(lat2 - lat1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lng2 - lng1) / 2) ** 2
    return 2 * r * math.asin(min(1, math.sqrt(a)))


async def geocode(place: str) -> dict:
    """'Gomti Nagar, Lucknow' -> {lat, lng, label}. Raises 404 if not found."""
    global _last_nominatim_call
    key = ("geo", place.strip().lower())
    cached = _cache_get(key)
    if cached:
        return cached
    async with _nominatim_lock:
        wait = 1.0 - (time.monotonic() - _last_nominatim_call)
        if wait > 0:
            await asyncio.sleep(wait)
        try:
            async with httpx.AsyncClient(timeout=10.0, headers=_headers()) as client:
                resp = await client.get(NOMINATIM_URL, params={"q": place, "format": "jsonv2", "limit": 1, "countrycodes": "in"})
                resp.raise_for_status()
                rows = resp.json()
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Location lookup failed: {exc}")
        finally:
            _last_nominatim_call = time.monotonic()
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Couldn't find the place '{place}'. Try adding the city name.")
    row = rows[0]
    result = {"lat": float(row["lat"]), "lng": float(row["lon"]), "label": row.get("display_name", place)}
    _cache_set(key, result, _GEOCODE_TTL)
    return result


def _overpass_query(category: str, lat: float, lng: float, radius_m: int) -> str:
    clauses = "".join(f"nwr{f}(around:{radius_m},{lat:.5f},{lng:.5f});" for f in CATEGORIES[category])
    return f"[out:json][timeout:25];({clauses});out center tags 400;"


async def _run_overpass(query: str) -> list[dict]:
    last_error: Exception | None = None
    async with httpx.AsyncClient(timeout=30.0, headers=_headers()) as client:
        for url in OVERPASS_URLS:
            try:
                resp = await client.post(url, data={"data": query})
                resp.raise_for_status()
                return resp.json().get("elements", [])
            except Exception as exc:  # busy (429/504) or down — try the mirror
                last_error = exc
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=f"Map data service is busy, please try again in a minute. ({last_error})",
    )


def _address(tags: dict) -> str | None:
    parts = [
        " ".join(p for p in (tags.get("addr:housenumber"), tags.get("addr:street")) if p),
        tags.get("addr:suburb") or tags.get("addr:neighbourhood"),
        tags.get("addr:city"),
        tags.get("addr:postcode"),
    ]
    text = ", ".join(p for p in parts if p)
    return text or tags.get("addr:full")


def _to_place(el: dict, category: str, center: tuple[float, float]) -> dict | None:
    tags = el.get("tags") or {}
    name = tags.get("name") or tags.get("name:en")
    lat = el.get("lat") or (el.get("center") or {}).get("lat")
    lng = el.get("lon") or (el.get("center") or {}).get("lon")
    if not name or lat is None or lng is None:
        return None
    speciality = tags.get("healthcare:speciality")
    return {
        "id": f"{el.get('type')}/{el.get('id')}",
        "name": name,
        "category": category,
        "type_label": CATEGORY_LABELS[category],
        "speciality": speciality.replace(";", ", ").replace("_", " ") if speciality else None,
        "address": _address(tags),
        "phone": tags.get("phone") or tags.get("contact:phone") or tags.get("contact:mobile"),
        "opening_hours": tags.get("opening_hours"),
        "website": tags.get("website") or tags.get("contact:website"),
        "latitude": float(lat),
        "longitude": float(lng),
        "distance_km": round(_haversine_km(center[0], center[1], float(lat), float(lng)), 2),
        "osm_url": f"https://www.openstreetmap.org/{el.get('type')}/{el.get('id')}",
        # Free deep link: opens this place's Google Maps listing (ratings, reviews, photos).
        "google_maps_url": f"https://www.google.com/maps/search/?api=1&query={quote_plus(name)}%20{lat},{lng}",
    }


async def explore(
    *, category: str, location: str | None, lat: float | None, lng: float | None,
    radius_km: float, keyword: str | None,
) -> dict:
    if category not in CATEGORIES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unknown category.")
    if lat is None or lng is None:
        if not location or not location.strip():
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Enter a place or use your location.")
        geo = await geocode(location)
        lat, lng, label = geo["lat"], geo["lng"], geo["label"]
    else:
        label = "Your location"

    radius_m = int(max(0.5, min(radius_km, 15)) * 1000)
    key = ("explore", category, round(lat, 3), round(lng, 3), radius_m)
    elements = _cache_get(key)
    if elements is None:
        elements = await _run_overpass(_overpass_query(category, lat, lng, radius_m))
        _cache_set(key, elements, _SEARCH_TTL)

    seen: set[tuple] = set()
    places = []
    for el in elements:
        place = _to_place(el, category, (lat, lng))
        if not place:
            continue
        dedupe = (place["name"].lower(), round(place["latitude"], 4), round(place["longitude"], 4))
        if dedupe in seen:
            continue
        seen.add(dedupe)
        places.append(place)

    if keyword and keyword.strip():
        k = keyword.strip().lower()
        places = [p for p in places if k in p["name"].lower() or k in (p["speciality"] or "").lower()]

    places.sort(key=lambda p: p["distance_km"])
    return {"center": {"lat": lat, "lng": lng, "label": label}, "radius_km": radius_m / 1000, "places": places[:300]}
