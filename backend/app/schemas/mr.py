import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.user import UserRole, UserStatus


class MRProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    company_name: str
    employee_id: str
    city: str
    state: str
    assigned_area: str


class MRListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    full_name: str
    email: str
    phone: str
    role: UserRole
    status: UserStatus
    last_login_at: datetime | None
    created_at: datetime
    mr_profile: MRProfileOut | None
