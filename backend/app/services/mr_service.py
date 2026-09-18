import uuid

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.audit_log import AuditAction
from app.models.mr_profile import MRProfile
from app.models.notification import NotificationType
from app.models.user import User, UserRole, UserStatus
from app.services.audit_service import log_action
from app.services.notification_service import create_notification


async def list_mrs(
    db: AsyncSession,
    *,
    status_filter: UserStatus | None,
    search: str | None,
    page: int,
    page_size: int,
) -> tuple[list[User], int]:
    query = select(User).options(selectinload(User.mr_profile)).where(User.role == UserRole.MR)
    count_query = select(func.count()).select_from(User).where(User.role == UserRole.MR)

    if status_filter:
        query = query.where(User.status == status_filter)
        count_query = count_query.where(User.status == status_filter)

    if search:
        like = f"%{search}%"
        query = query.where(User.full_name.ilike(like) | User.email.ilike(like) | User.phone.ilike(like))
        count_query = count_query.where(
            User.full_name.ilike(like) | User.email.ilike(like) | User.phone.ilike(like)
        )

    total = (await db.execute(count_query)).scalar_one()

    query = query.order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    return list(result.scalars().all()), total


async def get_mr(db: AsyncSession, mr_id: uuid.UUID) -> User:
    result = await db.execute(
        select(User).options(selectinload(User.mr_profile)).where(User.id == mr_id, User.role == UserRole.MR)
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="MR not found.")
    return user


async def _transition_status(
    db: AsyncSession,
    mr: User,
    new_status: UserStatus,
    action: AuditAction,
    admin_id: uuid.UUID,
    description: str,
) -> User:
    mr.status = new_status
    await log_action(db, user_id=admin_id, action=action, entity_type="User", entity_id=mr.id, description=description)

    notification_copy = {
        UserStatus.APPROVED: ("Account approved", "Your MR account has been approved. You can now log in.", NotificationType.SUCCESS),
        UserStatus.REJECTED: ("Registration rejected", "Your registration was not approved. Contact your administrator for details.", NotificationType.WARNING),
        UserStatus.SUSPENDED: ("Account suspended", "Your account has been suspended. Contact your administrator.", NotificationType.WARNING),
    }.get(new_status)
    if notification_copy:
        title, message, ntype = notification_copy
        await create_notification(db, user_id=mr.id, title=title, message=message, type=ntype)

    await db.commit()
    await db.refresh(mr)
    return mr


async def approve_mr(db: AsyncSession, mr_id: uuid.UUID, admin_id: uuid.UUID) -> User:
    mr = await get_mr(db, mr_id)
    if mr.status == UserStatus.APPROVED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="MR is already approved.")
    return await _transition_status(
        db, mr, UserStatus.APPROVED, AuditAction.MR_APPROVED, admin_id, f"MR {mr.email} approved."
    )


async def reject_mr(db: AsyncSession, mr_id: uuid.UUID, admin_id: uuid.UUID) -> User:
    mr = await get_mr(db, mr_id)
    return await _transition_status(
        db, mr, UserStatus.REJECTED, AuditAction.MR_REJECTED, admin_id, f"MR {mr.email} rejected."
    )


async def suspend_mr(db: AsyncSession, mr_id: uuid.UUID, admin_id: uuid.UUID) -> User:
    mr = await get_mr(db, mr_id)
    return await _transition_status(
        db, mr, UserStatus.SUSPENDED, AuditAction.MR_SUSPENDED, admin_id, f"MR {mr.email} suspended."
    )


async def activate_mr(db: AsyncSession, mr_id: uuid.UUID, admin_id: uuid.UUID) -> User:
    mr = await get_mr(db, mr_id)
    return await _transition_status(
        db, mr, UserStatus.APPROVED, AuditAction.MR_ACTIVATED, admin_id, f"MR {mr.email} reactivated."
    )
