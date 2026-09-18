import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_approved_mr
from app.models.doctor import Doctor
from app.models.user import User
from app.models.visit import VisitStatus
from app.schemas.common import ApiResponse
from app.schemas.doctor import DoctorOut
from app.schemas.visit import RouteStopOut, VisitCreate, VisitOut, VisitUpdate
from app.services import visit_service
from app.services.route_optimization_service import NearestNeighborRouteOptimizationService

router = APIRouter(prefix="/visits", tags=["Visits (Phase 4)"])
_route_service = NearestNeighborRouteOptimizationService()


@router.post("", response_model=ApiResponse[VisitOut], status_code=201)
async def plan_visit(payload: VisitCreate, db: AsyncSession = Depends(get_db), mr: User = Depends(get_current_approved_mr)):
    """'Add to Visit Plan' — enabled in Phase 4. Doctor must be in the MR's own territory."""
    visit = await visit_service.create_visit(db, mr.id, payload)
    return ApiResponse(message="Doctor added to your visit plan.", data=VisitOut.model_validate(visit))


@router.get("", response_model=ApiResponse[list[VisitOut]])
async def list_my_visits(
    status_filter: VisitStatus | None = Query(default=None, alias="status"),
    date_from: date | None = None,
    date_to: date | None = None,
    db: AsyncSession = Depends(get_db),
    mr: User = Depends(get_current_approved_mr),
):
    visits = await visit_service.list_visits_for_mr(db, mr.id, status_filter=status_filter, date_from=date_from, date_to=date_to)
    return ApiResponse(data=[VisitOut.model_validate(v) for v in visits])


@router.put("/{visit_id}", response_model=ApiResponse[VisitOut])
async def update_visit(visit_id: uuid.UUID, payload: VisitUpdate, db: AsyncSession = Depends(get_db), mr: User = Depends(get_current_approved_mr)):
    """Mark a planned visit completed/cancelled/missed, with notes/outcome/follow-up. Own visits only — 404 otherwise."""
    visit = await visit_service.update_visit(db, visit_id, mr.id, payload)
    return ApiResponse(message="Visit updated.", data=VisitOut.model_validate(visit))


@router.get("/follow-ups", response_model=ApiResponse[list[VisitOut]])
async def upcoming_follow_ups(db: AsyncSession = Depends(get_db), mr: User = Depends(get_current_approved_mr)):
    visits = await visit_service.get_upcoming_follow_ups(db, mr.id, date.today())
    return ApiResponse(data=[VisitOut.model_validate(v) for v in visits])


@router.get("/daily-route", response_model=ApiResponse[list[RouteStopOut]])
async def daily_route(
    target_date: date = Query(default_factory=date.today),
    db: AsyncSession = Depends(get_db),
    mr: User = Depends(get_current_approved_mr),
):
    """
    Today's (or any date's) planned visits, reordered into an
    efficient nearest-neighbor walk. See route_optimization_pure.py
    for the algorithm — deterministic and independently verified, not
    a black box.
    """
    planned = await visit_service.get_planned_visits_for_date(db, mr.id, target_date)
    if not planned:
        return ApiResponse(data=[])

    doctor_ids = [str(v.doctor_id) for v in planned]
    ordered_ids = await _route_service.optimize_route(str(mr.id), doctor_ids, db)

    from sqlalchemy import select
    doctors_result = await db.execute(select(Doctor).where(Doctor.id.in_([v.doctor_id for v in planned])))
    doctors_by_id = {str(d.id): d for d in doctors_result.scalars().all()}
    visits_by_doctor_id = {str(v.doctor_id): v for v in planned}

    stops = []
    for order, doctor_id in enumerate(ordered_ids, start=1):
        stops.append(RouteStopOut(
            visit=VisitOut.model_validate(visits_by_doctor_id[doctor_id]),
            doctor=DoctorOut.model_validate(doctors_by_id[doctor_id]),
            order=order,
        ))
    return ApiResponse(data=stops)


@router.get("/doctors/{doctor_id}/history", response_model=ApiResponse[list[VisitOut]])
async def doctor_visit_history(doctor_id: uuid.UUID, db: AsyncSession = Depends(get_db), mr: User = Depends(get_current_approved_mr)):
    """The requesting MR's own visit history with this doctor — replaces the Phase 1 'Visit History' placeholder."""
    visits = await visit_service.get_doctor_visit_history(db, mr.id, doctor_id)
    return ApiResponse(data=[VisitOut.model_validate(v) for v in visits])
