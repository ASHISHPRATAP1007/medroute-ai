import uuid

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Area(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "areas"
    __table_args__ = (UniqueConstraint("city_id", "name", name="uq_area_city_name"),)

    city_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    pincode: Mapped[str | None] = mapped_column(String(10), nullable=True)
