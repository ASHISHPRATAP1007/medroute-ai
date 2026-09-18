from sqlalchemy import CheckConstraint, Index, String

from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.directory_mixins import AuditUserMixin, LocationMixin, StatusSourceMixin
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class MedicalShop(Base, UUIDPrimaryKeyMixin, TimestampMixin, LocationMixin, StatusSourceMixin, AuditUserMixin):
    __tablename__ = "medical_shops"
    __table_args__ = (
        CheckConstraint("latitude IS NULL OR (latitude >= -90 AND latitude <= 90)", name="ck_shop_lat_range"),
        CheckConstraint("longitude IS NULL OR (longitude >= -180 AND longitude <= 180)", name="ck_shop_lng_range"),
        Index("ix_shops_name", "name"),
        Index("ix_shops_city", "city"),
        Index("ix_shops_area", "area"),
        Index("ix_shops_status", "status"),
    )

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    contact_person: Mapped[str | None] = mapped_column(String(150), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
