"""
Phase 4 — route optimization for a day's list of doctor visits.

The core algorithm (haversine distance + nearest-neighbor ordering) is
pure math with no DB or network dependency, so unlike most of this
project it can actually be run and verified in this environment — see
the bottom of this file for a `if __name__ == "__main__"` self-check,
and app/services/route_optimization_service.py is imported by a real
DB-backed wrapper for use in the API.

Nearest-neighbor is a well-known greedy TSP heuristic: not globally
optimal, but deterministic, fast, and good enough for a day's handful
of stops — appropriate for a field rep's daily route, not a logistics
fleet. Doctors with no coordinates are appended at the end, in their
original relative order, since we cannot place them on a route without
a location.
"""
import math
from dataclasses import dataclass


@dataclass
class RoutePoint:
    id: str
    lat: float | None
    lng: float | None


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance between two lat/lng points, in kilometers."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lng2 - lng1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return 2 * R * math.asin(min(1, math.sqrt(a)))


def nearest_neighbor_order(points: list[RoutePoint], start_id: str | None = None) -> list[str]:
    """
    Returns point IDs ordered by a greedy nearest-neighbor walk.
    Points with no coordinates are excluded from the walk and appended
    at the end, in their original relative order.
    """
    locatable = [p for p in points if p.lat is not None and p.lng is not None]
    unlocatable_ids = [p.id for p in points if p.lat is None or p.lng is None]

    if not locatable:
        return unlocatable_ids

    remaining = {p.id: p for p in locatable}

    if start_id and start_id in remaining:
        current = remaining.pop(start_id)
    else:
        current = locatable[0]
        remaining.pop(current.id, None)

    ordered = [current.id]
    while remaining:
        nearest_id = min(
            remaining, key=lambda pid: haversine_km(current.lat, current.lng, remaining[pid].lat, remaining[pid].lng)
        )
        current = remaining.pop(nearest_id)
        ordered.append(current.id)

    return ordered + unlocatable_ids


if __name__ == "__main__":
    # Self-check runnable with plain `python3 route_optimization_service.py`
    # — no pytest, no DB, no network needed. Real, verifiable output.
    lucknow_points = [
        RoutePoint(id="gomti_nagar", lat=26.8548, lng=81.0104),
        RoutePoint(id="hazratganj", lat=26.8500, lng=80.9450),
        RoutePoint(id="aliganj", lat=26.8890, lng=80.9310),
        RoutePoint(id="indira_nagar", lat=26.8760, lng=81.0080),
        RoutePoint(id="no_coords", lat=None, lng=None),
    ]
    order = nearest_neighbor_order(lucknow_points, start_id="gomti_nagar")
    print("Route order:", order)
    assert order[0] == "gomti_nagar", "Route must start at the requested point"
    assert order[-1] == "no_coords", "Points without coordinates must go last"
    assert set(order) == {p.id for p in lucknow_points}, "Route must include every point exactly once"
    assert len(order) == len(set(order)), "Route must not repeat a point"
    print("Self-check passed.")
