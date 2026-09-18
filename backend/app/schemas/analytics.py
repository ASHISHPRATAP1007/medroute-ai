import uuid
from datetime import date

from pydantic import BaseModel


class MRPerformanceOut(BaseModel):
    mr_id: uuid.UUID
    full_name: str
    visits_planned: int
    visits_completed: int
    visits_cancelled: int
    visits_missed: int
    completion_rate: float  # 0.0 - 1.0
    doctors_covered: int
    last_visit_date: date | None


class TerritoryCoverageOut(BaseModel):
    territory_id: uuid.UUID
    territory_name: str
    total_active_doctors: int
    doctors_visited: int
    coverage_percent: float  # 0.0 - 100.0
