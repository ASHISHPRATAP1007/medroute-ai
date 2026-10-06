import uuid

from pydantic import BaseModel


class DiscoverDoctorsRequest(BaseModel):
    specialization_name: str
    area: str
    city: str
    state: str


class DiscoveredDoctorOut(BaseModel):
    place_id: str
    name: str
    address: str | None
    rating: float | None
    user_ratings_total: int | None
    latitude: float | None
    longitude: float | None


class ImportDoctorRequest(BaseModel):
    place_id: str
    specialization_id: uuid.UUID
    city: str
    state: str
    area: str
