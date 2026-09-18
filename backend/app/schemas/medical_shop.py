import re
import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator

from app.models.directory_mixins import EntitySource, EntityStatus

PINCODE_RE = re.compile(r"^\d{6}$")


class MedicalShopBase(BaseModel):
    name: str
    contact_person: str | None = None
    phone: str | None = None
    email: EmailStr | None = None
    address: str
    area: str | None = None
    city: str
    state: str
    pincode: str | None = None
    latitude: Decimal | None = None
    longitude: Decimal | None = None

    @field_validator("name", "address", "city", "state")
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


class MedicalShopCreate(MedicalShopBase):
    pass


class MedicalShopUpdate(MedicalShopBase):
    pass


class MedicalShopOut(MedicalShopBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    status: EntityStatus
    source: EntitySource
    created_at: datetime
    updated_at: datetime
