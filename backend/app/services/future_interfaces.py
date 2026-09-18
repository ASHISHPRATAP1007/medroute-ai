"""
Interface stubs for Phase 2-5 services. NONE of these are implemented
or called in Phase 1 — they exist purely so future work plugs into a
stable contract instead of requiring a rewrite. Do not wire these into
any router yet.
"""
from abc import ABC, abstractmethod
from typing import Any


class GooglePlacesService(ABC):
    """Phase 2: enrich Doctor/MedicalShop/Stockist records with Google Places data.

    Concrete implementation: app/services/google_places_service.py
    (HttpxGooglePlacesService).
    """

    @abstractmethod
    async def fetch_place_details(self, place_id: str) -> dict[str, Any]:
        ...

    @abstractmethod
    async def search_nearby(self, lat: float, lng: float, radius_m: int) -> list[dict[str, Any]]:
        ...


class AIRecommendationService(ABC):
    """Phase 3: opportunity scoring and 'why this doctor' explanations."""

    @abstractmethod
    async def get_daily_plan(self, mr_id: str) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    async def score_doctor(self, doctor_id: str, mr_id: str) -> float:
        ...


class RouteOptimizationService(ABC):
    """Phase 4: optimal visiting order for a day's doctor list."""

    @abstractmethod
    async def optimize_route(self, mr_id: str, doctor_ids: list[str]) -> list[str]:
        ...


class VisitService(ABC):
    """Phase 4: visit logging, follow-ups, visit history."""

    @abstractmethod
    async def log_visit(self, mr_id: str, doctor_id: str, notes: str) -> None:
        ...

    @abstractmethod
    async def get_visit_history(self, mr_id: str, doctor_id: str) -> list[dict[str, Any]]:
        ...


class NotificationService(ABC):
    """Phase 5: push/email/SMS notifications for approvals, assignments, etc."""

    @abstractmethod
    async def notify(self, user_id: str, message: str, channel: str = "email") -> None:
        ...
