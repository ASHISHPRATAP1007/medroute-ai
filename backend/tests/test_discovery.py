"""
Doctor discovery (Google Places API (New)) — search + import.

Google itself is never called: the HTTP layer is replaced with
httpx.MockTransport returning payloads shaped like Places API (New)
responses, so these tests also exercise our request building and the
New -> legacy-shape normalization in google_places_service.py.
"""
import json

import httpx
import pytest

from app.core.security import create_access_token, hash_password

PLACE_ID = "ChIJtest_cardio_1"

SEARCH_RESPONSE = {
    "places": [
        {
            "id": PLACE_ID,
            "displayName": {"text": "Dr. Real Cardio", "languageCode": "en"},
            "formattedAddress": "12 Hazratganj, Lucknow, Uttar Pradesh 226001, India",
            "location": {"latitude": 26.85, "longitude": 80.945},
            "rating": 4.6,
            "userRatingCount": 210,
        },
        {"id": "ChIJno_name"},  # incomplete result — must be dropped, not crash
    ]
}

DETAILS_RESPONSE = {
    "id": PLACE_ID,
    "displayName": {"text": "Dr. Real Cardio"},
    "formattedAddress": "12 Hazratganj, Lucknow, Uttar Pradesh 226001, India",
    "nationalPhoneNumber": "0522 400 1234",
    "location": {"latitude": 26.85, "longitude": 80.945},
    "rating": 4.6,
    "userRatingCount": 210,
    "regularOpeningHours": {"openNow": True, "weekdayDescriptions": ["Monday: 10:00 AM – 2:00 PM"]},
    "photos": [{"name": f"places/{PLACE_ID}/photos/abc", "widthPx": 800, "heightPx": 600}],
    "reviews": [
        {
            "authorAttribution": {"displayName": "Ravi"},
            "rating": 5,
            "text": {"text": "Very good doctor."},
            "publishTime": "2026-09-01T10:00:00Z",
        }
    ],
}


def _mock_google(calls: list):
    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        if request.url.path.endswith("/places:searchText"):
            return httpx.Response(200, json=SEARCH_RESPONSE)
        if request.url.path == f"/v1/places/{PLACE_ID}":
            return httpx.Response(200, json=DETAILS_RESPONSE)
        return httpx.Response(404, json={"error": {"message": "not found"}})

    return httpx.MockTransport(handler)


@pytest.fixture
def google_enabled(monkeypatch):
    from app.core.config import get_settings

    settings = get_settings()
    monkeypatch.setattr(settings, "GOOGLE_PLACES_ENABLED", True)
    monkeypatch.setattr(settings, "GOOGLE_PLACES_API_KEY", "test-key")

    calls: list[httpx.Request] = []
    real_client = httpx.AsyncClient

    def fake_client(*args, **kwargs):
        kwargs["transport"] = _mock_google(calls)
        return real_client(*args, **kwargs)

    monkeypatch.setattr("app.services.google_places_service.httpx.AsyncClient", fake_client)
    return calls


async def _make_admin(db):
    from app.models.user import User, UserRole, UserStatus
    admin = User(
        full_name="Admin", email="admin.disc@example.com", phone="9999900090",
        password_hash=hash_password("Admin@1234"), role=UserRole.ADMIN, status=UserStatus.APPROVED,
    )
    db.add(admin)
    await db.commit()
    await db.refresh(admin)
    return admin


async def _make_spec(db):
    from app.models.specialization import Specialization
    spec = Specialization(name="Cardiologist-Disc")
    db.add(spec)
    await db.commit()
    await db.refresh(spec)
    return spec


def _auth(user):
    token = create_access_token(subject=str(user.id), role=user.role.value, status=user.status.value)
    return {"Authorization": f"Bearer {token}"}


SEARCH_BODY = {"specialization_name": "Cardiologist", "area": "Hazratganj", "city": "Lucknow", "state": "Uttar Pradesh"}


@pytest.mark.asyncio
async def test_search_returns_503_when_not_configured(client, db):
    admin = await _make_admin(db)
    resp = await client.post("/api/v1/doctors/discovery/search", json=SEARCH_BODY, headers=_auth(admin))
    assert resp.status_code == 503
    assert "not configured" in resp.json()["message"].lower()


@pytest.mark.asyncio
async def test_search_requires_admin(client, db):
    from app.models.user import User, UserRole, UserStatus
    mr = User(full_name="MR", email="mr.disc@example.com", phone="9999900091",
              password_hash=hash_password("Mr@12345"), role=UserRole.MR, status=UserStatus.APPROVED)
    db.add(mr)
    await db.commit()
    await db.refresh(mr)
    resp = await client.post("/api/v1/doctors/discovery/search", json=SEARCH_BODY, headers=_auth(mr))
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_search_uses_places_new_api_and_normalizes(client, db, google_enabled):
    admin = await _make_admin(db)
    resp = await client.post("/api/v1/doctors/discovery/search", json=SEARCH_BODY, headers=_auth(admin))
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert len(data) == 1  # the nameless result was dropped
    assert data[0] == {
        "place_id": PLACE_ID, "name": "Dr. Real Cardio",
        "address": "12 Hazratganj, Lucknow, Uttar Pradesh 226001, India",
        "rating": 4.6, "user_ratings_total": 210, "latitude": 26.85, "longitude": 80.945,
        "already_imported": False,
    }

    req = google_enabled[0]
    assert str(req.url) == "https://places.googleapis.com/v1/places:searchText"
    assert req.headers["X-Goog-Api-Key"] == "test-key"
    assert " " not in req.headers["X-Goog-FieldMask"]
    body = json.loads(req.content)
    assert body["textQuery"] == "Cardiologist doctor in Hazratganj, Lucknow, Uttar Pradesh"
    assert body["includedType"] == "doctor"


@pytest.mark.asyncio
async def test_import_creates_doctor_with_enrichment_then_blocks_duplicate(client, db, google_enabled):
    admin = await _make_admin(db)
    spec = await _make_spec(db)
    body = {"place_id": PLACE_ID, "specialization_id": str(spec.id),
            "city": "Lucknow", "state": "Uttar Pradesh", "area": "Hazratganj"}

    resp = await client.post("/api/v1/doctors/discovery/import", json=body, headers=_auth(admin))
    assert resp.status_code == 201, resp.text
    doctor = resp.json()["data"]
    assert doctor["full_name"] == "Dr. Real Cardio"
    assert doctor["phone"] == "0522 400 1234"
    assert doctor["source"] == "EXTERNAL"
    # Exactly one Google call for the whole import.
    assert len(google_enabled) == 1

    ext = await client.get(f"/api/v1/doctors/{doctor['id']}/external-data", headers=_auth(admin))
    enrichment = ext.json()["data"]
    assert enrichment["rating"] == 4.6
    assert enrichment["opening_hours"]["weekday_text"] == ["Monday: 10:00 AM – 2:00 PM"]
    assert enrichment["reviews"][0]["author"] == "Ravi"
    assert enrichment["reviews"][0]["text"] == "Very good doctor."

    again = await client.post("/api/v1/doctors/discovery/import", json=body, headers=_auth(admin))
    assert again.status_code == 409

    # Search now flags it as already imported.
    search = await client.post("/api/v1/doctors/discovery/search", json=SEARCH_BODY, headers=_auth(admin))
    assert search.json()["data"][0]["already_imported"] is True


@pytest.mark.asyncio
async def test_import_unknown_specialization_is_404_not_500(client, db, google_enabled):
    admin = await _make_admin(db)
    body = {"place_id": PLACE_ID, "specialization_id": "00000000-0000-0000-0000-000000000000",
            "city": "Lucknow", "state": "Uttar Pradesh", "area": ""}
    resp = await client.post("/api/v1/doctors/discovery/import", json=body, headers=_auth(admin))
    assert resp.status_code == 404
    assert google_enabled == []  # validated before spending a Google call


@pytest.mark.asyncio
async def test_google_error_message_is_surfaced(client, db, monkeypatch):
    from app.core.config import get_settings
    settings = get_settings()
    monkeypatch.setattr(settings, "GOOGLE_PLACES_ENABLED", True)
    monkeypatch.setattr(settings, "GOOGLE_PLACES_API_KEY", "bad-key")
    real_client = httpx.AsyncClient

    def fake_client(*args, **kwargs):
        kwargs["transport"] = httpx.MockTransport(
            lambda r: httpx.Response(400, json={"error": {"code": 400, "message": "API key not valid.", "status": "INVALID_ARGUMENT"}})
        )
        return real_client(*args, **kwargs)

    monkeypatch.setattr("app.services.google_places_service.httpx.AsyncClient", fake_client)
    admin = await _make_admin(db)
    resp = await client.post("/api/v1/doctors/discovery/search", json=SEARCH_BODY, headers=_auth(admin))
    assert resp.status_code == 502
    assert "API key not valid" in resp.json()["message"]
