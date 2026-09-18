import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_admin
from app.models.user import User, UserStatus
from app.schemas.common import ApiResponse, PaginatedData
from app.schemas.mr import MRListItem
from app.services import mr_service

router = APIRouter(prefix="/admin/mrs", tags=["Admin - MR Management"])


@router.get("", response_model=ApiResponse[PaginatedData[MRListItem]])
async def list_mrs(
    status_filter: UserStatus | None = Query(default=None, alias="status"),
    search: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    items, total = await mr_service.list_mrs(
        db, status_filter=status_filter, search=search, page=page, page_size=page_size
    )
    total_pages = (total + page_size - 1) // page_size if total else 0
    return ApiResponse(
        data=PaginatedData(
            items=[MRListItem.model_validate(i) for i in items],
            page=page,
            page_size=page_size,
            total_items=total,
            total_pages=total_pages,
        )
    )


@router.get("/{mr_id}", response_model=ApiResponse[MRListItem])
async def get_mr(mr_id: uuid.UUID, db: AsyncSession = Depends(get_db), _admin: User = Depends(require_admin)):
    mr = await mr_service.get_mr(db, mr_id)
    return ApiResponse(data=MRListItem.model_validate(mr))


@router.post("/{mr_id}/approve", response_model=ApiResponse[MRListItem])
async def approve_mr(mr_id: uuid.UUID, db: AsyncSession = Depends(get_db), admin: User = Depends(require_admin)):
    mr = await mr_service.approve_mr(db, mr_id, admin.id)
    return ApiResponse(message="MR approved.", data=MRListItem.model_validate(mr))


@router.post("/{mr_id}/reject", response_model=ApiResponse[MRListItem])
async def reject_mr(mr_id: uuid.UUID, db: AsyncSession = Depends(get_db), admin: User = Depends(require_admin)):
    mr = await mr_service.reject_mr(db, mr_id, admin.id)
    return ApiResponse(message="MR rejected.", data=MRListItem.model_validate(mr))


@router.post("/{mr_id}/suspend", response_model=ApiResponse[MRListItem])
async def suspend_mr(mr_id: uuid.UUID, db: AsyncSession = Depends(get_db), admin: User = Depends(require_admin)):
    mr = await mr_service.suspend_mr(db, mr_id, admin.id)
    return ApiResponse(message="MR suspended.", data=MRListItem.model_validate(mr))


@router.post("/{mr_id}/activate", response_model=ApiResponse[MRListItem])
async def activate_mr(mr_id: uuid.UUID, db: AsyncSession = Depends(get_db), admin: User = Depends(require_admin)):
    mr = await mr_service.activate_mr(db, mr_id, admin.id)
    return ApiResponse(message="MR activated.", data=MRListItem.model_validate(mr))
