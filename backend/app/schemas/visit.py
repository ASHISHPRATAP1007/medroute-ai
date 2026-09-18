import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models.visit import VisitStatus
from app.schemas.doctor import DoctorOut


class VisitCreate(BaseModel):
    doctor_id: uuid.UUID
    scheduled_date: date


class VisitUpdate(BaseModel):
    status: VisitStatus
    notes: str | None = None
    outcome: str | None = None
    follow_up_date: date | None = None


class VisitOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    doctor_id: uuid.UUID
    scheduled_date: date
    status: VisitStatus
    notes: str | None
    outcome: str | None
    follow_up_date: date | None
    created_at: datetime


class VisitWithDoctorOut(VisitOut):
    doctor: DoctorOut


class RouteStopOut(BaseModel):
    visit: VisitOut
    doctor: DoctorOut
    order: int
