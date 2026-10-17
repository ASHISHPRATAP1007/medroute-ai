import pytest

from app.core.security import create_access_token, hash_password


def _auth(user):
    token = create_access_token(subject=str(user.id), role=user.role.value, status=user.status.value)
    return {"Authorization": f"Bearer {token}"}


async def _user(db, email, phone, role, status):
    from app.models.user import User
    u = User(full_name=email.split("@")[0], email=email, phone=phone,
             password_hash=hash_password("Pass@1234"), role=role, status=status)
    db.add(u)
    await db.commit()
    await db.refresh(u)
    return u


async def _world(db):
    """Two areas with one doctor + shop each; MR assigned to 'Gomti' only."""
    from app.models.area import Area
    from app.models.city import City
    from app.models.doctor import Doctor
    from app.models.medical_shop import MedicalShop
    from app.models.specialization import Specialization
    from app.models.territory import Territory
    from app.models.territory_mr import TerritoryMR
    from app.models.user import UserRole, UserStatus

    admin = await _user(db, "admin.s@example.com", "9000000101", UserRole.ADMIN, UserStatus.APPROVED)
    mr = await _user(db, "sharma.mr@example.com", "9000000102", UserRole.MR, UserStatus.APPROVED)
    city = City(name="Lucknow-S", state="UP")
    db.add(city)
    await db.flush()
    gomti, aliganj = Area(city_id=city.id, name="Gomti"), Area(city_id=city.id, name="Aliganj")
    db.add_all([gomti, aliganj])
    await db.flush()
    t = Territory(area_id=gomti.id, name="T-Gomti")
    db.add(t)
    await db.flush()
    db.add(TerritoryMR(territory_id=t.id, mr_id=mr.id, assigned_by=admin.id))
    spec = Specialization(name="Spec-S")
    db.add(spec)
    await db.flush()
    for area in ("Gomti", "Aliganj"):
        db.add(Doctor(full_name=f"Dr. Sharma {area}", specialization_id=spec.id, address="x",
                      area=area, city="Lucknow-S", state="UP"))
        db.add(MedicalShop(name=f"Sharma Medicos {area}", address="x", area=area, city="Lucknow-S", state="UP"))
    await db.commit()
    return admin, mr


@pytest.mark.asyncio
async def test_admin_search_sees_everything_including_mrs(client, db):
    admin, _ = await _world(db)
    resp = await client.get("/api/v1/search?q=sharma", headers=_auth(admin))
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data["doctors"]) == 2
    assert len(data["medical_shops"]) == 2
    assert [m["email"] for m in data["mrs"]] == ["sharma.mr@example.com"]


@pytest.mark.asyncio
async def test_mr_search_is_territory_restricted_and_hides_users(client, db):
    _, mr = await _world(db)
    resp = await client.get("/api/v1/search?q=sharma", headers=_auth(mr))
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert [d["area"] for d in data["doctors"]] == ["Gomti"]
    assert [s["area"] for s in data["medical_shops"]] == ["Gomti"]
    assert data["mrs"] == []


@pytest.mark.asyncio
async def test_search_wildcards_are_literal(client, db):
    admin, _ = await _world(db)
    resp = await client.get("/api/v1/search?q=%25%25", headers=_auth(admin))  # "%%"
    assert resp.status_code == 200
    assert resp.json()["data"]["doctors"] == []


@pytest.mark.asyncio
async def test_bootstrap_creates_initial_super_admin_once(db, monkeypatch):
    from sqlalchemy import func, select

    from app.bootstrap import bootstrap
    from app.core.config import get_settings
    from app.core.security import verify_password
    from app.models.specialization import Specialization
    from app.models.user import User, UserRole

    settings = get_settings()
    monkeypatch.setattr(settings, "INITIAL_ADMIN_EMAIL", "Owner@Example.com")
    monkeypatch.setattr(settings, "INITIAL_ADMIN_PASSWORD", "Owner@12345")
    monkeypatch.setattr(settings, "SEED_DEMO_DATA", False)

    await bootstrap()
    await bootstrap()  # idempotent

    admins = (await db.execute(select(User).where(User.role == UserRole.SUPER_ADMIN))).scalars().all()
    assert [a.email for a in admins] == ["owner@example.com"]
    assert verify_password("Owner@12345", admins[0].password_hash)
    assert (await db.execute(select(func.count()).select_from(Specialization))).scalar() > 10
    # No demo accounts unless SEED_DEMO_DATA is on.
    demo = (await db.execute(select(User).where(User.email.like("%@medroute.dev")))).scalars().all()
    assert demo == []
