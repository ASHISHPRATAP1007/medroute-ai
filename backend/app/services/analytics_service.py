"""
Phase 5 — analytics computed entirely from real rows in Doctor,
Visit, Territory, and TerritoryMR. No estimated, interpolated, or
placeholder figures — a territory or MR with zero visits reports
zero, not a plausible-looking fake number.
"""
from sqlalchemy import distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.area import Area
from app.models.directory_mixins import EntityStatus
from app.models.doctor import Doctor
from app.models.territory import Territory
from app.models.territory_mr import TerritoryMR
from app.models.user import User, UserRole, UserStatus
from app.models.visit import Visit, VisitStatus
from app.schemas.analytics import MRPerformanceOut, TerritoryCoverageOut


async def get_mr_performance(db: AsyncSession) -> list[MRPerformanceOut]:
    result = await db.execute(select(User).where(User.role == UserRole.MR, User.status == UserStatus.APPROVED))
    mrs = list(result.scalars().all())

    reports = []
    for mr in mrs:
        visits_result = await db.execute(select(Visit).where(Visit.mr_id == mr.id))
        visits = list(visits_result.scalars().all())

        planned = sum(1 for v in visits if v.status == VisitStatus.PLANNED)
        completed = sum(1 for v in visits if v.status == VisitStatus.COMPLETED)
        cancelled = sum(1 for v in visits if v.status == VisitStatus.CANCELLED)
        missed = sum(1 for v in visits if v.status == VisitStatus.MISSED)

        decided = completed + cancelled + missed  # visits no longer pending
        completion_rate = round(completed / decided, 2) if decided else 0.0
        doctors_covered = len({v.doctor_id for v in visits if v.status == VisitStatus.COMPLETED})
        completed_dates = [v.scheduled_date for v in visits if v.status == VisitStatus.COMPLETED]
        last_visit_date = max(completed_dates) if completed_dates else None

        reports.append(MRPerformanceOut(
            mr_id=mr.id, full_name=mr.full_name, visits_planned=planned, visits_completed=completed,
            visits_cancelled=cancelled, visits_missed=missed, completion_rate=completion_rate,
            doctors_covered=doctors_covered, last_visit_date=last_visit_date,
        ))

    reports.sort(key=lambda r: r.visits_completed, reverse=True)
    return reports


async def get_territory_coverage(db: AsyncSession) -> list[TerritoryCoverageOut]:
    territories_result = await db.execute(select(Territory))
    territories = list(territories_result.scalars().all())

    reports = []
    for territory in territories:
        area_result = await db.execute(select(Area).where(Area.id == territory.area_id))
        area = area_result.scalar_one_or_none()
        if area is None:
            continue

        total_doctors = (await db.execute(
            select(func.count()).select_from(Doctor).where(Doctor.area == area.name, Doctor.status == EntityStatus.ACTIVE)
        )).scalar_one()

        # Visited = at least one COMPLETED visit, by any MR assigned to this territory.
        mr_ids_result = await db.execute(select(TerritoryMR.mr_id).where(TerritoryMR.territory_id == territory.id))
        mr_ids = [row[0] for row in mr_ids_result.all()]

        if total_doctors == 0 or not mr_ids:
            doctors_visited = 0
        else:
            visited_result = await db.execute(
                select(func.count(distinct(Visit.doctor_id)))
                .select_from(Visit)
                .join(Doctor, Doctor.id == Visit.doctor_id)
                .where(
                    Visit.mr_id.in_(mr_ids), Visit.status == VisitStatus.COMPLETED,
                    Doctor.area == area.name, Doctor.status == EntityStatus.ACTIVE,
                )
            )
            doctors_visited = visited_result.scalar_one()

        coverage_percent = round((doctors_visited / total_doctors) * 100, 1) if total_doctors else 0.0

        reports.append(TerritoryCoverageOut(
            territory_id=territory.id, territory_name=territory.name, total_active_doctors=total_doctors,
            doctors_visited=doctors_visited, coverage_percent=coverage_percent,
        ))

    reports.sort(key=lambda r: r.coverage_percent)
    return reports
