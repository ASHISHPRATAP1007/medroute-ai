"""
Phase 2 — Google Places enrichment cache.

Deliberately polymorphic (entity_type + entity_id) rather than three
separate FK'd tables, mirroring the AuditLog pattern already in the
codebase, since Doctor/MedicalShop/Stockist all need the same shape of
cached data (rating, reviews, hours, photos) and none of it is
authoritative — it's a cache of what Google last returned, refreshed
on demand via POST /{entity}/{id}/sync-external.

We never call Google on every read. Reads always hit this table;
writes only happen from external_data_service.sync_place_details().
"""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, Index, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class PlaceEnrichment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "place_enrichments"
    __table_args__ = (
        UniqueConstraint("entity_type", "entity_id", name="uq_place_enrichment_entity"),
        Index("ix_place_enrichments_entity", "entity_type", "entity_id"),
    )

    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)  # "Doctor" | "MedicalShop" | "Stockist"
    entity_id: Mapped[uuid.UUID] = mapped_column(nullable=False)

    place_id: Mapped[str] = mapped_column(String(255), nullable=False)
    rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    user_ratings_total: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Raw-ish structures straight from Google, kept as JSONB so the shape
    # can evolve without a migration each time Google adds a field.
    opening_hours: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # {"weekday_text": [...], "open_now": bool}
    photos: Mapped[list | None] = mapped_column(JSONB, nullable=True)         # [{"photo_reference": "...", "width":.., "height":..}]
    reviews: Mapped[list | None] = mapped_column(JSONB, nullable=True)        # capped list of {"author", "rating", "text", "time"}

    last_synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_sync_status: Mapped[str] = mapped_column(String(20), nullable=False, default="SUCCESS")  # SUCCESS | FAILED
    last_sync_error: Mapped[str | None] = mapped_column(String(500), nullable=True)
