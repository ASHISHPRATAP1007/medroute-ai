import uuid

from sqlalchemy import CheckConstraint, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.directory_mixins import AuditUserMixin, LocationMixin, StatusSourceMixin
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Doctor(Base, UUIDPrimaryKeyMixin, TimestampMixin, LocationMixin, StatusSourceMixin, AuditUserMixin):
    __tablename__ = "doctors"
    __table_args__ = (
        CheckConstraint("latitude IS NULL OR (latitude >= -90 AND latitude <= 90)", name="ck_doctor_lat_range"),
        CheckConstraint("longitude IS NULL OR (longitude >= -180 AND longitude <= 180)", name="ck_doctor_lng_range"),
        Index("ix_doctors_full_name", "full_name"),
        Index("ix_doctors_city", "city"),
        Index("ix_doctors_area", "area"),
        Index("ix_doctors_status", "status"),
        Index("ix_doctors_specialization_id", "specialization_id"),
    )

    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    specialization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("specializations.id", ondelete="RESTRICT"), nullable=False
    )
    qualification: Mapped[str | None] = mapped_column(String(150), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    clinic_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    hospital_name: Mapped[str | None] = mapped_column(String(200), nullable=True)

    specialization: Mapped["Specialization"] = relationship()
