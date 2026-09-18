from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_approved_mr, require_admin
from app.models.directory_mixins import EntityStatus
from app.models.doctor import Doctor
from app.models.medical_shop import MedicalShop
from app.models.stockist import Stockist
from app.models.territory import Territory
from app.models.territory_mr import TerritoryMR
from app.models.user import User, UserRole, UserStatus
from app.schemas.common import ApiResponse
from app.schemas.mr import MRListItem
from app.services.doctor_service import get_mr_authorized_area_names

router = APIRouter(tags=["Dashboard"])


class AdminDashboardOut(BaseModel):
    total_mrs: int
    pending_mrs: int
    approved_mrs: int
    total_doctors: int
    active_doctors: int
    medical_shops: int
    stockists: int
    territories: int
    recent_pending_mrs: list[MRListItem]


class MRDashboardOut(BaseModel):
    full_name: str
    assigned_territory_count: int
    total_doctors: int
    total_medical_shops: int
    total_stockists: int


async def _count(db: AsyncSession, model, *conditions) -> int:
    query = select(func.count()).select_from(model)
    for c in conditions:
        query = query.where(c)
    return (await db.execute(query)).scalar_one()


@router.get("/admin/dashboard", response_model=ApiResponse[AdminDashboardOut])
async def admin_dashboard(db: AsyncSession = Depends(get_db), _admin: User = Depends(require_admin)):
    total_mrs = await _count(db, User, User.role == UserRole.MR)
    pending_mrs = await _count(db, User, User.role == UserRole.MR, User.status == UserStatus.PENDING)
    approved_mrs = await _count(db, User, User.role == UserRole.MR, User.status == UserStatus.APPROVED)
    total_doctors = await _count(db, Doctor)
    active_doctors = await _count(db, Doctor, Doctor.status == EntityStatus.ACTIVE)
    shops = await _count(db, MedicalShop)
    stockists = await _count(db, Stockist)
    territories = await _count(db, Territory)

    recent = await db.execute(
        select(User).where(User.role == UserRole.MR, User.status == UserStatus.PENDING)
        .order_by(User.created_at.desc()).limit(5)
    )

    return ApiResponse(data=AdminDashboardOut(
        total_mrs=total_mrs, pending_mrs=pending_mrs, approved_mrs=approved_mrs,
        total_doctors=total_doctors, active_doctors=active_doctors,
        medical_shops=shops, stockists=stockists, territories=territories,
        recent_pending_mrs=[MRListItem.model_validate(u) for u in recent.scalars().all()],
    ))


@router.get("/mr/dashboard", response_model=ApiResponse[MRDashboardOut])
async def mr_dashboard(db: AsyncSession = Depends(get_db), mr: User = Depends(get_current_approved_mr)):
    territory_count = await _count(db, TerritoryMR, TerritoryMR.mr_id == mr.id)
    areas = await get_mr_authorized_area_names(db, mr.id)

    if areas:
        doctors = await _count(db, Doctor, Doctor.area.in_(areas), Doctor.status == EntityStatus.ACTIVE)
        shops = await _count(db, MedicalShop, MedicalShop.area.in_(areas), MedicalShop.status == EntityStatus.ACTIVE)
        stockists = await _count(db, Stockist, Stockist.area.in_(areas), Stockist.status == EntityStatus.ACTIVE)
    else:
        doctors = shops = stockists = 0

    return ApiResponse(data=MRDashboardOut(
        full_name=mr.full_name, assigned_territory_count=territory_count,
        total_doctors=doctors, total_medical_shops=shops, total_stockists=stockists,
    ))
