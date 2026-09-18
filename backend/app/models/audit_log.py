import enum
import uuid

from sqlalchemy import Enum, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import INET, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class AuditAction(str, enum.Enum):
    USER_REGISTERED = "USER_REGISTERED"
    MR_APPROVED = "MR_APPROVED"
    MR_REJECTED = "MR_REJECTED"
    MR_SUSPENDED = "MR_SUSPENDED"
    MR_ACTIVATED = "MR_ACTIVATED"

    DOCTOR_CREATED = "DOCTOR_CREATED"
    DOCTOR_UPDATED = "DOCTOR_UPDATED"
    DOCTOR_DEACTIVATED = "DOCTOR_DEACTIVATED"
    DOCTOR_ACTIVATED = "DOCTOR_ACTIVATED"

    SHOP_CREATED = "SHOP_CREATED"
    SHOP_UPDATED = "SHOP_UPDATED"
    SHOP_DEACTIVATED = "SHOP_DEACTIVATED"

    STOCKIST_CREATED = "STOCKIST_CREATED"
    STOCKIST_UPDATED = "STOCKIST_UPDATED"
    STOCKIST_DEACTIVATED = "STOCKIST_DEACTIVATED"

    TERRITORY_CREATED = "TERRITORY_CREATED"
    TERRITORY_UPDATED = "TERRITORY_UPDATED"
    MR_ASSIGNED_TO_TERRITORY = "MR_ASSIGNED_TO_TERRITORY"
    MR_REMOVED_FROM_TERRITORY = "MR_REMOVED_FROM_TERRITORY"

    # Phase 2
    EXTERNAL_SYNC_SUCCEEDED = "EXTERNAL_SYNC_SUCCEEDED"
    EXTERNAL_SYNC_FAILED = "EXTERNAL_SYNC_FAILED"

    # Phase 4
    VISIT_PLANNED = "VISIT_PLANNED"
    VISIT_COMPLETED = "VISIT_COMPLETED"
    VISIT_CANCELLED = "VISIT_CANCELLED"


class AuditLog(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_user_id", "user_id"),
        Index("ix_audit_logs_action", "action"),
        Index("ix_audit_logs_entity", "entity_type", "entity_id"),
        Index("ix_audit_logs_created_at", "created_at"),
    )

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    action: Mapped[AuditAction] = mapped_column(Enum(AuditAction, name="audit_action"), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(INET, nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
