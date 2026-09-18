import enum
import uuid
from datetime import date

from sqlalchemy import Date, Enum, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class VisitStatus(str, enum.Enum):
    PLANNED = "PLANNED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    MISSED = "MISSED"


class Visit(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "visits"
    __table_args__ = (
        # One planned visit per MR/doctor/day — prevents accidental double-booking
        # from the "Add to Visit Plan" button being tapped twice.
        UniqueConstraint("mr_id", "doctor_id", "scheduled_date", name="uq_visit_mr_doctor_date"),
        Index("ix_visits_mr_id", "mr_id"),
        Index("ix_visits_doctor_id", "doctor_id"),
        Index("ix_visits_scheduled_date", "scheduled_date"),
        Index("ix_visits_status", "status"),
        Index("ix_visits_follow_up_date", "follow_up_date"),
    )

    mr_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    doctor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False
    )
    scheduled_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[VisitStatus] = mapped_column(
        Enum(VisitStatus, name="visit_status"), nullable=False, default=VisitStatus.PLANNED
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    outcome: Mapped[str | None] = mapped_column(Text, nullable=True)
    follow_up_date: Mapped[date | None] = mapped_column(Date, nullable=True)
