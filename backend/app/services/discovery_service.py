"""
Admin-triggered discovery of real doctors from Google Places, to replace
manually-entered or demo directory rows with verified real-world data.

Two-step flow, deliberately not automatic:
  1. search_doctors() — free-text search, returns candidates for the admin
     to review. Nothing is written to the database yet.
  2. import_doctor() — admin picks one candidate; only then do we create a
     Doctor row (source=EXTERNAL) and cache its Places data.

This costs a real Google Places API call per search and per import, so it
is never triggered automatically — always an explicit admin action.
"""
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.audit_log import AuditAction
from app.models.directory_mixins import EntitySource
from app.models.doctor import Doctor
from app.models.place_enrichment import PlaceEnrichment
from app.services.audit_service import log_action
from app.services.google_places_service import GooglePlacesUnavailableError, HttpxGooglePlacesService

settings = get_settings()


def _get_places_service() -> HttpxGooglePlacesService:
    if not settings.google_places_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Google Places integration is not configured. Set GOOGLE_PLACES_ENABLED=true "
                "and a valid GOOGLE_PLACES_API_KEY to enable doctor discovery."
            ),
        )
    return HttpxGooglePlacesService(api_key=settings.GOOGLE_PLACES_API_KEY)


async def search_doctors(specialization_name: str, area: str, city: str, state: str) -> list[dict]:
    service = _get_places_service()
    query = f"{specialization_name} doctor in {area}, {city}, {state}"

    try:
        results = await service.text_search(query)
    except GooglePlacesUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Google Places search failed: {exc}")

    candidates = []
    for r in results[:20]:
        location = r.get("geometry", {}).get("location", {})
        candidates.append({
            "place_id": r.get("place_id"),
            "name": r.get("name"),
            "address": r.get("formatted_address"),
            "rating": r.get("rating"),
            "user_ratings_total": r.get("user_ratings_total"),
            "latitude": location.get("lat"),
            "longitude": location.get("lng"),
        })
    return candidates


async def import_doctor(
    db: AsyncSession, *, place_id: str, specialization_id: uuid.UUID,
    city: str, state: str, area: str, admin_id: uuid.UUID,
) -> Doctor:
    service = _get_places_service()

    try:
        details = await service.fetch_place_details(place_id)
    except GooglePlacesUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Could not fetch place details: {exc}")

    import httpx
    params = {
        "place_id": place_id,
        "fields": "name,formatted_address,formatted_phone_number,geometry",
        "key": settings.GOOGLE_PLACES_API_KEY,
    }
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(HttpxGooglePlacesService.DETAILS_URL, params=params)
            resp.raise_for_status()
            basic = resp.json().get("result", {})
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Could not fetch place basic info: {exc}")

    name = basic.get("name")
    address = basic.get("formatted_address")
    phone = basic.get("formatted_phone_number")
    location = basic.get("geometry", {}).get("location", {})

    if not name or not address:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Google Places did not return enough data to import this doctor.")

    doctor = Doctor(
        full_name=name, specialization_id=specialization_id, phone=phone,
        address=address, area=area, city=city, state=state,
        latitude=location.get("lat"), longitude=location.get("lng"),
        source=EntitySource.EXTERNAL, external_provider="google_places", external_place_id=place_id,
        last_external_sync=datetime.now(timezone.utc).isoformat(),
        created_by=admin_id, updated_by=admin_id,
    )
    db.add(doctor)
    await db.flush()

    enrichment = PlaceEnrichment(
        entity_type="Doctor", entity_id=doctor.id, place_id=place_id,
        rating=details.get("rating"), user_ratings_total=details.get("user_ratings_total"),
        opening_hours=details.get("opening_hours"), photos=details.get("photos", [])[:5],
        reviews=[
            {"author": r.get("author_name"), "rating": r.get("rating"), "text": r.get("text"), "time": r.get("time")}
            for r in details.get("reviews", [])[:5]
        ],
        last_synced_at=datetime.now(timezone.utc), last_sync_status="SUCCESS",
    )
    db.add(enrichment)

    await log_action(
        db, user_id=admin_id, action=AuditAction.DOCTOR_CREATED, entity_type="Doctor", entity_id=doctor.id,
        description=f"Doctor '{name}' imported from Google Places.",
    )
    await db.commit()
    await db.refresh(doctor)
    return doctor
