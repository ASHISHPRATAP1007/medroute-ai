from pydantic import BaseModel


class ExplorePlace(BaseModel):
    id: str
    name: str
    category: str
    type_label: str
    speciality: str | None
    address: str | None
    phone: str | None
    opening_hours: str | None
    website: str | None
    latitude: float
    longitude: float
    distance_km: float
    osm_url: str
    google_maps_url: str


class ExploreCenter(BaseModel):
    lat: float
    lng: float
    label: str


class ExploreResult(BaseModel):
    center: ExploreCenter
    radius_km: float
    places: list[ExplorePlace]
