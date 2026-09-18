from sqlalchemy import CheckConstraint, Index, String

from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.directory_mixins import AuditUserMixin, LocationMixin, StatusSourceMixin
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Stockist(Base, UUIDPrimaryKeyMixin, TimestampMixin, LocationMixin, StatusSourceMixin, AuditUserMixin):
    __tablename__ = "stockists"
    __table_args__ = (
        CheckConstraint("latitude IS NULL OR (latitude >= -90 AND latitude <= 90)", name="ck_stockist_lat_range"),
        CheckConstraint("longitude IS NULL OR (longitude >= -180 AND longitude <= 180)", name="ck_stockist_lng_range"),
        Index("ix_stockists_name", "name"),
        Index("ix_stockists_city", "city"),
        Index("ix_stockists_area", "area"),
        Index("ix_stockists_status", "status"),
    )

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    company_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    contact_person: Mapped[str | None] = mapped_column(String(150), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    coverage_area: Mapped[str | None] = mapped_column(String(255), nullable=True)
