"""
Domain logic for authentication. Kept out of the API layer so routes
stay thin (per project rules).
"""
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    generate_refresh_token_value,
    hash_password,
    hash_refresh_token,
    refresh_token_expiry,
    verify_password,
    verify_refresh_token,
)
from app.models.mr_profile import MRProfile
from app.models.refresh_token import RefreshToken
from app.models.user import User, UserRole, UserStatus
from app.schemas.auth import MRRegisterRequest
from app.services.audit_service import log_action
from app.models.audit_log import AuditAction


async def register_mr(db: AsyncSession, payload: MRRegisterRequest) -> User:
    existing = await db.execute(
        select(User).where((User.email == payload.email) | (User.phone == payload.mobile_number))
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email or mobile number already exists.",
        )

    user = User(
        full_name=payload.full_name,
        email=payload.email,
        phone=payload.mobile_number,
        password_hash=hash_password(payload.password),
        role=UserRole.MR,
        status=UserStatus.PENDING,
    )
    db.add(user)
    await db.flush()  # get user.id before creating dependent row

    profile = MRProfile(
        user_id=user.id,
        company_name=payload.company_name,
        employee_id=payload.employee_id,
        city=payload.city,
        state=payload.state,
        assigned_area=payload.assigned_area,
    )
    db.add(profile)

    await log_action(db, user_id=user.id, action=AuditAction.USER_REGISTERED,
                      entity_type="User", entity_id=user.id,
                      description=f"MR self-registered: {user.email}")

    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    invalid_credentials = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password."
    )
    if user is None or not verify_password(password, user.password_hash):
        raise invalid_credentials

    if user.role == UserRole.MR:
        if user.status == UserStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your account is pending admin approval.",
            )
        if user.status == UserStatus.REJECTED:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your registration was rejected. Contact your administrator.",
            )
        if user.status == UserStatus.SUSPENDED:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your account has been suspended. Contact your administrator.",
            )
        if user.status != UserStatus.APPROVED:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account not active.")

    if not user.is_active:
        raise invalid_credentials

    user.last_login_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(user)
    return user


async def issue_tokens(db: AsyncSession, user: User) -> tuple[str, str]:
    access_token = create_access_token(subject=str(user.id), role=user.role.value, status=user.status.value)

    raw_refresh = generate_refresh_token_value()
    token_row = RefreshToken(
        user_id=user.id,
        token_hash=hash_refresh_token(raw_refresh),
        expires_at=refresh_token_expiry(),
    )
    db.add(token_row)
    await db.commit()

    return access_token, raw_refresh


async def rotate_refresh_token(db: AsyncSession, raw_refresh_token: str) -> tuple[str, str]:
    """Validate the presented refresh token, revoke it, and issue a fresh pair."""
    invalid = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token.")

    result = await db.execute(
        select(RefreshToken).where(RefreshToken.revoked == False)  # noqa: E712
    )
    candidates = result.scalars().all()

    matched: RefreshToken | None = None
    for candidate in candidates:
        if verify_refresh_token(raw_refresh_token, candidate.token_hash):
            matched = candidate
            break

    if matched is None:
        raise invalid
    if matched.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise invalid

    user_result = await db.execute(select(User).where(User.id == matched.user_id))
    user = user_result.scalar_one_or_none()
    if user is None or not user.is_active or user.status == UserStatus.SUSPENDED:
        raise invalid

    # Rotate: revoke the used token, issue a brand new pair.
    matched.revoked = True
    matched.revoked_at = datetime.now(timezone.utc)
    await db.commit()

    return await issue_tokens(db, user)


async def revoke_all_refresh_tokens_for_raw(db: AsyncSession, raw_refresh_token: str) -> None:
    """Used on logout — revokes just the presented token."""
    result = await db.execute(select(RefreshToken).where(RefreshToken.revoked == False))  # noqa: E712
    for candidate in result.scalars().all():
        if verify_refresh_token(raw_refresh_token, candidate.token_hash):
            candidate.revoked = True
            candidate.revoked_at = datetime.now(timezone.utc)
            await db.commit()
            return
