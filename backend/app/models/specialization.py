from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

# Seeded on first migration/seed run — admin can add more later.
DEFAULT_SPECIALIZATIONS = [
    "Cardiologist", "Dermatologist", "Gynecologist", "Orthopedic",
    "Pediatrician", "Neurologist", "General Physician", "ENT Specialist",
    "Dentist", "Ophthalmologist", "Urologist", "Pulmonologist",
    "Gastroenterologist", "Oncologist", "Psychiatrist", "Endocrinologist",
    "Nephrologist", "General Surgeon", "Other",
]


class Specialization(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "specializations"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
