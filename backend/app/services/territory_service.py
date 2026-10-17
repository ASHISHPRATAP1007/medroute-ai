import uuid

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.area import Area
from app.models.audit_log import AuditAction
from app.models.city import City
from app.models.territory import Territory, TerritoryStatus
from app.models.territory_mr import TerritoryMR
from app.models.user import User, UserRole
from app.schemas.territory import AreaCreate, CityCreate, TerritoryCreate, TerritoryUpdate
from app.services.audit_service import log_action


async def create_city(db: AsyncSession, payload: CityCreate) -> City:
    city = City(**payload.model_dump())
    db.add(city)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This city already exists.")
    await db.refresh(city)
    return city


async def list_cities(db: AsyncSession) -> list[City]:
    result = await db.execute(select(City).order_by(City.name))
    return list(result.scalars().all())


async def create_area(db: AsyncSession, payload: AreaCreate) -> Area:
    area = Area(**payload.model_dump())
    db.add(area)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This area already exists in the city.")
    await db.refresh(area)
    return area


async def list_areas(db: AsyncSession, city_id: uuid.UUID | None = None) -> list[Area]:
    query = select(Area).order_by(Area.name)
    if city_id:
        query = query.where(Area.city_id == city_id)
    result = await db.execute(query)
    return list(result.scalars().all())


async def create_territory(db: AsyncSession, payload: TerritoryCreate, admin_id: uuid.UUID) -> Territory:
    territory = Territory(area_id=payload.area_id, name=payload.name, description=payload.description)
    db.add(territory)
    await db.flush()
    await log_action(db, user_id=admin_id, action=AuditAction.TERRITORY_CREATED, entity_type="Territory",
                      entity_id=territory.id, description=f"Territory '{territory.name}' created.")
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This territory already exists in the area.")
    # Re-fetch with mr_links eagerly loaded — AsyncSession cannot lazy-load
    # relationships later during Pydantic serialization.
    return await get_territory(db, territory.id)


async def list_territories(db: AsyncSession) -> list[Territory]:
    result = await db.execute(select(Territory).options(selectinload(Territory.mr_links)).order_by(Territory.name))
    return list(result.scalars().all())


async def get_territory(db: AsyncSession, territory_id: uuid.UUID) -> Territory:
    result = await db.execute(
        select(Territory).options(selectinload(Territory.mr_links)).where(Territory.id == territory_id)
    )
    territory = result.scalar_one_or_none()
    if territory is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Territory not found.")
    return territory


async def update_territory(db: AsyncSession, territory_id: uuid.UUID, payload: TerritoryUpdate, admin_id: uuid.UUID) -> Territory:
    territory = await get_territory(db, territory_id)
    territory.name = payload.name
    territory.description = payload.description
    territory.status = payload.status
    await log_action(db, user_id=admin_id, action=AuditAction.TERRITORY_UPDATED, entity_type="Territory",
                      entity_id=territory.id, description=f"Territory '{territory.name}' updated.")
    await db.commit()
    return await get_territory(db, territory.id)


async def assign_mr(db: AsyncSession, territory_id: uuid.UUID, mr_id: uuid.UUID, admin_id: uuid.UUID) -> TerritoryMR:
    territory = await get_territory(db, territory_id)  # 404s if not found

    mr_result = await db.execute(select(User).where(User.id == mr_id, User.role == UserRole.MR))
    mr = mr_result.scalar_one_or_none()
    if mr is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="MR not found.")

    existing = await db.execute(
        select(TerritoryMR).where(TerritoryMR.territory_id == territory_id, TerritoryMR.mr_id == mr_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="MR is already assigned to this territory.")

    link = TerritoryMR(territory_id=territory_id, mr_id=mr_id, assigned_by=admin_id)
    db.add(link)
    await log_action(db, user_id=admin_id, action=AuditAction.MR_ASSIGNED_TO_TERRITORY, entity_type="Territory",
                      entity_id=territory.id, description=f"MR {mr.email} assigned to territory '{territory.name}'.")
    from app.models.notification import NotificationType
    from app.services.notification_service import create_notification
    await create_notification(
        db, user_id=mr_id, title="New territory assigned",
        message=f"You've been assigned to '{territory.name}'.", type=NotificationType.INFO,
    )
    await db.commit()
    await db.refresh(link)
    return link


async def remove_mr(db: AsyncSession, territory_id: uuid.UUID, mr_id: uuid.UUID, admin_id: uuid.UUID) -> None:
    result = await db.execute(
        select(TerritoryMR).where(TerritoryMR.territory_id == territory_id, TerritoryMR.mr_id == mr_id)
    )
    link = result.scalar_one_or_none()
    if link is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="MR is not assigned to this territory.")
    await db.delete(link)
    await log_action(db, user_id=admin_id, action=AuditAction.MR_REMOVED_FROM_TERRITORY, entity_type="Territory",
                      entity_id=territory_id, description=f"MR removed from territory.")
    await db.commit()


def _clean(value: str | None) -> str:
    return " ".join((value or "").split())


async def auto_assign_from_profile(db: AsyncSession, mr: User, admin_id: uuid.UUID) -> Territory | None:
    """
    On approval, give the MR a territory matching the city/area they entered
    at registration, so they immediately see the doctors, shops and stockists
    of their own area (map + list) without a separate manual step.

    - Skips if the MR already has a territory, or the profile has no area.
    - Reuses an existing City/Area/Territory when names match (case- and
      space-insensitive); otherwise creates them.
    Does NOT commit — the caller's transaction (the approval) does.
    """
    from app.models.area import Area
    from app.models.city import City
    from app.models.mr_profile import MRProfile
    from app.models.notification import NotificationType
    from app.services.notification_service import create_notification

    already = await db.execute(select(TerritoryMR.id).where(TerritoryMR.mr_id == mr.id).limit(1))
    if already.scalar_one_or_none() is not None:
        return None

    profile = (await db.execute(select(MRProfile).where(MRProfile.user_id == mr.id))).scalar_one_or_none()
    if profile is None:
        return None
    city_name, state_name, area_name = _clean(profile.city), _clean(profile.state), _clean(profile.assigned_area)
    if not city_name or not area_name:
        return None

    city = (await db.execute(
        select(City).where(func.lower(City.name) == city_name.lower(), func.lower(City.state) == state_name.lower())
    )).scalars().first()
    if city is None:
        city = City(name=city_name.title(), state=state_name.title() or "-", country="India")
        db.add(city)
        await db.flush()

    area = (await db.execute(
        select(Area).where(Area.city_id == city.id, func.lower(Area.name) == area_name.lower())
    )).scalars().first()
    if area is None:
        area = Area(city_id=city.id, name=area_name.title())
        db.add(area)
        await db.flush()

    territory = (await db.execute(
        select(Territory)
        .where(Territory.area_id == area.id, Territory.status == TerritoryStatus.ACTIVE)
        .order_by(Territory.created_at)
    )).scalars().first()
    if territory is None:
        territory = Territory(
            area_id=area.id, name=f"{area.name} Territory",
            description=f"Auto-created when an MR from {area.name}, {city.name} was approved.",
        )
        db.add(territory)
        await db.flush()
        await log_action(db, user_id=admin_id, action=AuditAction.TERRITORY_CREATED, entity_type="Territory",
                         entity_id=territory.id, description=f"Territory '{territory.name}' auto-created on MR approval.")

    db.add(TerritoryMR(territory_id=territory.id, mr_id=mr.id, assigned_by=admin_id))
    await log_action(db, user_id=admin_id, action=AuditAction.MR_ASSIGNED_TO_TERRITORY, entity_type="Territory",
                     entity_id=territory.id, description=f"MR {mr.email} auto-assigned to '{territory.name}' on approval.")
    await create_notification(
        db, user_id=mr.id, title="Territory assigned",
        message=f"You've been assigned to '{territory.name}' ({area.name}, {city.name}).", type=NotificationType.INFO,
    )
    await db.flush()
    return territory
