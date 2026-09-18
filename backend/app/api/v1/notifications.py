import uuid

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.notification import NotificationOut
from app.services import notification_service

router = APIRouter(prefix="/notifications", tags=["Notifications (Phase 5)"])


class UnreadCountOut(BaseModel):
    unread_count: int


@router.get("", response_model=ApiResponse[list[NotificationOut]])
async def list_notifications(
    unread_only: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    notifications = await notification_service.list_notifications(db, user.id, unread_only=unread_only)
    return ApiResponse(data=[NotificationOut.model_validate(n) for n in notifications])


@router.get("/unread-count", response_model=ApiResponse[UnreadCountOut])
async def unread_count(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    count = await notification_service.count_unread(db, user.id)
    return ApiResponse(data=UnreadCountOut(unread_count=count))


@router.post("/{notification_id}/read", response_model=ApiResponse[NotificationOut])
async def mark_read(notification_id: uuid.UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    notification = await notification_service.mark_read(db, notification_id, user.id)
    return ApiResponse(data=NotificationOut.model_validate(notification))


@router.post("/read-all", response_model=ApiResponse[None])
async def mark_all_read(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    count = await notification_service.mark_all_read(db, user.id)
    return ApiResponse(message=f"Marked {count} notification(s) as read.")
