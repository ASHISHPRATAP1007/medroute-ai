import pytest

from app.core.security import create_access_token, hash_password


async def _make_admin(db):
    from app.models.user import User, UserRole, UserStatus
    admin = User(
        full_name="Admin", email="admin@example.com", phone="9999999999",
        password_hash=hash_password("Admin@1234"), role=UserRole.ADMIN, status=UserStatus.APPROVED,
    )
    db.add(admin)
    await db.commit()
    await db.refresh(admin)
    return admin


async def _make_pending_mr(db):
    from app.models.user import User, UserRole, UserStatus
    mr = User(
        full_name="Pending MR", email="pending.mr@example.com", phone="9888888888",
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
async def test_admin_can_approve_pending_mr(client, db):
    admin = await _make_admin(db)
    mr = await _make_pending_mr(db)

    resp = await client.post(f"/api/v1/admin/mrs/{mr.id}/approve", headers=_auth_header(admin))
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "APPROVED"


@pytest.mark.asyncio
async def test_mr_cannot_access_admin_endpoint(client, db):
    mr = await _make_pending_mr(db)
    resp = await client.get("/api/v1/admin/mrs", headers=_auth_header(mr))
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_suspended_mr_is_blocked_from_protected_routes(client, db):
    from app.models.user import UserStatus
    mr = await _make_pending_mr(db)
    mr.status = UserStatus.SUSPENDED
    await db.commit()

    resp = await client.get("/api/v1/auth/me", headers=_auth_header(mr))
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_admin_list_mrs_filters_by_status(client, db):
    admin = await _make_admin(db)
    await _make_pending_mr(db)

    resp = await client.get("/api/v1/admin/mrs?status=PENDING", headers=_auth_header(admin))
    assert resp.status_code == 200
    body = resp.json()["data"]
    assert body["total_items"] == 1
    assert body["items"][0]["status"] == "PENDING"
