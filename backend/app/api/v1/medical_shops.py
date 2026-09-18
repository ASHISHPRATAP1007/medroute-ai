import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_approved_mr, require_admin
from app.models.audit_log import AuditAction
from app.models.directory_mixins import EntityStatus
from app.models.medical_shop import MedicalShop
from app.models.user import User
from app.schemas.common import ApiResponse, PaginatedData
from app.schemas.medical_shop import MedicalShopCreate, MedicalShopOut, MedicalShopUpdate
from app.services import directory_service, doctor_service

router = APIRouter(prefix="/medical-shops", tags=["Medical Shops"])


@router.get("", response_model=ApiResponse[PaginatedData[MedicalShopOut]])
async def list_shops(
    search: str | None = None, city: str | None = None, area: str | None = None, pincode: str | None = None,
    status_filter: EntityStatus | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1), page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db), _admin: User = Depends(require_admin),
):
    items, total = await directory_service.list_entities(
        db, MedicalShop, search=search, city=city, area=area, pincode=pincode,
        status_filter=status_filter, page=page, page_size=page_size, restrict_to_areas=None,
    )
    total_pages = (total + page_size - 1) // page_size if total else 0
    return ApiResponse(data=PaginatedData(items=[MedicalShopOut.model_validate(i) for i in items],
                        page=page, page_size=page_size, total_items=total, total_pages=total_pages))


@router.get("/mine", response_model=ApiResponse[PaginatedData[MedicalShopOut]])
async def list_shops_for_mr(
    search: str | None = None, city: str | None = None, area: str | None = None, pincode: str | None = None,
    page: int = Query(default=1, ge=1), page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db), mr: User = Depends(get_current_approved_mr),
):
    restrict = await doctor_service.get_mr_authorized_area_names(db, mr.id)
    items, total = await directory_service.list_entities(
        db, MedicalShop, search=search, city=city, area=area, pincode=pincode,
        status_filter=EntityStatus.ACTIVE, page=page, page_size=page_size, restrict_to_areas=restrict,
    )
    total_pages = (total + page_size - 1) // page_size if total else 0
    return ApiResponse(data=PaginatedData(items=[MedicalShopOut.model_validate(i) for i in items],
                        page=page, page_size=page_size, total_items=total, total_pages=total_pages))


@router.get("/{shop_id}", response_model=ApiResponse[MedicalShopOut])
async def get_shop(shop_id: uuid.UUID, db: AsyncSession = Depends(get_db), _admin: User = Depends(require_admin)):
    shop = await directory_service.get_entity(db, MedicalShop, shop_id, "Medical shop")
    return ApiResponse(data=MedicalShopOut.model_validate(shop))


@router.post("", response_model=ApiResponse[MedicalShopOut], status_code=201)
async def create_shop(payload: MedicalShopCreate, db: AsyncSession = Depends(get_db), admin: User = Depends(require_admin)):
    shop = await directory_service.create_entity(db, MedicalShop, payload, admin.id, AuditAction.SHOP_CREATED, "MedicalShop")
    return ApiResponse(message="Medical shop created.", data=MedicalShopOut.model_validate(shop))


@router.put("/{shop_id}", response_model=ApiResponse[MedicalShopOut])
async def update_shop(shop_id: uuid.UUID, payload: MedicalShopUpdate, db: AsyncSession = Depends(get_db), admin: User = Depends(require_admin)):
    shop = await directory_service.update_entity(db, MedicalShop, shop_id, payload, admin.id, AuditAction.SHOP_UPDATED, "MedicalShop")
    return ApiResponse(message="Medical shop updated.", data=MedicalShopOut.model_validate(shop))


@router.post("/{shop_id}/deactivate", response_model=ApiResponse[MedicalShopOut])
async def deactivate_shop(shop_id: uuid.UUID, db: AsyncSession = Depends(get_db), admin: User = Depends(require_admin)):
    shop = await directory_service.deactivate_entity(db, MedicalShop, shop_id, admin.id, AuditAction.SHOP_DEACTIVATED, "MedicalShop")
    return ApiResponse(message="Medical shop deactivated.", data=MedicalShopOut.model_validate(shop))
