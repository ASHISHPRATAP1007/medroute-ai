import pytest

from app.core.security import create_access_token, hash_password


async def _make_admin(db):
    from app.models.user import User, UserRole, UserStatus
    admin = User(
        full_name="Admin", email="admin.p3@example.com", phone="9999900010",
        password_hash=hash_password("Admin@1234"), role=UserRole.ADMIN, status=UserStatus.APPROVED,
    )
    db.add(admin)
    await db.commit()
    await db.refresh(admin)
    return admin


async def _make_approved_mr(db):
    from app.models.user import User, UserRole, UserStatus
    mr = User(
        full_name="Approved MR", email="mr.p3@example.com", phone="9999900011",
        password_hash=hash_password("Mr@12345"), role=UserRole.MR, status=UserStatus.APPROVED,
    )
    db.add(mr)
    await db.commit()
    await db.refresh(mr)
    return mr


async def _make_specialization(db):
    from app.models.specialization import Specialization
    spec = Specialization(name="TestSpec-P3")
    db.add(spec)
    await db.commit()
    await db.refresh(spec)
    return spec


async def _make_territory_with_doctor(db, admin_id, mr_id):
    from app.models.city import City
    from app.models.area import Area
    from app.models.territory import Territory
    from app.models.territory_mr import TerritoryMR
    from app.models.doctor import Doctor

    city = City(name="TestCity", state="TestState")
    db.add(city)
    await db.flush()
    area = Area(city_id=city.id, name="TestArea")
    db.add(area)
    await db.flush()
    territory = Territory(area_id=area.id, name="TestTerritory")
    db.add(territory)
    await db.flush()
    db.add(TerritoryMR(territory_id=territory.id, mr_id=mr_id, assigned_by=admin_id))

    spec = await _make_specialization(db)
    # Fully complete profile -> should score higher than a bare-minimum one.
    complete_doctor = Doctor(
        full_name="Dr. Complete", specialization_id=spec.id, address="1 Complete St",
        area="TestArea", city="TestCity", state="TestState",
        phone="9000000000", email="complete@example.com", clinic_name="Clinic A",
        hospital_name="Hospital A", qualification="MBBS",
        created_by=admin_id, updated_by=admin_id,
    )
    bare_doctor = Doctor(
        full_name="Dr. Bare", specialization_id=spec.id, address="2 Bare St",
        area="TestArea", city="TestCity", state="TestState",
        created_by=admin_id, updated_by=admin_id,
    )
    outside_doctor = Doctor(
        full_name="Dr. Outside", specialization_id=spec.id, address="3 Outside St",
        area="OtherArea", city="OtherCity", state="OtherState",
        created_by=admin_id, updated_by=admin_id,
    )
    db.add_all([complete_doctor, bare_doctor, outside_doctor])
    await db.commit()
    await db.refresh(complete_doctor)
    await db.refresh(bare_doctor)
    await db.refresh(outside_doctor)
    return complete_doctor, bare_doctor, outside_doctor


def _auth_header(user):
    token = create_access_token(subject=str(user.id), role=user.role.value, status=user.status.value)
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_daily_plan_only_includes_territory_doctors(client, db):
    admin = await _make_admin(db)
    mr = await _make_approved_mr(db)
    complete_doctor, bare_doctor, outside_doctor = await _make_territory_with_doctor(db, admin.id, mr.id)

    resp = await client.get("/api/v1/ai/daily-plan", headers=_auth_header(mr))
    assert resp.status_code == 200
    items = resp.json()["data"]
    doctor_ids = {item["doctor"]["id"] for item in items}

    assert str(complete_doctor.id) in doctor_ids
    assert str(bare_doctor.id) in doctor_ids
    assert str(outside_doctor.id) not in doctor_ids  # outside MR's territory — never leaks


@pytest.mark.asyncio
async def test_more_complete_profile_scores_higher(client, db):
    admin = await _make_admin(db)
    mr = await _make_approved_mr(db)
    complete_doctor, bare_doctor, _ = await _make_territory_with_doctor(db, admin.id, mr.id)

    resp = await client.get("/api/v1/ai/daily-plan", headers=_auth_header(mr))
    items = {item["doctor"]["id"]: item for item in resp.json()["data"]}

    complete_score = items[str(complete_doctor.id)]["score"]
    bare_score = items[str(bare_doctor.id)]["score"]
    assert complete_score > bare_score
    assert len(items[str(complete_doctor.id)]["reasons"]) > 0


@pytest.mark.asyncio
async def test_mr_with_no_territory_gets_empty_plan(client, db):
    mr = await _make_approved_mr(db)
    resp = await client.get("/api/v1/ai/daily-plan", headers=_auth_header(mr))
    assert resp.status_code == 200
    assert resp.json()["data"] == []


@pytest.mark.asyncio
async def test_opportunity_score_404s_for_out_of_territory_doctor(client, db):
    admin = await _make_admin(db)
    mr = await _make_approved_mr(db)
    _, _, outside_doctor = await _make_territory_with_doctor(db, admin.id, mr.id)

    resp = await client.get(f"/api/v1/ai/doctors/{outside_doctor.id}/opportunity-score", headers=_auth_header(mr))
    assert resp.status_code == 404
