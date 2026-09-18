import uuid
from datetime import date

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditAction
from app.models.doctor import Doctor
from app.models.visit import Visit, VisitStatus
from app.services import doctor_service
from app.services.audit_service import log_action


async def _assert_doctor_in_mr_territory(db: AsyncSession, mr_id: uuid.UUID, doctor_id: uuid.UUID) -> Doctor:
    restrict = await doctor_service.get_mr_authorized_area_names(db, mr_id)
    return await doctor_service.get_doctor(db, doctor_id, restrict_to_areas=restrict)  # 404s if unauthorized


async def create_visit(db: AsyncSession, mr_id: uuid.UUID, payload) -> Visit:
    await _assert_doctor_in_mr_territory(db, mr_id, payload.doctor_id)

    visit = Visit(mr_id=mr_id, doctor_id=payload.doctor_id, scheduled_date=payload.scheduled_date)
    db.add(visit)
    await db.flush()
    await log_action(
        db, user_id=mr_id, action=AuditAction.VISIT_PLANNED, entity_type="Visit", entity_id=visit.id,
        description=f"Visit planned for doctor {payload.doctor_id} on {payload.scheduled_date}.",
    )
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This doctor is already on your visit plan for that date.",
        )
    await db.refresh(visit)
    return visit


async def get_own_visit(db: AsyncSession, visit_id: uuid.UUID, mr_id: uuid.UUID) -> Visit:
    result = await db.execute(select(Visit).where(Visit.id == visit_id, Visit.mr_id == mr_id))
    visit = result.scalar_one_or_none()
    if visit is None:
        # Same 404-not-403 pattern as doctor territory checks — don't
        # confirm whether a visit ID exists at all if it isn't the
        # caller's own.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visit not found.")
    return visit


async def update_visit(db: AsyncSession, visit_id: uuid.UUID, mr_id: uuid.UUID, payload) -> Visit:
    visit = await get_own_visit(db, visit_id, mr_id)
    visit.status = payload.status
    visit.notes = payload.notes
    visit.outcome = payload.outcome
    visit.follow_up_date = payload.follow_up_date

    action = {
        VisitStatus.COMPLETED: AuditAction.VISIT_COMPLETED,
        VisitStatus.CANCELLED: AuditAction.VISIT_CANCELLED,
    }.get(payload.status)
    if action:
        await log_action(db, user_id=mr_id, action=action, entity_type="Visit", entity_id=visit.id,
                          description=f"Visit {visit_id} marked {payload.status.value}.")

    await db.commit()
    await db.refresh(visit)
    return visit


async def list_visits_for_mr(
    db: AsyncSession, mr_id: uuid.UUID, *, status_filter: VisitStatus | None,
    date_from: date | None, date_to: date | None,
) -> list[Visit]:
    query = select(Visit).where(Visit.mr_id == mr_id)
    if status_filter:
        query = query.where(Visit.status == status_filter)
    if date_from:
        query = query.where(Visit.scheduled_date >= date_from)
    if date_to:
        query = query.where(Visit.scheduled_date <= date_to)
    query = query.order_by(Visit.scheduled_date.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_doctor_visit_history(db: AsyncSession, mr_id: uuid.UUID, doctor_id: uuid.UUID) -> list[Visit]:
    """An MR's own visit history with one specific doctor — never another MR's visits."""
    result = await db.execute(
        select(Visit).where(Visit.mr_id == mr_id, Visit.doctor_id == doctor_id).order_by(Visit.scheduled_date.desc())
    )
    return list(result.scalars().all())


async def get_upcoming_follow_ups(db: AsyncSession, mr_id: uuid.UUID, today: date) -> list[Visit]:
    result = await db.execute(
        select(Visit)
        .where(Visit.mr_id == mr_id, Visit.follow_up_date.is_not(None), Visit.follow_up_date >= today)
        .order_by(Visit.follow_up_date.asc())
    )
    return list(result.scalars().all())


async def get_planned_visits_for_date(db: AsyncSession, mr_id: uuid.UUID, target_date: date) -> list[Visit]:
    result = await db.execute(
        select(Visit).where(
            Visit.mr_id == mr_id, Visit.scheduled_date == target_date, Visit.status == VisitStatus.PLANNED
        )
    )
    return list(result.scalars().all())
