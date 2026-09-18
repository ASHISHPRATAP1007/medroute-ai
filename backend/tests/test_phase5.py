import pytest

from app.core.security import create_access_token, hash_password


async def _make_admin(db):
    from app.models.user import User, UserRole, UserStatus
    admin = User(
        full_name="Admin", email="admin.p5@example.com", phone="9999900030",
        password_hash=hash_password("Admin@1234"), role=UserRole.ADMIN, status=UserStatus.APPROVED,
    )
    db.add(admin)
    await db.commit()
    await db.refresh(admin)
    return admin


async def _make_pending_mr(db):
    from app.models.user import User, UserRole, UserStatus
    mr = User(
        full_name="P5 MR", email="mr.p5@example.com", phone="9999900031",
        password_hash=hash_password("Mr@12345"), role=UserRole.MR, status=UserStatus.PENDING,
    )
    db.add(mr)
    await db.commit()
    await db.refresh(mr)
    return mr


def _auth_header(user):
    token = create_access_token(subject=str(user.id), role=user.role.value, status=user.status.value)
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_mr_performance_report_zero_for_new_mr(client, db):
    from app.models.user import UserStatus
    admin = await _make_admin(db)
    mr = await _make_pending_mr(db)
    mr.status = UserStatus.APPROVED
    await db.commit()

    resp = await client.get("/api/v1/admin/analytics/mr-performance", headers=_auth_header(admin))
    assert resp.status_code == 200
    report = next(r for r in resp.json()["data"] if r["mr_id"] == str(mr.id))
    assert report["visits_completed"] == 0
    assert report["completion_rate"] == 0.0
    assert report["last_visit_date"] is None


@pytest.mark.asyncio
async def test_territory_coverage_zero_percent_with_no_visits(client, db):
    from app.models.city import City
    from app.models.area import Area
    from app.models.territory import Territory
    from app.models.specialization import Specialization
    from app.models.doctor import Doctor

    admin = await _make_admin(db)
    city = City(name="P5City", state="P5State")
    db.add(city)
    await db.flush()
    area = Area(city_id=city.id, name="P5Area")
    db.add(area)
    await db.flush()
    territory = Territory(area_id=area.id, name="P5Territory")
    db.add(territory)
    await db.flush()
    spec = Specialization(name="P5Spec")
    db.add(spec)
    await db.flush()
    doctor = Doctor(
        full_name="Dr P5", specialization_id=spec.id, address="1 P5 St",
        area="P5Area", city="P5City", state="P5State", created_by=admin.id, updated_by=admin.id,
    )
    db.add(doctor)
    await db.commit()

    resp = await client.get("/api/v1/admin/analytics/territory-coverage", headers=_auth_header(admin))
    assert resp.status_code == 200
    report = next(r for r in resp.json()["data"] if r["territory_id"] == str(territory.id))
    assert report["total_active_doctors"] == 1
    assert report["doctors_visited"] == 0
    assert report["coverage_percent"] == 0.0


@pytest.mark.asyncio
async def test_csv_import_creates_valid_rows_and_reports_bad_ones(client, db):
    from app.models.specialization import Specialization
    admin = await _make_admin(db)
    spec = Specialization(name="Cardiologist")
    db.add(spec)
    await db.commit()

    csv_content = (
        "full_name,specialization,address,city,state\n"
        "Dr. Good One,Cardiologist,1 Main St,Lucknow,Uttar Pradesh\n"
        "Dr. Bad Spec,NotARealSpecialization,2 Main St,Lucknow,Uttar Pradesh\n"
        ",Cardiologist,3 Main St,Lucknow,Uttar Pradesh\n"  # missing full_name
    )
    files = {"file": ("doctors.csv", csv_content, "text/csv")}
    resp = await client.post("/api/v1/doctors/import", files=files, headers=_auth_header(admin))
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["created"] == 1
    assert data["skipped"] == 2
    assert len(data["errors"]) == 2


@pytest.mark.asyncio
async def test_csv_export_contains_header_and_created_doctor(client, db):
    from app.models.specialization import Specialization
    from app.models.doctor import Doctor
    admin = await _make_admin(db)
    spec = Specialization(name="Dermatologist")
    db.add(spec)
    await db.flush()
    doctor = Doctor(
        full_name="Dr. Export Me", specialization_id=spec.id, address="1 Export St",
        city="Lucknow", state="Uttar Pradesh", created_by=admin.id, updated_by=admin.id,
    )
    db.add(doctor)
    await db.commit()

    resp = await client.get("/api/v1/doctors/export", headers=_auth_header(admin))
    assert resp.status_code == 200
    body = resp.text
    assert "full_name" in body.splitlines()[0]
    assert "Dr. Export Me" in body


@pytest.mark.asyncio
async def test_mr_gets_notification_on_approval(client, db):
    admin = await _make_admin(db)
    mr = await _make_pending_mr(db)

    approve_resp = await client.post(f"/api/v1/admin/mrs/{mr.id}/approve", headers=_auth_header(admin))
    assert approve_resp.status_code == 200

    notif_resp = await client.get("/api/v1/notifications", headers=_auth_header(mr))
    assert notif_resp.status_code == 200
    notifications = notif_resp.json()["data"]
    assert any("approved" in n["title"].lower() for n in notifications)


@pytest.mark.asyncio
async def test_mark_notification_read(client, db):
    admin = await _make_admin(db)
    mr = await _make_pending_mr(db)
    await client.post(f"/api/v1/admin/mrs/{mr.id}/approve", headers=_auth_header(admin))

    before = await client.get("/api/v1/notifications/unread-count", headers=_auth_header(mr))
    assert before.json()["data"]["unread_count"] == 1

    notifications = (await client.get("/api/v1/notifications", headers=_auth_header(mr))).json()["data"]
    notification_id = notifications[0]["id"]

    mark_resp = await client.post(f"/api/v1/notifications/{notification_id}/read", headers=_auth_header(mr))
    assert mark_resp.status_code == 200

    after = await client.get("/api/v1/notifications/unread-count", headers=_auth_header(mr))
    assert after.json()["data"]["unread_count"] == 0
