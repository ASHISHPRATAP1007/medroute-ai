import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PlaceEnrichmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    place_id: str
    rating: float | None
    user_ratings_total: int | None
    opening_hours: dict | None
    photos: list | None
    reviews: list | None
    last_synced_at: datetime
    last_sync_status: str
    last_sync_error: str | None
