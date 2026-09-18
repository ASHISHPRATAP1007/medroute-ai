from sqlalchemy import String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class City(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "cities"
    __table_args__ = (UniqueConstraint("name", "state", "country", name="uq_city_name_state_country"),)

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(100), nullable=False)
    country: Mapped[str] = mapped_column(String(100), nullable=False, default="India")
