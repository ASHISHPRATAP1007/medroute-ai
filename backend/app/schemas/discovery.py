import uuid

from pydantic import BaseModel, Field


class DiscoverDoctorsRequest(BaseModel):
    specialization_name: str = Field(min_length=2, max_length=100)
    area: str = Field(default="", max_length=150)
    city: str = Field(min_length=2, max_length=100)
    state: str = Field(min_length=2, max_length=100)


class DiscoveredDoctorOut(BaseModel):
    place_id: str
    name: str
    address: str | None
    rating: float | None
    user_ratings_total: int | None
    latitude: float | None
    longitude: float | None
    already_imported: bool = False


class ImportDoctorRequest(BaseModel):
    place_id: str = Field(min_length=3, max_length=255)
    specialization_id: uuid.UUID
    city: str = Field(min_length=2, max_length=100)
    state: str = Field(min_length=2, max_length=100)
    area: str = Field(default="", max_length=150)
