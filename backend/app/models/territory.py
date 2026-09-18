import enum
import uuid

from sqlalchemy import Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class TerritoryStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class Territory(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "territories"
    __table_args__ = (UniqueConstraint("area_id", "name", name="uq_territory_area_name"),)

    area_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("areas.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[TerritoryStatus] = mapped_column(
        Enum(TerritoryStatus, name="territory_status"), default=TerritoryStatus.ACTIVE, nullable=False
    )

    mr_links: Mapped[list["TerritoryMR"]] = relationship(
        back_populates="territory", cascade="all, delete-orphan"
    )
