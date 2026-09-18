from app.schemas.doctor import DoctorOut
from pydantic import BaseModel


class OpportunityScoreOut(BaseModel):
    score: int
    reasons: list[str]


class DailyPlanItemOut(BaseModel):
    doctor: DoctorOut
    score: int
    reasons: list[str]
