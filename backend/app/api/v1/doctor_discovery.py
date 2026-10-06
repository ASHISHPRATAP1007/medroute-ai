from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_admin
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.discovery import DiscoverDoctorsRequest, DiscoveredDoctorOut, ImportDoctorRequest
from app.schemas.doctor import DoctorOut
from app.services import discovery_service

router = APIRouter(prefix="/doctors/discovery", tags=["Doctor Discovery (Google Places)"])


@router.post("/search", response_model=ApiResponse[list[DiscoveredDoctorOut]])
async def search_doctors(payload: DiscoverDoctorsRequest, _admin: User = Depends(require_admin)):
    """
    Real-world doctor search via Google Places — nothing is saved yet.
    Requires GOOGLE_PLACES_ENABLED=true and a valid GOOGLE_PLACES_API_KEY;
    returns 503 with a clear message otherwise.
    """
    candidates = await discovery_service.search_doctors(
        payload.specialization_name, payload.area, payload.city, payload.state
    )
    return ApiResponse(data=[DiscoveredDoctorOut(**c) for c in candidates])


@router.post("/import", response_model=ApiResponse[DoctorOut], status_code=201)
async def import_doctor(
    payload: ImportDoctorRequest, db: AsyncSession = Depends(get_db), admin: User = Depends(require_admin)
):
    """Admin-confirmed import of one discovered doctor into the real directory."""
    doctor = await discovery_service.import_doctor(
        db, place_id=payload.place_id, specialization_id=payload.specialization_id,
        city=payload.city, state=payload.state, area=payload.area, admin_id=admin.id,
    )
    return ApiResponse(message=f"{doctor.full_name} imported successfully.", data=DoctorOut.model_validate(doctor))
