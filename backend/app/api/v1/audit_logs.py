import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_admin
from app.models.audit_log import AuditAction, AuditLog
from app.models.user import User
from app.schemas.common import ApiResponse, PaginatedData

router = APIRouter(prefix="/admin/audit-logs", tags=["Admin - Audit Logs"])


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    user_id: uuid.UUID | None
    action: AuditAction
    entity_type: str
    entity_id: uuid.UUID | None
    description: str | None
    created_at: datetime


@router.get("", response_model=ApiResponse[PaginatedData[AuditLogOut]])
async def list_audit_logs(
    action: AuditAction | None = None,
    user_id: uuid.UUID | None = None,
    entity_type: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    query = select(AuditLog)
    count_query = select(func.count()).select_from(AuditLog)

    conditions = []
    if action:
        conditions.append(AuditLog.action == action)
    if user_id:
        conditions.append(AuditLog.user_id == user_id)
    if entity_type:
        conditions.append(AuditLog.entity_type == entity_type)
    if date_from:
        conditions.append(AuditLog.created_at >= date_from)
    if date_to:
        conditions.append(AuditLog.created_at <= date_to)

    for c in conditions:
        query = query.where(c)
        count_query = count_query.where(c)

    total = (await db.execute(count_query)).scalar_one()
    query = query.order_by(AuditLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = list(result.scalars().all())
    total_pages = (total + page_size - 1) // page_size if total else 0

    return ApiResponse(data=PaginatedData(
        items=[AuditLogOut.model_validate(i) for i in items], page=page, page_size=page_size,
        total_items=total, total_pages=total_pages,
    ))
