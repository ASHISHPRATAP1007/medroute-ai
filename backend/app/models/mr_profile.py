import uuid

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class MRProfile(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "mr_profiles"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_mr_profiles_user_id"),
        UniqueConstraint("employee_id", "company_name", name="uq_mr_profiles_employee_company"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    company_name: Mapped[str] = mapped_column(String(150), nullable=False)
    employee_id: Mapped[str] = mapped_column(String(50), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(100), nullable=False)
    assigned_area: Mapped[str] = mapped_column(String(150), nullable=False)

    user: Mapped["User"] = relationship(back_populates="mr_profile")
