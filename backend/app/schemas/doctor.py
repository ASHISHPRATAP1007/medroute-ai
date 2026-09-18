import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator

from app.models.directory_mixins import EntitySource, EntityStatus

PINCODE_RE = __import__("re").compile(r"^\d{6}$")


class DoctorBase(BaseModel):
    full_name: str
    specialization_id: uuid.UUID
    qualification: str | None = None
    phone: str | None = None
    email: EmailStr | None = None
    clinic_name: str | None = None
    hospital_name: str | None = None
    address: str
    area: str | None = None
    city: str
    state: str
    pincode: str | None = None
    latitude: Decimal | None = None
    longitude: Decimal | None = None

    @field_validator("full_name", "address", "city", "state")
    @classmethod
    def required(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("This field is required.")
        return v

    @field_validator("pincode")
    @classmethod
    def valid_pincode(cls, v: str | None) -> str | None:
        if v and not PINCODE_RE.match(v):
            raise ValueError("Pincode must be a 6-digit number.")
        return v

    @field_validator("latitude")
    @classmethod
    def valid_lat(cls, v: Decimal | None) -> Decimal | None:
        if v is not None and not (Decimal("-90") <= v <= Decimal("90")):
            raise ValueError("Latitude must be between -90 and 90.")
        return v

    @field_validator("longitude")
    @classmethod
    def valid_lng(cls, v: Decimal | None) -> Decimal | None:
        if v is not None and not (Decimal("-180") <= v <= Decimal("180")):
            raise ValueError("Longitude must be between -180 and 180.")
        return v


class DoctorCreate(DoctorBase):
    pass


class DoctorUpdate(DoctorBase):
    pass


class DoctorOut(DoctorBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: EntityStatus
    source: EntitySource
    created_at: datetime
    updated_at: datetime
