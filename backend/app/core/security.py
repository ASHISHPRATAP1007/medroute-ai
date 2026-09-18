"""
Password hashing and JWT token utilities.

Design notes:
- Access tokens are short-lived and carry {sub, role, status, type: "access"}.
- Refresh tokens are opaque random strings stored (hashed) in the DB
  (see models/refresh_token.py) so they can be individually revoked and
  rotated on every use. The JWT itself is NOT used as the refresh token —
  this lets us revoke server-side without needing a blocklist of JWT ids.
"""
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

settings = get_settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ---------- Passwords ----------

def hash_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)


# ---------- Access tokens (JWT) ----------

def create_access_token(subject: str, role: str, status: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": subject,
        "role": role,
        "status": status,
        "type": "access",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[dict[str, Any]]:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        if payload.get("type") != "access":
            return None
        return payload
    except JWTError:
        return None


# ---------- Refresh tokens (opaque, DB-backed) ----------

def generate_refresh_token_value() -> str:
    """A high-entropy opaque token — the raw value returned to the client."""
    return secrets.token_urlsafe(48)


def hash_refresh_token(raw_token: str) -> str:
    """Store only a hash of the refresh token in the DB, never the raw value."""
    return pwd_context.hash(raw_token)


def verify_refresh_token(raw_token: str, token_hash: str) -> bool:
    return pwd_context.verify(raw_token, token_hash)


def refresh_token_expiry() -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
