from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User, UserRole, UserStatus
from app.schemas.auth import UserPublic
from app.schemas.common import ApiResponse
from app.schemas.doctor import DoctorOut
from app.schemas.medical_shop import MedicalShopOut
from app.schemas.search import GlobalSearchOut
from app.schemas.stockist import StockistOut
from app.services import search_service

router = APIRouter(prefix="/search", tags=["Global Search"])


@router.get("", response_model=ApiResponse[GlobalSearchOut])
async def global_search(
    q: str = Query(min_length=2, max_length=100),
    limit: int = Query(default=5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Grouped search across doctors, medical shops, stockists (and MRs, for admins)."""
    if user.role == UserRole.MR and user.status != UserStatus.APPROVED:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Your MR account is not yet approved.")
    found = await search_service.global_search(db, user, q, limit)
    return ApiResponse(data=GlobalSearchOut(
        doctors=[DoctorOut.model_validate(d) for d in found["doctors"]],
        medical_shops=[MedicalShopOut.model_validate(s) for s in found["medical_shops"]],
        stockists=[StockistOut.model_validate(s) for s in found["stockists"]],
        mrs=[UserPublic.model_validate(u) for u in found["mrs"]],
    ))
