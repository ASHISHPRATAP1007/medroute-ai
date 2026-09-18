import re
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator, model_validator

from app.models.user import UserRole, UserStatus

INDIAN_MOBILE_RE = re.compile(r"^[6-9]\d{9}$")
STRONG_PASSWORD_RE = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^\w\s]).{8,}$")


class MRRegisterRequest(BaseModel):
    full_name: str
    mobile_number: str
    email: EmailStr
    password: str
    confirm_password: str
    company_name: str
    employee_id: str
    city: str
    state: str
    assigned_area: str

    @field_validator("full_name")
    @classmethod
    def name_not_blank(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Full name is required.")
        return v

    @field_validator("mobile_number")
    @classmethod
    def valid_indian_mobile(cls, v: str) -> str:
        v = v.strip()
        if not INDIAN_MOBILE_RE.match(v):
            raise ValueError("Enter a valid 10-digit Indian mobile number.")
        return v

    @field_validator("password")
    @classmethod
    def strong_password(cls, v: str) -> str:
        if not STRONG_PASSWORD_RE.match(v):
            raise ValueError(
                "Password must be at least 8 characters and include an uppercase letter, "
                "a lowercase letter, a number, and a special character."
            )
        return v

    @field_validator("company_name", "employee_id", "city", "state", "assigned_area")
    @classmethod
    def required_field(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("This field is required.")
        return v

    @model_validator(mode="after")
    def passwords_match(self) -> "MRRegisterRequest":
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match.")
        return self


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    full_name: str
    email: str
    phone: str
    role: UserRole
    status: UserStatus
    last_login_at: datetime | None
    created_at: datetime
