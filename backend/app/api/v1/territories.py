import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_approved_mr, require_admin
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.territory import (
    AreaCreate, AreaOut, AssignMRRequest, CityCreate, CityOut,
    TerritoryCreate, TerritoryOut, TerritoryUpdate,
)
from app.services import territory_service
from app.services.doctor_service import get_mr_authorized_area_names

router = APIRouter(tags=["Territories"])


@router.post("/cities", response_model=ApiResponse[CityOut], status_code=201)
async def create_city(payload: CityCreate, db: AsyncSession = Depends(get_db), _admin: User = Depends(require_admin)):
    city = await territory_service.create_city(db, payload)
    return ApiResponse(message="City created.", data=CityOut.model_validate(city))


@router.get("/cities", response_model=ApiResponse[list[CityOut]])
async def list_cities(db: AsyncSession = Depends(get_db), _user: User = Depends(require_admin)):
    cities = await territory_service.list_cities(db)
    return ApiResponse(data=[CityOut.model_validate(c) for c in cities])


@router.post("/areas", response_model=ApiResponse[AreaOut], status_code=201)
async def create_area(payload: AreaCreate, db: AsyncSession = Depends(get_db), _admin: User = Depends(require_admin)):
    area = await territory_service.create_area(db, payload)
    return ApiResponse(message="Area created.", data=AreaOut.model_validate(area))


@router.get("/areas", response_model=ApiResponse[list[AreaOut]])
async def list_areas(city_id: uuid.UUID | None = Query(default=None), db: AsyncSession = Depends(get_db), _user: User = Depends(require_admin)):
    areas = await territory_service.list_areas(db, city_id)
    return ApiResponse(data=[AreaOut.model_validate(a) for a in areas])


@router.post("/territories", response_model=ApiResponse[TerritoryOut], status_code=201)
async def create_territory(payload: TerritoryCreate, db: AsyncSession = Depends(get_db), admin: User = Depends(require_admin)):
    territory = await territory_service.create_territory(db, payload, admin.id)
    return ApiResponse(message="Territory created.", data=TerritoryOut.model_validate(territory))


@router.get("/territories", response_model=ApiResponse[list[TerritoryOut]])
async def list_territories(db: AsyncSession = Depends(get_db), _admin: User = Depends(require_admin)):
    territories = await territory_service.list_territories(db)
    return ApiResponse(data=[TerritoryOut.model_validate(t) for t in territories])


@router.get("/territories/mine", response_model=ApiResponse[list[TerritoryOut]])
async def list_my_territories(db: AsyncSession = Depends(get_db), mr: User = Depends(get_current_approved_mr)):
    """MR's own assigned territories, for their dashboard/profile."""
    from sqlalchemy import select
    from app.models.territory import Territory
    from app.models.territory_mr import TerritoryMR

    result = await db.execute(
        select(Territory).join(TerritoryMR, TerritoryMR.territory_id == Territory.id).where(TerritoryMR.mr_id == mr.id)
    )
    territories = list(result.scalars().all())
    return ApiResponse(data=[TerritoryOut.model_validate(t) for t in territories])


@router.put("/territories/{territory_id}", response_model=ApiResponse[TerritoryOut])
async def update_territory(territory_id: uuid.UUID, payload: TerritoryUpdate, db: AsyncSession = Depends(get_db), admin: User = Depends(require_admin)):
    territory = await territory_service.update_territory(db, territory_id, payload, admin.id)
    return ApiResponse(message="Territory updated.", data=TerritoryOut.model_validate(territory))


@router.post("/territories/{territory_id}/assign-mr", response_model=ApiResponse[None])
async def assign_mr(territory_id: uuid.UUID, payload: AssignMRRequest, db: AsyncSession = Depends(get_db), admin: User = Depends(require_admin)):
    await territory_service.assign_mr(db, territory_id, payload.mr_id, admin.id)
    return ApiResponse(message="MR assigned to territory.")


@router.post("/territories/{territory_id}/remove-mr", response_model=ApiResponse[None])
async def remove_mr(territory_id: uuid.UUID, payload: AssignMRRequest, db: AsyncSession = Depends(get_db), admin: User = Depends(require_admin)):
    await territory_service.remove_mr(db, territory_id, payload.mr_id, admin.id)
    return ApiResponse(message="MR removed from territory.")
