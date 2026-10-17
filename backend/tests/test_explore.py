"""Free Explore (OpenStreetMap). Nominatim/Overpass are mocked with httpx.MockTransport."""
import httpx
import pytest

from app.core.security import create_access_token, hash_password

NOMINATIM = [{"lat": "26.8500", "lon": "80.9500", "display_name": "Hazratganj, Lucknow, Uttar Pradesh, India"}]
OVERPASS = {"elements": [
    {"type": "node", "id": 1, "lat": 26.851, "lon": 80.951, "tags": {
        "amenity": "clinic", "name": "Sharma Heart Clinic", "healthcare:speciality": "cardiology",
        "phone": "+91 522 400 0000", "addr:street": "MG Road", "addr:city": "Lucknow", "opening_hours": "Mo-Sa 10:00-14:00"}},
    {"type": "way", "id": 2, "center": {"lat": 26.90, "lon": 80.99}, "tags": {"amenity": "doctors", "name": "Dr. Far Away"}},
    {"type": "node", "id": 3, "lat": 26.852, "lon": 80.952, "tags": {"amenity": "doctors"}},  # no name -> dropped
    {"type": "node", "id": 4, "lat": 26.851, "lon": 80.951, "tags": {"healthcare": "clinic", "name": "Sharma Heart Clinic"}},  # duplicate
]}


@pytest.fixture
def osm(monkeypatch):
    from app.services import explore_service
    explore_service._cache.clear()
    calls = []

    def handler(request: httpx.Request):
        calls.append(request)
        if "nominatim" in request.url.host:
            return httpx.Response(200, json=NOMINATIM)
        return httpx.Response(200, json=OVERPASS)

    real = httpx.AsyncClient

    def fake(*a, **k):
        k["transport"] = httpx.MockTransport(handler)
        return real(*a, **k)

    monkeypatch.setattr("app.services.explore_service.httpx.AsyncClient", fake)
    return calls


async def _mr(db, status="APPROVED"):
    from app.models.user import User, UserRole, UserStatus
    u = User(full_name="MR", email=f"mr.{status.lower()}@ex.com", phone=f"90000004{len(status):02d}",
             password_hash=hash_password("Pass@1234"), role=UserRole.MR, status=UserStatus(status))
    db.add(u)
    await db.commit()
    await db.refresh(u)
    return {"Authorization": f"Bearer {create_access_token(subject=str(u.id), role='MR', status=status)}"}


@pytest.mark.asyncio
async def test_explore_any_place_for_mr_without_territory(client, db, osm):
    h = await _mr(db)
    resp = await client.get("/api/v1/explore/places?category=doctor&location=Hazratganj, Lucknow", headers=h)
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data["center"]["label"].startswith("Hazratganj")
    names = [p["name"] for p in data["places"]]
    assert names == ["Sharma Heart Clinic", "Dr. Far Away"]  # nearest first, nameless + duplicate dropped
    first = data["places"][0]
    assert first["phone"] == "+91 522 400 0000"
    assert first["speciality"] == "cardiology"
    assert first["address"] == "MG Road, Lucknow"
    assert first["google_maps_url"].startswith("https://www.google.com/maps/search/?api=1&query=Sharma+Heart+Clinic")
    assert first["distance_km"] < 1

    # Overpass query used the geocoded point and the doctor tag filters
    overpass_req = [c for c in osm if "nominatim" not in c.url.host][0]
    body = overpass_req.content.decode()
    assert "around%3A5000%2C26.85000%2C80.95000" in body
    assert "doctors" in body


@pytest.mark.asyncio
async def test_explore_gps_keyword_and_cache(client, db, osm):
    h = await _mr(db)
    url = "/api/v1/explore/places?category=doctor&lat=26.85&lng=80.95&radius_km=3&keyword=cardio"
    r1 = await client.get(url, headers=h)
    assert [p["name"] for p in r1.json()["data"]["places"]] == ["Sharma Heart Clinic"]
    assert all("nominatim" not in c.url.host for c in osm)  # GPS: no geocoding
    await client.get(url, headers=h)
    assert len(osm) == 1  # second call served from cache


@pytest.mark.asyncio
async def test_explore_requires_place_or_gps_and_approved_mr(client, db, osm):
    h = await _mr(db)
    assert (await client.get("/api/v1/explore/places?category=doctor", headers=h)).status_code == 422
    pending = await _mr(db, "PENDING")
    assert (await client.get("/api/v1/explore/places?category=doctor&location=x", headers=pending)).status_code == 403
    assert (await client.get("/api/v1/explore/places?category=doctor&location=x")).status_code == 401
