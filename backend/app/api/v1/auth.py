from fastapi import APIRouter, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.config import get_settings
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    MRRegisterRequest,
    RefreshRequest,
    TokenResponse,
    UserPublic,
)
from app.schemas.common import ApiResponse
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])
settings = get_settings()
limiter = Limiter(key_func=get_remote_address)


@router.post("/register", response_model=ApiResponse[UserPublic], status_code=201)
@limiter.limit(settings.REGISTER_RATE_LIMIT)
async def register(request: Request, payload: MRRegisterRequest, db: AsyncSession = Depends(get_db)):
    """MR self-registration. Account is created with status=PENDING."""
    user = await auth_service.register_mr(db, payload)
    return ApiResponse(
        message="Registration submitted successfully. Your account is waiting for admin approval.",
        data=UserPublic.model_validate(user),
    )


@router.post("/login", response_model=ApiResponse[TokenResponse])
@limiter.limit(settings.LOGIN_RATE_LIMIT)
async def login(request: Request, payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await auth_service.authenticate_user(db, payload.email, payload.password)
    access_token, refresh_token = await auth_service.issue_tokens(db, user)
    return ApiResponse(data=TokenResponse(access_token=access_token, refresh_token=refresh_token))


@router.post("/refresh", response_model=ApiResponse[TokenResponse])
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    access_token, refresh_token = await auth_service.rotate_refresh_token(db, payload.refresh_token)
    return ApiResponse(data=TokenResponse(access_token=access_token, refresh_token=refresh_token))


@router.post("/logout", response_model=ApiResponse[None])
async def logout(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    await auth_service.revoke_all_refresh_tokens_for_raw(db, payload.refresh_token)
    return ApiResponse(message="Logged out successfully.")


@router.get("/me", response_model=ApiResponse[UserPublic])
async def me(current_user: User = Depends(get_current_user)):
    return ApiResponse(data=UserPublic.model_validate(current_user))
