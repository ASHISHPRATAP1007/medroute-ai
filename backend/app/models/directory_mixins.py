"""
Shared field groups for the three "field directory" entities:
Doctor, MedicalShop, Stockist. They all share address/location fields,
an ACTIVE/INACTIVE status, a source (ADMIN/IMPORT/EXTERNAL), and
created_by/updated_by audit trails, plus fields reserved for the
Phase 2 external-data (Google Places) integration.
"""
import enum
import uuid
from decimal import Decimal

from sqlalchemy import Enum, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column


class EntityStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class EntitySource(str, enum.Enum):
    ADMIN = "ADMIN"
    IMPORT = "IMPORT"
    EXTERNAL = "EXTERNAL"  # reserved for Phase 2 — not populated in Phase 1


class LocationMixin:
    address: Mapped[str] = mapped_column(String(500), nullable=False)
    area: Mapped[str | None] = mapped_column(String(150), nullable=True)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(100), nullable=False)
    pincode: Mapped[str | None] = mapped_column(String(10), nullable=True)
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6), nullable=True)
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6), nullable=True)


class StatusSourceMixin:
    status: Mapped[EntityStatus] = mapped_column(
        Enum(EntityStatus, name="entity_status"), default=EntityStatus.ACTIVE, nullable=False
    )
    source: Mapped[EntitySource] = mapped_column(
        Enum(EntitySource, name="entity_source"), default=EntitySource.ADMIN, nullable=False
    )
    # Phase 2 placeholders — never called/populated in Phase 1.
    external_provider: Mapped[str | None] = mapped_column(String(50), nullable=True)
    external_place_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_external_sync: Mapped[str | None] = mapped_column(String(50), nullable=True)


class AuditUserMixin:
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
