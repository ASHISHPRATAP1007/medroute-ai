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
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.audit_log import AuditAction
from app.models.directory_mixins import EntitySource
from app.models.doctor import Doctor
from app.models.place_enrichment import PlaceEnrichment
from app.models.specialization import Specialization
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


async def search_doctors(
    db: AsyncSession, specialization_name: str, area: str, city: str, state: str
) -> list[dict]:
    service = _get_places_service()
    location = ", ".join(part for part in (area, city, state) if part)
    query = f"{specialization_name} doctor in {location}"

    try:
        results = await service.text_search(query)
    except GooglePlacesUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Google Places search failed: {exc}")

    results = [r for r in results[:20] if r.get("place_id") and r.get("name")]

    # Flag candidates already in our directory so the admin doesn't import twice.
    place_ids = [r["place_id"] for r in results]
    already: set[str] = set()
    if place_ids:
        rows = await db.execute(select(Doctor.external_place_id).where(Doctor.external_place_id.in_(place_ids)))
        already = {row[0] for row in rows.all()}

    candidates = []
    for r in results:
        location = (r.get("geometry") or {}).get("location") or {}
        candidates.append({
            "place_id": r["place_id"],
            "name": r["name"],
            "address": r.get("formatted_address"),
            "rating": r.get("rating"),
            "user_ratings_total": r.get("user_ratings_total"),
            "latitude": location.get("lat"),
            "longitude": location.get("lng"),
            "already_imported": r["place_id"] in already,
        })
    return candidates


async def import_doctor(
    db: AsyncSession, *, place_id: str, specialization_id: uuid.UUID,
    city: str, state: str, area: str, admin_id: uuid.UUID,
) -> Doctor:
    existing = await db.execute(select(Doctor.id).where(Doctor.external_place_id == place_id))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This doctor is already in your directory.")

    spec = await db.get(Specialization, specialization_id)
    if spec is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Specialization not found.")

    service = _get_places_service()
    try:
        # One call returns both the basic profile and the enrichment data.
        details = await service.fetch_place_details(place_id, include_basic=True)
    except GooglePlacesUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Could not fetch place details: {exc}")

    name = details.get("name")
    address = details.get("formatted_address")
    phone = details.get("formatted_phone_number")
    location = (details.get("geometry") or {}).get("location") or {}

    if not name or not address:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Google Places did not return enough data to import this doctor.",
        )

    now = datetime.now(timezone.utc)
    cap = settings.GOOGLE_PLACES_MAX_CACHED_REVIEWS
    doctor = Doctor(
        full_name=name[:150], specialization_id=specialization_id, phone=(phone or None) and phone[:20],
        address=address[:500], area=area or None, city=city, state=state,
        latitude=location.get("lat"), longitude=location.get("lng"),
        source=EntitySource.EXTERNAL, external_provider="google_places", external_place_id=place_id,
        last_external_sync=now.isoformat(),
        created_by=admin_id, updated_by=admin_id,
    )
    db.add(doctor)
    await db.flush()

    enrichment = PlaceEnrichment(
        entity_type="Doctor", entity_id=doctor.id, place_id=place_id,
        rating=details.get("rating"), user_ratings_total=details.get("user_ratings_total"),
        opening_hours=details.get("opening_hours"), photos=(details.get("photos") or [])[:cap],
        reviews=[
            {"author": r.get("author_name"), "rating": r.get("rating"), "text": r.get("text"), "time": r.get("time")}
            for r in (details.get("reviews") or [])[:cap]
        ],
        last_synced_at=now, last_sync_status="SUCCESS",
    )
    db.add(enrichment)

    await log_action(
        db, user_id=admin_id, action=AuditAction.DOCTOR_CREATED, entity_type="Doctor", entity_id=doctor.id,
        description=f"Doctor '{name}' imported from Google Places.",
    )
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This doctor is already in your directory.")
    await db.refresh(doctor)
    return doctor
