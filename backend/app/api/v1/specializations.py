import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.specialization import Specialization
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/specializations", tags=["Specializations"])


class SpecializationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    is_active: bool


@router.get("", response_model=ApiResponse[list[SpecializationOut]])
async def list_specializations(db: AsyncSession = Depends(get_db), _user=Depends(get_current_user)):
    result = await db.execute(select(Specialization).where(Specialization.is_active == True).order_by(Specialization.name))  # noqa: E712
    return ApiResponse(data=[SpecializationOut.model_validate(s) for s in result.scalars().all()])
