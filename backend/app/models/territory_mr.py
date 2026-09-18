import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import UUIDPrimaryKeyMixin


class TerritoryMR(Base, UUIDPrimaryKeyMixin):
    """MR <-> Territory assignment. An MR may hold multiple territories."""
    __tablename__ = "territory_mrs"
    __table_args__ = (UniqueConstraint("territory_id", "mr_id", name="uq_territory_mr"),)

    territory_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("territories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    mr_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    assigned_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    territory: Mapped["Territory"] = relationship(back_populates="mr_links")
