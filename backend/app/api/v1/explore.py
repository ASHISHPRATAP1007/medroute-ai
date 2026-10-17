from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.api.v1.auth import limiter
from app.core.config import get_settings
from app.core.dependencies import get_current_user
from app.models.user import User, UserRole, UserStatus
from app.schemas.common import ApiResponse
from app.schemas.explore import ExploreResult
from app.services import explore_service

router = APIRouter(prefix="/explore", tags=["Explore (free, OpenStreetMap)"])
settings = get_settings()


@router.get("/places", response_model=ApiResponse[ExploreResult])
@limiter.limit(settings.EXPLORE_RATE_LIMIT)
async def explore_places(
    request: Request,
    category: Literal["doctor", "hospital", "pharmacy", "distributor"] = "doctor",
    location: str | None = Query(default=None, max_length=200, description="Any place, e.g. 'Gomti Nagar, Lucknow'"),
    lat: float | None = Query(default=None, ge=-90, le=90),
    lng: float | None = Query(default=None, ge=-180, le=180),
    radius_km: float = Query(default=5, ge=0.5, le=15),
    keyword: str | None = Query(default=None, max_length=100, description="Filter by name or speciality"),
    user: User = Depends(get_current_user),
):
    """
    Doctors, hospitals, medical stores or suppliers around ANY place (typed, or
    the user's GPS position) — from OpenStreetMap, free. Not limited to the
    MR's territory: it's public map data, not the company directory.
    """
    if user.role == UserRole.MR and user.status != UserStatus.APPROVED:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Your MR account is not yet approved.")
    result = await explore_service.explore(
        category=category, location=location, lat=lat, lng=lng, radius_km=radius_km, keyword=keyword
    )
    return ApiResponse(data=ExploreResult(**result))
