import uuid

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification, NotificationType


async def create_notification(
    db: AsyncSession, *, user_id: uuid.UUID, title: str, message: str, type: NotificationType = NotificationType.INFO
) -> None:
    """
    Adds a Notification WITHOUT committing — same pattern as
    audit_service.log_action, so callers commit as part of their own
    transaction and a notification is never created for an action that
    then fails to commit.
    """
    db.add(Notification(user_id=user_id, title=title, message=message, type=type))


async def list_notifications(db: AsyncSession, user_id: uuid.UUID, unread_only: bool = False) -> list[Notification]:
    query = select(Notification).where(Notification.user_id == user_id)
    if unread_only:
        query = query.where(Notification.is_read == False)  # noqa: E712
    query = query.order_by(Notification.created_at.desc()).limit(50)
    result = await db.execute(query)
    return list(result.scalars().all())


async def count_unread(db: AsyncSession, user_id: uuid.UUID) -> int:
    result = await db.execute(
        select(func.count()).select_from(Notification).where(Notification.user_id == user_id, Notification.is_read == False)  # noqa: E712
    )
    return result.scalar_one()


async def mark_read(db: AsyncSession, notification_id: uuid.UUID, user_id: uuid.UUID) -> Notification:
    result = await db.execute(
        select(Notification).where(Notification.id == notification_id, Notification.user_id == user_id)
    )
    notification = result.scalar_one_or_none()
    if notification is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found.")
    notification.is_read = True
    await db.commit()
    await db.refresh(notification)
    return notification


async def mark_all_read(db: AsyncSession, user_id: uuid.UUID) -> int:
    notifications = await list_notifications(db, user_id, unread_only=True)
    for n in notifications:
        n.is_read = True
    await db.commit()
    return len(notifications)
