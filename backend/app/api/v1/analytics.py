from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_admin
from app.models.user import User
from app.schemas.analytics import MRPerformanceOut, TerritoryCoverageOut
from app.schemas.common import ApiResponse
from app.services import analytics_service

router = APIRouter(prefix="/admin/analytics", tags=["Admin - Analytics (Phase 5)"])


@router.get("/mr-performance", response_model=ApiResponse[list[MRPerformanceOut]])
async def mr_performance(db: AsyncSession = Depends(get_db), _admin: User = Depends(require_admin)):
    reports = await analytics_service.get_mr_performance(db)
    return ApiResponse(data=reports)


@router.get("/territory-coverage", response_model=ApiResponse[list[TerritoryCoverageOut]])
async def territory_coverage(db: AsyncSession = Depends(get_db), _admin: User = Depends(require_admin)):
    reports = await analytics_service.get_territory_coverage(db)
    return ApiResponse(data=reports)
