"""
Generic search/CRUD logic shared by MedicalShop and Stockist — both
entities have an identical shape (name/address/city/area/status) so a
single parameterized service avoids duplicating the same code twice,
per project rule #6 (avoid duplicated code).
"""
import uuid
from typing import Type, TypeVar

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditAction
from app.models.directory_mixins import EntityStatus
from app.services.audit_service import log_action

ModelT = TypeVar("ModelT")


async def list_entities(
    db: AsyncSession,
    model: Type[ModelT],
    *,
    search: str | None,
    city: str | None,
    area: str | None,
    pincode: str | None,
    status_filter: EntityStatus | None,
    page: int,
    page_size: int,
    restrict_to_areas: list[str] | None,
) -> tuple[list[ModelT], int]:
    query = select(model)
    count_query = select(func.count()).select_from(model)

    conditions = []
    if search:
        conditions.append(model.name.ilike(f"%{search}%"))
    if city:
        conditions.append(model.city.ilike(city))
    if area:
        conditions.append(model.area.ilike(area))
    if pincode:
        conditions.append(model.pincode == pincode)
    if status_filter:
        conditions.append(model.status == status_filter)
    if restrict_to_areas is not None:
        if len(restrict_to_areas) == 0:
            return [], 0
        conditions.append(model.area.in_(restrict_to_areas))

    for cond in conditions:
        query = query.where(cond)
        count_query = count_query.where(cond)

    total = (await db.execute(count_query)).scalar_one()
    query = query.order_by(model.name.asc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    return list(result.scalars().all()), total


async def get_entity(db: AsyncSession, model: Type[ModelT], entity_id: uuid.UUID, entity_label: str,
                      restrict_to_areas: list[str] | None = None) -> ModelT:
    result = await db.execute(select(model).where(model.id == entity_id))
    entity = result.scalar_one_or_none()
    if entity is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{entity_label} not found.")
    if restrict_to_areas is not None and entity.area not in restrict_to_areas:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{entity_label} not found.")
    return entity


async def create_entity(db: AsyncSession, model: Type[ModelT], payload, admin_id: uuid.UUID,
                         created_action: AuditAction, entity_label: str) -> ModelT:
    entity = model(**payload.model_dump(), created_by=admin_id, updated_by=admin_id)
    db.add(entity)
    await db.flush()
    await log_action(db, user_id=admin_id, action=created_action, entity_type=entity_label,
                      entity_id=entity.id, description=f"{entity_label} '{entity.name}' created.")
    await db.commit()
    await db.refresh(entity)
    return entity


async def update_entity(db: AsyncSession, model: Type[ModelT], entity_id: uuid.UUID, payload, admin_id: uuid.UUID,
                         updated_action: AuditAction, entity_label: str) -> ModelT:
    entity = await get_entity(db, model, entity_id, entity_label)
    for field, value in payload.model_dump().items():
        setattr(entity, field, value)
    entity.updated_by = admin_id
    await log_action(db, user_id=admin_id, action=updated_action, entity_type=entity_label,
                      entity_id=entity.id, description=f"{entity_label} '{entity.name}' updated.")
    await db.commit()
    await db.refresh(entity)
    return entity


async def deactivate_entity(db: AsyncSession, model: Type[ModelT], entity_id: uuid.UUID, admin_id: uuid.UUID,
                             deactivated_action: AuditAction, entity_label: str) -> ModelT:
    entity = await get_entity(db, model, entity_id, entity_label)
    entity.status = EntityStatus.INACTIVE
    entity.updated_by = admin_id
    await log_action(db, user_id=admin_id, action=deactivated_action, entity_type=entity_label,
                      entity_id=entity.id, description=f"{entity_label} '{entity.name}' deactivated.")
    await db.commit()
    await db.refresh(entity)
    return entity
