from datetime import date, timedelta

import pytest

from app.core.security import create_access_token, hash_password


async def _make_admin(db):
    from app.models.user import User, UserRole, UserStatus
    admin = User(
        full_name="Admin", email="admin.p4@example.com", phone="9999900020",
        password_hash=hash_password("Admin@1234"), role=UserRole.ADMIN, status=UserStatus.APPROVED,
    )
    db.add(admin)
    await db.commit()
    await db.refresh(admin)
    return admin


async def _make_approved_mr(db, email="mr.p4@example.com", phone="9999900021"):
    from app.models.user import User, UserRole, UserStatus
    mr = User(
        full_name="Approved MR", email=email, phone=phone,
        password_hash=hash_password("Mr@12345"), role=UserRole.MR, status=UserStatus.APPROVED,
    )
    db.add(mr)
    await db.commit()
    await db.refresh(mr)
    return mr


async def _make_territory_with_doctor(db, admin_id, mr_id, lat=None, lng=None, area_name="TestArea"):
    from app.models.city import City
    from app.models.area import Area
    from app.models.territory import Territory
    from app.models.territory_mr import TerritoryMR
    from app.models.doctor import Doctor
    from app.models.specialization import Specialization

    city = City(name=f"City-{area_name}", state="TestState")
    db.add(city)
    await db.flush()
    area = Area(city_id=city.id, name=area_name)
    db.add(area)
    await db.flush()
    territory = Territory(area_id=area.id, name=f"Territory-{area_name}")
    db.add(territory)
    await db.flush()
    db.add(TerritoryMR(territory_id=territory.id, mr_id=mr_id, assigned_by=admin_id))

    spec = Specialization(name=f"Spec-{area_name}")
    db.add(spec)
    await db.flush()

    doctor = Doctor(
        full_name=f"Dr. {area_name}", specialization_id=spec.id, address=f"1 {area_name} St",
        area=area_name, city=city.name, state="TestState", latitude=lat, longitude=lng,
        created_by=admin_id, updated_by=admin_id,
    )
    db.add(doctor)
    await db.commit()
    await db.refresh(doctor)
    return doctor


def _auth_header(user):
    token = create_access_token(subject=str(user.id), role=user.role.value, status=user.status.value)
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_mr_can_plan_visit_for_own_territory_doctor(client, db):
    admin = await _make_admin(db)
    mr = await _make_approved_mr(db)
    doctor = await _make_territory_with_doctor(db, admin.id, mr.id)

    resp = await client.post(
        "/api/v1/visits", json={"doctor_id": str(doctor.id), "scheduled_date": "2026-09-20"},
        headers=_auth_header(mr),
    )
    assert resp.status_code == 201
    assert resp.json()["data"]["status"] == "PLANNED"


@pytest.mark.asyncio
async def test_cannot_plan_duplicate_visit_same_day(client, db):
    admin = await _make_admin(db)
    mr = await _make_approved_mr(db)
    doctor = await _make_territory_with_doctor(db, admin.id, mr.id)

    payload = {"doctor_id": str(doctor.id), "scheduled_date": "2026-09-20"}
    first = await client.post("/api/v1/visits", json=payload, headers=_auth_header(mr))
    second = await client.post("/api/v1/visits", json=payload, headers=_auth_header(mr))
    assert first.status_code == 201
    assert second.status_code == 409


@pytest.mark.asyncio
async def test_cannot_plan_visit_for_out_of_territory_doctor(client, db):
    admin = await _make_admin(db)
    mr = await _make_approved_mr(db)
    other_mr = await _make_approved_mr(db, email="other.mr.p4@example.com", phone="9999900022")
    doctor = await _make_territory_with_doctor(db, admin.id, other_mr.id, area_name="OtherArea")

    resp = await client.post(
        "/api/v1/visits", json={"doctor_id": str(doctor.id), "scheduled_date": "2026-09-20"},
        headers=_auth_header(mr),
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_mr_cannot_update_another_mrs_visit(client, db):
    admin = await _make_admin(db)
    mr1 = await _make_approved_mr(db)
    mr2 = await _make_approved_mr(db, email="mr2.p4@example.com", phone="9999900023")
    doctor = await _make_territory_with_doctor(db, admin.id, mr1.id)

    plan_resp = await client.post(
        "/api/v1/visits", json={"doctor_id": str(doctor.id), "scheduled_date": "2026-09-20"},
        headers=_auth_header(mr1),
    )
    visit_id = plan_resp.json()["data"]["id"]

    resp = await client.put(
        f"/api/v1/visits/{visit_id}",
        json={"status": "COMPLETED", "notes": "hijacked"},
        headers=_auth_header(mr2),
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_complete_visit_with_follow_up(client, db):
    admin = await _make_admin(db)
    mr = await _make_approved_mr(db)
    doctor = await _make_territory_with_doctor(db, admin.id, mr.id)

    plan_resp = await client.post(
        "/api/v1/visits", json={"doctor_id": str(doctor.id), "scheduled_date": "2026-09-20"},
        headers=_auth_header(mr),
    )
    visit_id = plan_resp.json()["data"]["id"]

    resp = await client.put(
        f"/api/v1/visits/{visit_id}",
        json={
            "status": "COMPLETED",
            "outcome": "Discussed new product line.",
            # Relative to today — a hard-coded date silently stops being
            # "upcoming" once the calendar passes it.
            "follow_up_date": (date.today() + timedelta(days=10)).isoformat(),
        },
        headers=_auth_header(mr),
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "COMPLETED"

    follow_ups = await client.get("/api/v1/visits/follow-ups", headers=_auth_header(mr))
    assert follow_ups.status_code == 200
    assert len(follow_ups.json()["data"]) == 1


@pytest.mark.asyncio
async def test_daily_route_orders_by_distance(client, db):
    admin = await _make_admin(db)
    mr = await _make_approved_mr(db)
    # Two doctors far apart, one close to the first — nearest-neighbor
    # should visit the close one second, not the far one.
    doctor_a = await _make_territory_with_doctor(db, admin.id, mr.id, lat=26.8548, lng=81.0104, area_name="AreaA")
    doctor_b = await _make_territory_with_doctor(db, admin.id, mr.id, lat=26.8550, lng=81.0110, area_name="AreaB")  # very close to A
    doctor_c = await _make_territory_with_doctor(db, admin.id, mr.id, lat=28.7041, lng=77.1025, area_name="AreaC")  # Delhi — far away

    for doctor in (doctor_a, doctor_b, doctor_c):
        await client.post(
            "/api/v1/visits", json={"doctor_id": str(doctor.id), "scheduled_date": "2026-09-21"},
            headers=_auth_header(mr),
        )

    resp = await client.get("/api/v1/visits/daily-route?target_date=2026-09-21", headers=_auth_header(mr))
    assert resp.status_code == 200
    stops = resp.json()["data"]
    assert len(stops) == 3
    ordered_doctor_ids = [s["doctor"]["id"] for s in stops]
    # C (Delhi) must not be visited between A and B — it should end up last.
    assert ordered_doctor_ids[-1] == str(doctor_c.id)


@pytest.mark.asyncio
async def test_daily_route_from_gps_start_and_distances(client, db):
    admin = await _make_admin(db)
    mr = await _make_approved_mr(db)
    doctor_a = await _make_territory_with_doctor(db, admin.id, mr.id, lat=26.8548, lng=81.0104, area_name="AreaA")
    doctor_c = await _make_territory_with_doctor(db, admin.id, mr.id, lat=28.7041, lng=77.1025, area_name="AreaC")

    for doctor in (doctor_a, doctor_c):
        await client.post(
            "/api/v1/visits", json={"doctor_id": str(doctor.id), "scheduled_date": "2026-09-22"},
            headers=_auth_header(mr),
        )

    # MR is standing in Delhi -> the Delhi doctor must come first.
    resp = await client.get(
        "/api/v1/visits/daily-route?target_date=2026-09-22&start_lat=28.70&start_lng=77.10",
        headers=_auth_header(mr),
    )
    assert resp.status_code == 200
    stops = resp.json()["data"]
    assert [s["doctor"]["id"] for s in stops] == [str(doctor_c.id), str(doctor_a.id)]
    assert stops[0]["distance_from_previous_km"] < 1
    # Delhi -> Lucknow is roughly 400-450 km as the crow flies.
    assert 380 < stops[1]["distance_from_previous_km"] < 470


@pytest.mark.asyncio
async def test_visit_list_includes_doctor_details(client, db):
    admin = await _make_admin(db)
    mr = await _make_approved_mr(db)
    doctor = await _make_territory_with_doctor(db, admin.id, mr.id, area_name="NamedArea")
    await client.post(
        "/api/v1/visits", json={"doctor_id": str(doctor.id), "scheduled_date": "2026-09-23"},
        headers=_auth_header(mr),
    )
    resp = await client.get("/api/v1/visits", headers=_auth_header(mr))
    assert resp.status_code == 200
    visit = resp.json()["data"][0]
    assert visit["doctor"]["full_name"] == "Dr. NamedArea"
    assert visit["doctor_id"] == str(doctor.id)


@pytest.mark.asyncio
async def test_overdue_planned_visits_become_missed_and_can_still_be_completed(client, db):
    admin = await _make_admin(db)
    mr = await _make_approved_mr(db)
    doctor = await _make_territory_with_doctor(db, admin.id, mr.id)
    past = (date.today() - timedelta(days=3)).isoformat()
    future = (date.today() + timedelta(days=3)).isoformat()
    for d in (past, future):
        await client.post("/api/v1/visits", json={"doctor_id": str(doctor.id), "scheduled_date": d}, headers=_auth_header(mr))

    resp = await client.get("/api/v1/visits", headers=_auth_header(mr))
    by_date = {v["scheduled_date"]: v for v in resp.json()["data"]}
    assert by_date[past]["status"] == "MISSED"
    assert by_date[future]["status"] == "PLANNED"

    late = await client.put(
        f"/api/v1/visits/{by_date[past]['id']}", json={"status": "COMPLETED", "outcome": "Logged late"},
        headers=_auth_header(mr),
    )
    assert late.status_code == 200
    assert late.json()["data"]["status"] == "COMPLETED"
