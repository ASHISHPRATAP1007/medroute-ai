import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

from app.models.territory import TerritoryStatus


class CityCreate(BaseModel):
    name: str
    state: str
    country: str = "India"

    @field_validator("name", "state")
    @classmethod
    def required(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("This field is required.")
        return v


class CityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    state: str
    country: str


class AreaCreate(BaseModel):
    city_id: uuid.UUID
    name: str
    pincode: str | None = None

    @field_validator("name")
    @classmethod
    def required(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("This field is required.")
        return v


class AreaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    city_id: uuid.UUID
    name: str
    pincode: str | None


class TerritoryCreate(BaseModel):
    area_id: uuid.UUID
    name: str
    description: str | None = None

    @field_validator("name")
    @classmethod
    def required(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("This field is required.")
        return v


class TerritoryUpdate(BaseModel):
    name: str
    description: str | None = None
    status: TerritoryStatus


class TerritoryMRLinkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    mr_id: uuid.UUID


class TerritoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    area_id: uuid.UUID
    name: str
    description: str | None
    status: TerritoryStatus
    created_at: datetime
    mr_links: list[TerritoryMRLinkOut] = []


class AssignMRRequest(BaseModel):
    mr_id: uuid.UUID
