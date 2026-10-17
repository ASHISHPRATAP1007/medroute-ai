"""Regression tests for endpoints that used to 500 on async lazy-loading."""
import pytest

from app.core.security import create_access_token, hash_password


def _auth(user):
    return {"Authorization": f"Bearer {create_access_token(subject=str(user.id), role=user.role.value, status=user.status.value)}"}


async def _user(db, email, phone, role, status):
    from app.models.user import User
    u = User(full_name=email, email=email, phone=phone, password_hash=hash_password("Pass@1234"), role=role, status=status)
    db.add(u)
    await db.commit()
    await db.refresh(u)
    return u


@pytest.mark.asyncio
async def test_admin_dashboard_with_pending_mr(client, db):
    from app.models.mr_profile import MRProfile
    from app.models.user import UserRole, UserStatus
    admin = await _user(db, "a.dash@example.com", "9000000201", UserRole.ADMIN, UserStatus.APPROVED)
    pending = await _user(db, "p.dash@example.com", "9000000202", UserRole.MR, UserStatus.PENDING)
    db.add(MRProfile(user_id=pending.id, company_name="Acme", employee_id="E1", city="Lucknow", state="UP", assigned_area="X"))
    await db.commit()

    resp = await client.get("/api/v1/admin/dashboard", headers=_auth(admin))
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data["pending_mrs"] == 1
    assert data["recent_pending_mrs"][0]["mr_profile"]["employee_id"] == "E1"


@pytest.mark.asyncio
async def test_mr_my_territories(client, db):
    from app.models.area import Area
    from app.models.city import City
    from app.models.territory import Territory
    from app.models.territory_mr import TerritoryMR
    from app.models.user import UserRole, UserStatus
    admin = await _user(db, "a2.dash@example.com", "9000000203", UserRole.ADMIN, UserStatus.APPROVED)
    mr = await _user(db, "m.dash@example.com", "9000000204", UserRole.MR, UserStatus.APPROVED)
    city = City(name="C-Dash", state="UP")
    db.add(city)
    await db.flush()
    area = Area(city_id=city.id, name="A-Dash")
    db.add(area)
    await db.flush()
    t = Territory(area_id=area.id, name="T-Dash")
    db.add(t)
    await db.flush()
    db.add(TerritoryMR(territory_id=t.id, mr_id=mr.id, assigned_by=admin.id))
    await db.commit()

    resp = await client.get("/api/v1/territories/mine", headers=_auth(mr))
    assert resp.status_code == 200, resp.text
    assert [x["name"] for x in resp.json()["data"]] == ["T-Dash"]

    dash = await client.get("/api/v1/mr/dashboard", headers=_auth(mr))
    assert dash.status_code == 200
    assert dash.json()["data"]["assigned_territory_count"] == 1


@pytest.mark.asyncio
async def test_unhandled_errors_keep_cors_headers(client, db, monkeypatch):
    from app.models.user import UserRole, UserStatus
    from app.services import search_service
    admin = await _user(db, "a3.dash@example.com", "9000000205", UserRole.ADMIN, UserStatus.APPROVED)

    async def boom(*a, **k):
        raise RuntimeError("boom")

    monkeypatch.setattr(search_service, "global_search", boom)
    resp = await client.get("/api/v1/search?q=xx", headers={**_auth(admin), "Origin": "http://localhost:3000"})
    assert resp.status_code == 500
    assert resp.json()["message"] == "Something went wrong."
    assert resp.headers.get("access-control-allow-origin") == "http://localhost:3000"
