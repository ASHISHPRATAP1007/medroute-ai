"""
Phase 3 — rule-based AI recommendation engine.

Design note on "AI": this is a deterministic, explainable scoring
function over real signals already in the database — not a call to an
external LLM. Two reasons: (1) this environment has no network access
to call any external AI API, and (2) a transparent scoring formula is
arguably the right choice anyway for a "why this doctor?" feature that
field reps need to trust and act on — a black-box score with no
reasoning would be worse for adoption than a clear one.

Signals used (all real, nothing fabricated):
  - Google rating + review count, IF this doctor has been synced via
    Phase 2 (app/services/external_data_service.py). Unsynced doctors
    simply don't get this component — never a guessed rating.
  - Profile completeness (phone/email/clinic/hospital/qualification
    present) — a proxy for how outreach-ready a lead is.
  - Recency (doctor added to the directory in the last 30 days) — a
    small boost so MRs notice new additions instead of only ever
    working through the oldest records.

Score is 0-100. `reasons` is a short list of plain-language sentences
built from exactly which components fired, so nothing in the "why" is
invented after the fact — it's a direct readout of the formula.

Concrete implementation extends the Phase 1 AIRecommendationService
contract but takes an AsyncSession per call (the abstract stub in
future_interfaces.py predates any DB wiring and didn't anticipate
needing one — documenting the deviation here rather than silently
diverging from the interface).
"""
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.doctor import Doctor
from app.models.directory_mixins import EntityStatus
from app.models.place_enrichment import PlaceEnrichment
from app.services.doctor_service import get_mr_authorized_area_names
from app.services.future_interfaces import AIRecommendationService

RECENCY_WINDOW_DAYS = 30

COMPLETENESS_FIELDS = ("phone", "email", "clinic_name", "hospital_name", "qualification")
COMPLETENESS_POINTS_PER_FIELD = 6  # 5 fields * 6 = 30 max

MAX_GOOGLE_SCORE = 40
MAX_COMPLETENESS_SCORE = len(COMPLETENESS_FIELDS) * COMPLETENESS_POINTS_PER_FIELD  # 30
RECENCY_SCORE = 15
BASE_SCORE = 15  # every active doctor starts here; components only add, never subtract


def _score_google(enrichment: PlaceEnrichment | None) -> tuple[int, str | None]:
    if enrichment is None or enrichment.rating is None:
        return 0, None
    # Rating (0-5) scaled to 32 points, review-volume bonus up to 8 points.
    rating_component = min(32, round((enrichment.rating / 5) * 32))
    volume_component = min(8, (enrichment.user_ratings_total or 0) // 25)
    total = min(MAX_GOOGLE_SCORE, rating_component + volume_component)
    reason = f"Google rating of {enrichment.rating}★ from {enrichment.user_ratings_total or 0} reviews."
    return total, reason


def _score_completeness(doctor: Doctor) -> tuple[int, str | None]:
    filled = [f for f in COMPLETENESS_FIELDS if getattr(doctor, f, None)]
    total = len(filled) * COMPLETENESS_POINTS_PER_FIELD
    if not filled:
        return 0, None
    reason = f"Profile is {round(len(filled) / len(COMPLETENESS_FIELDS) * 100)}% complete ({', '.join(filled)})."
    return total, reason


def _score_recency(doctor: Doctor) -> tuple[int, str | None]:
    age = datetime.now(timezone.utc) - doctor.created_at.replace(tzinfo=timezone.utc)
    if age <= timedelta(days=RECENCY_WINDOW_DAYS):
        return RECENCY_SCORE, f"Added to the directory {age.days} day(s) ago — a fresh lead."
    return 0, None


def _build_score(doctor: Doctor, enrichment: PlaceEnrichment | None) -> tuple[int, list[str]]:
    google_pts, google_reason = _score_google(enrichment)
    completeness_pts, completeness_reason = _score_completeness(doctor)
    recency_pts, recency_reason = _score_recency(doctor)

    total = min(100, BASE_SCORE + google_pts + completeness_pts + recency_pts)
    reasons = [r for r in (google_reason, completeness_reason, recency_reason) if r]
    if not reasons:
        reasons = ["Included based on being an active doctor in your territory; no additional signals yet."]
    return total, reasons


class RuleBasedAIRecommendationService(AIRecommendationService):
    async def score_doctor(self, doctor_id: str, mr_id: str, db: AsyncSession) -> dict:
        result = await db.execute(select(Doctor).where(Doctor.id == uuid.UUID(doctor_id)))
        doctor = result.scalar_one_or_none()
        if doctor is None:
            return {"score": 0, "reasons": ["Doctor not found."]}

        enrichment_result = await db.execute(
            select(PlaceEnrichment).where(
                PlaceEnrichment.entity_type == "Doctor", PlaceEnrichment.entity_id == doctor.id
            )
        )
        enrichment = enrichment_result.scalar_one_or_none()
        score, reasons = _build_score(doctor, enrichment)
        return {"score": score, "reasons": reasons}

    async def get_daily_plan(self, mr_id: str, db: AsyncSession, limit: int = 10) -> list[dict]:
        mr_uuid = uuid.UUID(mr_id)
        authorized_areas = await get_mr_authorized_area_names(db, mr_uuid)
        if not authorized_areas:
            return []

        result = await db.execute(
            select(Doctor).where(Doctor.area.in_(authorized_areas), Doctor.status == EntityStatus.ACTIVE)
        )
        doctors = list(result.scalars().all())
        if not doctors:
            return []

        enrichment_result = await db.execute(
            select(PlaceEnrichment).where(
                PlaceEnrichment.entity_type == "Doctor",
                PlaceEnrichment.entity_id.in_([d.id for d in doctors]),
            )
        )
        enrichment_by_doctor = {e.entity_id: e for e in enrichment_result.scalars().all()}

        scored = []
        for doctor in doctors:
            score, reasons = _build_score(doctor, enrichment_by_doctor.get(doctor.id))
            scored.append({"doctor": doctor, "score": score, "reasons": reasons})

        scored.sort(key=lambda item: item["score"], reverse=True)
        return scored[:limit]
