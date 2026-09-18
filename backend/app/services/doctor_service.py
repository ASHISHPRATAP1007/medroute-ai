import uuid

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.area import Area
from app.models.audit_log import AuditAction
from app.models.directory_mixins import EntityStatus
from app.models.doctor import Doctor
from app.models.territory import Territory
from app.models.territory_mr import TerritoryMR
from app.schemas.doctor import DoctorCreate, DoctorUpdate
from app.services.audit_service import log_action


async def get_mr_authorized_area_names(db: AsyncSession, mr_id: uuid.UUID) -> list[str]:
    """
    Resolve which Area names an MR is authorized to see, via their
    Territory assignments (Territory -> Area). This is the backend
    enforcement point referenced in spec section 19 — an MR cannot
    widen this by editing query params.
    """
    result = await db.execute(
        select(Area.name)
        .join(Territory, Territory.area_id == Area.id)
        .join(TerritoryMR, TerritoryMR.territory_id == Territory.id)
        .where(TerritoryMR.mr_id == mr_id, Territory.status == "ACTIVE")
        .distinct()
    )
    return [row[0] for row in result.all()]


async def list_doctors(
    db: AsyncSession,
    *,
    search: str | None,
    specialization_id: uuid.UUID | None,
    city: str | None,
    area: str | None,
    status_filter: EntityStatus | None,
    source: str | None,
    page: int,
    page_size: int,
    sort_by: str,
    sort_order: str,
    restrict_to_areas: list[str] | None,
) -> tuple[list[Doctor], int]:
    query = select(Doctor)
    count_query = select(func.count()).select_from(Doctor)

    conditions = []
    if search:
        like = f"%{search}%"
        conditions.append(Doctor.full_name.ilike(like))
    if specialization_id:
        conditions.append(Doctor.specialization_id == specialization_id)
    if city:
        conditions.append(Doctor.city.ilike(city))
    if area:
        conditions.append(Doctor.area.ilike(area))
    if status_filter:
        conditions.append(Doctor.status == status_filter)
    if source:
        conditions.append(Doctor.source == source)

    # Territory enforcement: MR only ever sees doctors within their
    # assigned areas, regardless of what `area`/`city` params they send.
    if restrict_to_areas is not None:
        if len(restrict_to_areas) == 0:
            return [], 0  # MR with no territory assignments sees nothing
        conditions.append(Doctor.area.in_(restrict_to_areas))

    for cond in conditions:
        query = query.where(cond)
        count_query = count_query.where(cond)

    total = (await db.execute(count_query)).scalar_one()

    sort_column = {
        "name": Doctor.full_name,
        "recently_added": Doctor.created_at,
        "specialization": Doctor.specialization_id,
    }.get(sort_by, Doctor.full_name)
    query = query.order_by(sort_column.desc() if sort_order == "desc" else sort_column.asc())

    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    return list(result.scalars().all()), total


async def get_doctor(db: AsyncSession, doctor_id: uuid.UUID, restrict_to_areas: list[str] | None = None) -> Doctor:
    result = await db.execute(select(Doctor).where(Doctor.id == doctor_id))
    doctor = result.scalar_one_or_none()
    if doctor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found.")
    if restrict_to_areas is not None and doctor.area not in restrict_to_areas:
        # Same 404 as "not found" — do not leak existence of out-of-territory records.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found.")
    return doctor


async def create_doctor(db: AsyncSession, payload: DoctorCreate, admin_id: uuid.UUID) -> Doctor:
    doctor = Doctor(**payload.model_dump(), created_by=admin_id, updated_by=admin_id)
    db.add(doctor)
    await db.flush()
    await log_action(
        db, user_id=admin_id, action=AuditAction.DOCTOR_CREATED,
        entity_type="Doctor", entity_id=doctor.id, description=f"Doctor {doctor.full_name} created.",
    )
    await db.commit()
    await db.refresh(doctor)
    return doctor


async def update_doctor(db: AsyncSession, doctor_id: uuid.UUID, payload: DoctorUpdate, admin_id: uuid.UUID) -> Doctor:
    doctor = await get_doctor(db, doctor_id)
    for field, value in payload.model_dump().items():
        setattr(doctor, field, value)
    doctor.updated_by = admin_id
    await log_action(
        db, user_id=admin_id, action=AuditAction.DOCTOR_UPDATED,
        entity_type="Doctor", entity_id=doctor.id, description=f"Doctor {doctor.full_name} updated.",
    )
    await db.commit()
    await db.refresh(doctor)
    return doctor


async def set_doctor_status(db: AsyncSession, doctor_id: uuid.UUID, new_status: EntityStatus, admin_id: uuid.UUID) -> Doctor:
    doctor = await get_doctor(db, doctor_id)
    doctor.status = new_status
    doctor.updated_by = admin_id
    action = AuditAction.DOCTOR_ACTIVATED if new_status == EntityStatus.ACTIVE else AuditAction.DOCTOR_DEACTIVATED
    await log_action(
        db, user_id=admin_id, action=action, entity_type="Doctor", entity_id=doctor.id,
        description=f"Doctor {doctor.full_name} set to {new_status.value}.",
    )
    await db.commit()
    await db.refresh(doctor)
    return doctor
