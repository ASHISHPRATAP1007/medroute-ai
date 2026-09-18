import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_approved_mr, require_admin
from app.models.audit_log import AuditAction
from app.models.directory_mixins import EntityStatus
from app.models.stockist import Stockist
from app.models.user import User
from app.schemas.common import ApiResponse, PaginatedData
from app.schemas.stockist import StockistCreate, StockistOut, StockistUpdate
from app.services import directory_service, doctor_service

router = APIRouter(prefix="/stockists", tags=["Stockists"])


@router.get("", response_model=ApiResponse[PaginatedData[StockistOut]])
async def list_stockists(
    search: str | None = None, city: str | None = None, area: str | None = None, pincode: str | None = None,
    status_filter: EntityStatus | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1), page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db), _admin: User = Depends(require_admin),
):
    items, total = await directory_service.list_entities(
        db, Stockist, search=search, city=city, area=area, pincode=pincode,
        status_filter=status_filter, page=page, page_size=page_size, restrict_to_areas=None,
    )
    total_pages = (total + page_size - 1) // page_size if total else 0
    return ApiResponse(data=PaginatedData(items=[StockistOut.model_validate(i) for i in items],
                        page=page, page_size=page_size, total_items=total, total_pages=total_pages))


@router.get("/mine", response_model=ApiResponse[PaginatedData[StockistOut]])
async def list_stockists_for_mr(
    search: str | None = None, city: str | None = None, area: str | None = None, pincode: str | None = None,
    page: int = Query(default=1, ge=1), page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db), mr: User = Depends(get_current_approved_mr),
):
    restrict = await doctor_service.get_mr_authorized_area_names(db, mr.id)
    items, total = await directory_service.list_entities(
        db, Stockist, search=search, city=city, area=area, pincode=pincode,
        status_filter=EntityStatus.ACTIVE, page=page, page_size=page_size, restrict_to_areas=restrict,
    )
    total_pages = (total + page_size - 1) // page_size if total else 0
    return ApiResponse(data=PaginatedData(items=[StockistOut.model_validate(i) for i in items],
                        page=page, page_size=page_size, total_items=total, total_pages=total_pages))


@router.get("/{stockist_id}", response_model=ApiResponse[StockistOut])
async def get_stockist(stockist_id: uuid.UUID, db: AsyncSession = Depends(get_db), _admin: User = Depends(require_admin)):
    stockist = await directory_service.get_entity(db, Stockist, stockist_id, "Stockist")
    return ApiResponse(data=StockistOut.model_validate(stockist))


@router.post("", response_model=ApiResponse[StockistOut], status_code=201)
async def create_stockist(payload: StockistCreate, db: AsyncSession = Depends(get_db), admin: User = Depends(require_admin)):
    stockist = await directory_service.create_entity(db, Stockist, payload, admin.id, AuditAction.STOCKIST_CREATED, "Stockist")
    return ApiResponse(message="Stockist created.", data=StockistOut.model_validate(stockist))


@router.put("/{stockist_id}", response_model=ApiResponse[StockistOut])
async def update_stockist(stockist_id: uuid.UUID, payload: StockistUpdate, db: AsyncSession = Depends(get_db), admin: User = Depends(require_admin)):
    stockist = await directory_service.update_entity(db, Stockist, stockist_id, payload, admin.id, AuditAction.STOCKIST_UPDATED, "Stockist")
    return ApiResponse(message="Stockist updated.", data=StockistOut.model_validate(stockist))


@router.post("/{stockist_id}/deactivate", response_model=ApiResponse[StockistOut])
async def deactivate_stockist(stockist_id: uuid.UUID, db: AsyncSession = Depends(get_db), admin: User = Depends(require_admin)):
    stockist = await directory_service.deactivate_entity(db, Stockist, stockist_id, admin.id, AuditAction.STOCKIST_DEACTIVATED, "Stockist")
    return ApiResponse(message="Stockist deactivated.", data=StockistOut.model_validate(stockist))
