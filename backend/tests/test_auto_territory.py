"""Approving an MR auto-assigns a territory from their registered city/area."""
import pytest

from app.core.security import create_access_token, hash_password


def _auth(user_id, role, status):
    return {"Authorization": f"Bearer {create_access_token(subject=str(user_id), role=role, status=status)}"}


def _payload(email, phone, emp, area="  gomti   NAGAR "):
    return {
        "full_name": "Field MR", "mobile_number": phone, "email": email,
        "password": "StrongP@ss1", "confirm_password": "StrongP@ss1",
        "company_name": "Acme Pharma", "employee_id": emp,
        "city": "lucknow", "state": "Uttar Pradesh", "assigned_area": area,
    }


@pytest.mark.asyncio
async def test_approval_assigns_territory_and_mr_sees_area_doctors(client, db):
    from sqlalchemy import select
    from app.core.config import get_settings
    from app.models.doctor import Doctor
    from app.models.specialization import Specialization
    from app.models.territory import Territory
    from app.models.user import User, UserRole, UserStatus
    from app.api.v1.auth import limiter

    limiter.enabled = False  # several registrations in one test
    try:
        admin = User(full_name="Admin", email="admin.auto@example.com", phone="9000000301",
                     password_hash=hash_password("Admin@1234"), role=UserRole.ADMIN, status=UserStatus.APPROVED)
        spec = Specialization(name="Spec-Auto")
        db.add_all([admin, spec])
        await db.flush()
        # Doctors typed by the admin with different spacing/case than the MR used.
        db.add_all([
            Doctor(full_name="Dr. In Area", specialization_id=spec.id, address="1 St", area="Gomti Nagar",
                   city="Lucknow", state="UP", latitude=26.85, longitude=81.01),
            Doctor(full_name="Dr. Elsewhere", specialization_id=spec.id, address="2 St", area="Aliganj",
                   city="Lucknow", state="UP"),
        ])
        await db.commit()
        admin_h = _auth(admin.id, "ADMIN", "APPROVED")

        reg = await client.post("/api/v1/auth/register", json=_payload("m1.auto@example.com", "9000000302", "A1"))
        assert reg.status_code == 201, reg.text
        mr_id = reg.json()["data"]["id"]

        approve = await client.post(f"/api/v1/admin/mrs/{mr_id}/approve", headers=admin_h)
        assert approve.status_code == 200, approve.text
        assert "Gomti Nagar Territory" in approve.json()["message"]

        mr_h = _auth(mr_id, "MR", "APPROVED")
        mine = await client.get("/api/v1/doctors/mine?page_size=100", headers=mr_h)
        assert [d["full_name"] for d in mine.json()["data"]["items"]] == ["Dr. In Area"]

        dash = await client.get("/api/v1/mr/dashboard", headers=mr_h)
        assert dash.json()["data"]["assigned_territory_count"] == 1
        assert dash.json()["data"]["total_doctors"] == 1

        notes = await client.get("/api/v1/notifications", headers=mr_h)
        assert any(n["title"] == "Territory assigned" for n in notes.json()["data"])

        # A second MR from the same area reuses the same territory.
        reg2 = await client.post("/api/v1/auth/register", json=_payload("m2.auto@example.com", "9000000303", "A2", area="Gomti Nagar"))
        await client.post(f"/api/v1/admin/mrs/{reg2.json()['data']['id']}/approve", headers=admin_h)
        territories = (await db.execute(select(Territory))).scalars().all()
        assert len(territories) == 1
    finally:
        limiter.enabled = True
