"""
Tests for Phase 2 Google Places sync. All Google calls are mocked —
these verify our caching/error-handling logic, not Google's API itself,
since there's no network access available to hit the real service.
"""
from unittest.mock import AsyncMock, patch
import uuid

import pytest

from app.core.security import create_access_token, hash_password


async def _make_admin(db):
    from app.models.user import User, UserRole, UserStatus
    admin = User(
        full_name="Admin", email="admin.p2@example.com", phone="9999900001",
        password_hash=hash_password("Admin@1234"), role=UserRole.ADMIN, status=UserStatus.APPROVED,
    )
    db.add(admin)
    await db.commit()
    await db.refresh(admin)
    return admin


async def _make_specialization(db):
    from app.models.specialization import Specialization
    spec = Specialization(name="Cardiologist-Test")
    db.add(spec)
    await db.commit()
    await db.refresh(spec)
    return spec


async def _make_doctor(db, admin_id):
    from app.models.doctor import Doctor
    spec = await _make_specialization(db)
    doctor = Doctor(
        full_name="Dr. Test Sync", specialization_id=spec.id, address="1 Test Street",
        city="Lucknow", state="Uttar Pradesh", created_by=admin_id, updated_by=admin_id,
    )
    db.add(doctor)
    await db.commit()
    await db.refresh(doctor)
    return doctor


def _auth_header(user):
    token = create_access_token(subject=str(user.id), role=user.role.value, status=user.status.value)
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_sync_fails_cleanly_when_not_configured(client, db):
    admin = await _make_admin(db)
    doctor = await _make_doctor(db, admin.id)

    resp = await client.post(f"/api/v1/doctors/{doctor.id}/sync-external", headers=_auth_header(admin))
    assert resp.status_code == 503
    assert "not configured" in resp.json()["message"].lower()


@pytest.mark.asyncio
async def test_external_data_is_none_before_first_sync(client, db):
    admin = await _make_admin(db)
    doctor = await _make_doctor(db, admin.id)

    resp = await client.get(f"/api/v1/doctors/{doctor.id}/external-data", headers=_auth_header(admin))
    assert resp.status_code == 200
    assert resp.json()["data"] is None


@pytest.mark.asyncio
async def test_sync_caches_google_response(client, db, monkeypatch):
    from app.core.config import get_settings
    admin = await _make_admin(db)
    doctor = await _make_doctor(db, admin.id)

    settings = get_settings()
    monkeypatch.setattr(settings, "GOOGLE_PLACES_ENABLED", True)
    monkeypatch.setattr(settings, "GOOGLE_PLACES_API_KEY", "fake-key-for-test")

    fake_details = {
        "rating": 4.5,
        "user_ratings_total": 128,
        "opening_hours": {"open_now": True, "weekday_text": ["Monday: 9AM–6PM"]},
        "photos": [{"photo_reference": "abc123"}],
        "reviews": [{"author_name": "A Patient", "rating": 5, "text": "Great doctor.", "time": 1700000000}],
    }

    with patch("app.services.google_places_service.HttpxGooglePlacesService.find_place_id", new=AsyncMock(return_value="place_123")), \
         patch("app.services.google_places_service.HttpxGooglePlacesService.fetch_place_details", new=AsyncMock(return_value=fake_details)):
        resp = await client.post(f"/api/v1/doctors/{doctor.id}/sync-external", headers=_auth_header(admin))

    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["rating"] == 4.5
    assert data["user_ratings_total"] == 128
    assert data["last_sync_status"] == "SUCCESS"

    # Second read should hit the cache, not Google again.
    read_resp = await client.get(f"/api/v1/doctors/{doctor.id}/external-data", headers=_auth_header(admin))
    assert read_resp.status_code == 200
    assert read_resp.json()["data"]["rating"] == 4.5


@pytest.mark.asyncio
async def test_sync_records_failure_when_no_place_found(client, db, monkeypatch):
    from app.core.config import get_settings
    admin = await _make_admin(db)
    doctor = await _make_doctor(db, admin.id)

    settings = get_settings()
    monkeypatch.setattr(settings, "GOOGLE_PLACES_ENABLED", True)
    monkeypatch.setattr(settings, "GOOGLE_PLACES_API_KEY", "fake-key-for-test")

    with patch("app.services.google_places_service.HttpxGooglePlacesService.find_place_id", new=AsyncMock(return_value=None)):
        resp = await client.post(f"/api/v1/doctors/{doctor.id}/sync-external", headers=_auth_header(admin))

    assert resp.status_code == 502


@pytest.mark.asyncio
async def test_mr_cannot_trigger_sync(client, db):
    from app.models.user import User, UserRole, UserStatus
    mr = User(
        full_name="MR", email="mr.p2@example.com", phone="9999900002",
        password_hash=hash_password("Mr@12345"), role=UserRole.MR, status=UserStatus.APPROVED,
    )
    db.add(mr)
    await db.commit()
    await db.refresh(mr)

    admin_stub_id = uuid.uuid4()
    resp = await client.post(f"/api/v1/doctors/{admin_stub_id}/sync-external", headers=_auth_header(mr))
    assert resp.status_code == 403
