"""
Phase 4 — concrete RouteOptimizationService.

Wraps the pure, independently-runnable algorithm in
route_optimization_pure.py (haversine distance + nearest-neighbor
ordering) with a DB lookup of doctor coordinates. See that file for
why nearest-neighbor was chosen and a standalone self-check that
proves the algorithm itself works correctly without any DB or network
dependency — the one part of this project verified to actually run.
"""
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.doctor import Doctor
from app.services.future_interfaces import RouteOptimizationService
from app.services.route_optimization_pure import RoutePoint, nearest_neighbor_order


class NearestNeighborRouteOptimizationService(RouteOptimizationService):
    async def optimize_route(self, mr_id: str, doctor_ids: list[str], db: AsyncSession) -> list[str]:
        """
        Extended beyond the Phase 1 abstract signature to take a DB
        session — see ai_recommendation_service.py for the same
        documented deviation and rationale.
        """
        if not doctor_ids:
            return []

        uuid_ids = [uuid.UUID(d) for d in doctor_ids]
        result = await db.execute(select(Doctor).where(Doctor.id.in_(uuid_ids)))
        doctors_by_id = {str(d.id): d for d in result.scalars().all()}

        points = [
            RoutePoint(
                id=doctor_id,
                lat=float(doctors_by_id[doctor_id].latitude) if doctor_id in doctors_by_id and doctors_by_id[doctor_id].latitude is not None else None,
                lng=float(doctors_by_id[doctor_id].longitude) if doctor_id in doctors_by_id and doctors_by_id[doctor_id].longitude is not None else None,
            )
            for doctor_id in doctor_ids
            if doctor_id in doctors_by_id
        ]
        return nearest_neighbor_order(points)
