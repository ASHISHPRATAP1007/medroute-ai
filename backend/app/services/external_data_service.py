"""
Phase 2 — orchestrates syncing and reading cached Google Places data.

Design:
- Reads (get_cached_enrichment) always hit our own `place_enrichments`
  table — never Google. Doctor/shop/stockist profile pages should be
  fast and not depend on Google's uptime or quota.
- Writes (sync_place_details) are triggered explicitly by an admin
  action, never automatically on every profile view — Google Places
  has real per-request cost and rate limits, and Phase 1's directory
  entries don't come with a place_id yet, so the first sync also has
  to *resolve* the place_id from the address.
- If GOOGLE_PLACES_ENABLED is false or no API key is set, sync raises
  a clear, actionable error rather than silently doing nothing or
  fabricating data (spec: "Do not fabricate external data").
"""
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.audit_log import AuditAction
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
                "and a valid GOOGLE_PLACES_API_KEY to enable this feature."
            ),
        )
    return HttpxGooglePlacesService(api_key=settings.GOOGLE_PLACES_API_KEY)


async def get_cached_enrichment(db: AsyncSession, entity_type: str, entity_id: uuid.UUID) -> PlaceEnrichment | None:
    result = await db.execute(
        select(PlaceEnrichment).where(
            PlaceEnrichment.entity_type == entity_type, PlaceEnrichment.entity_id == entity_id
        )
    )
    return result.scalar_one_or_none()


def _build_search_text(name: str, address: str, city: str) -> str:
    return f"{name}, {address}, {city}"


async def sync_place_details(
    db: AsyncSession,
    *,
    entity_type: str,
    entity_id: uuid.UUID,
    search_name: str,
    address: str,
    city: str,
    admin_id: uuid.UUID,
) -> PlaceEnrichment:
    """
    Resolve a place_id from the entity's address (first sync) or reuse
    the cached one (later syncs), fetch fresh details, and upsert the
    cache row. Raises HTTPException on failure so the caller gets a
    clear reason and an EXTERNAL_SYNC_FAILED audit entry is recorded.
    """
    service = _get_places_service()
    existing = await get_cached_enrichment(db, entity_type, entity_id)

    try:
        place_id = existing.place_id if existing else await service.find_place_id(
            _build_search_text(search_name, address, city)
        )
        if not place_id:
            raise GooglePlacesUnavailableError("No matching Google Places result for this address.")

        details = await service.fetch_place_details(place_id)

        photos = (details.get("photos") or [])[: settings.GOOGLE_PLACES_MAX_CACHED_REVIEWS]
        raw_reviews = (details.get("reviews") or [])[: settings.GOOGLE_PLACES_MAX_CACHED_REVIEWS]
        reviews = [
            {"author": r.get("author_name"), "rating": r.get("rating"), "text": r.get("text"), "time": r.get("time")}
            for r in raw_reviews
        ]

        if existing:
            existing.place_id = place_id
            existing.rating = details.get("rating")
            existing.user_ratings_total = details.get("user_ratings_total")
            existing.opening_hours = details.get("opening_hours")
            existing.photos = photos
            existing.reviews = reviews
            existing.last_synced_at = datetime.now(timezone.utc)
            existing.last_sync_status = "SUCCESS"
            existing.last_sync_error = None
            enrichment = existing
        else:
            enrichment = PlaceEnrichment(
                entity_type=entity_type, entity_id=entity_id, place_id=place_id,
                rating=details.get("rating"), user_ratings_total=details.get("user_ratings_total"),
                opening_hours=details.get("opening_hours"), photos=photos, reviews=reviews,
                last_synced_at=datetime.now(timezone.utc), last_sync_status="SUCCESS",
            )
            db.add(enrichment)

        await log_action(
            db, user_id=admin_id, action=AuditAction.EXTERNAL_SYNC_SUCCEEDED, entity_type=entity_type,
            entity_id=entity_id, description=f"Google Places sync succeeded for {entity_type} {entity_id}.",
        )
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Enrichment record conflict — try again.")
        await db.refresh(enrichment)
        return enrichment

    except GooglePlacesUnavailableError as exc:
        await log_action(
            db, user_id=admin_id, action=AuditAction.EXTERNAL_SYNC_FAILED, entity_type=entity_type,
            entity_id=entity_id, description=f"Google Places sync failed: {exc}",
        )
        await db.commit()
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Google Places sync failed: {exc}")
