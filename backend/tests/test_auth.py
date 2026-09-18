import pytest

VALID_MR_PAYLOAD = {
    "full_name": "Test MR",
    "mobile_number": "9876543210",
    "email": "test.mr@example.com",
    "password": "StrongP@ss1",
    "confirm_password": "StrongP@ss1",
    "company_name": "Acme Pharma",
    "employee_id": "EMP001",
    "city": "Lucknow",
    "state": "Uttar Pradesh",
    "assigned_area": "Gomti Nagar",
}


@pytest.mark.asyncio
async def test_register_mr_creates_pending_account(client):
    resp = await client.post("/api/v1/auth/register", json=VALID_MR_PAYLOAD)
    assert resp.status_code == 201
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["status"] == "PENDING"


@pytest.mark.asyncio
async def test_register_rejects_mismatched_passwords(client):
    payload = dict(VALID_MR_PAYLOAD, confirm_password="Different@123")
    resp = await client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_register_rejects_invalid_mobile(client):
    payload = dict(VALID_MR_PAYLOAD, mobile_number="12345", email="other@example.com")
    resp = await client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_pending_mr_cannot_login(client):
    await client.post("/api/v1/auth/register", json=VALID_MR_PAYLOAD)
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": VALID_MR_PAYLOAD["email"], "password": VALID_MR_PAYLOAD["password"]},
    )
    assert resp.status_code == 403
    assert "pending" in resp.json()["message"].lower()


@pytest.mark.asyncio
async def test_login_with_wrong_password_fails(client):
    await client.post("/api/v1/auth/register", json=VALID_MR_PAYLOAD)
    resp = await client.post(
        "/api/v1/auth/login", json={"email": VALID_MR_PAYLOAD["email"], "password": "WrongPass@1"}
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token_rotation(client, db):
    from app.core.security import hash_password
    from app.models.user import User, UserRole, UserStatus
    from app.services.auth_service import issue_tokens

    user = User(
        full_name="Approved MR", email="approved@example.com", phone="9123456780",
        password_hash=hash_password("Whatever@123"), role=UserRole.MR, status=UserStatus.APPROVED,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    access1, refresh1 = await issue_tokens(db, user)

    resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh1})
    assert resp.status_code == 200
    new_tokens = resp.json()["data"]
    assert new_tokens["access_token"] != access1
    assert new_tokens["refresh_token"] != refresh1

    # The old refresh token must now be rejected (rotation/revocation).
    reuse_resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh1})
    assert reuse_resp.status_code == 401


@pytest.mark.asyncio
async def test_me_requires_auth(client):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401
