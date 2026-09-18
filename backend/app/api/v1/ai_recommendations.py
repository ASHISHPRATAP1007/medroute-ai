import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_approved_mr, get_current_user
from app.models.user import User, UserRole
from app.schemas.ai_recommendation import DailyPlanItemOut, OpportunityScoreOut
from app.schemas.common import ApiResponse
from app.schemas.doctor import DoctorOut
from app.services import doctor_service
from app.services.ai_recommendation_service import RuleBasedAIRecommendationService

router = APIRouter(prefix="/ai", tags=["AI Recommendations (Phase 3)"])
_service = RuleBasedAIRecommendationService()


@router.get("/daily-plan", response_model=ApiResponse[list[DailyPlanItemOut]])
async def get_daily_plan(
    limit: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    mr: User = Depends(get_current_approved_mr),
):
    """
    Ranked list of active doctors in the MR's own assigned territory,
    scored by a transparent rule-based formula (see
    app/services/ai_recommendation_service.py). Always territory-
    restricted server-side, same as doctor discovery.
    """
    items = await _service.get_daily_plan(str(mr.id), db, limit=limit)
    return ApiResponse(data=[
        DailyPlanItemOut(doctor=DoctorOut.model_validate(item["doctor"]), score=item["score"], reasons=item["reasons"])
        for item in items
    ])


@router.get("/doctors/{doctor_id}/opportunity-score", response_model=ApiResponse[OpportunityScoreOut])
async def get_doctor_opportunity_score(
    doctor_id: uuid.UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    """Admin gets an unrestricted score; MR only for doctors in their own territory."""
    restrict = None
    if user.role == UserRole.MR:
        restrict = await doctor_service.get_mr_authorized_area_names(db, user.id)
    await doctor_service.get_doctor(db, doctor_id, restrict_to_areas=restrict)  # 404s if unauthorized

    result = await _service.score_doctor(str(doctor_id), str(user.id), db)
    return ApiResponse(data=OpportunityScoreOut(**result))
