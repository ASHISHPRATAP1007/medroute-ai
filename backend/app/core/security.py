"""
Password hashing and JWT token utilities.

Design notes:
- Access tokens are short-lived and carry {sub, role, status, type: "access"}.
- Refresh tokens are opaque random strings stored (hashed) in the DB
  (see models/refresh_token.py) so they can be individually revoked and
  rotated on every use. The JWT itself is NOT used as the refresh token —
  this lets us revoke server-side without needing a blocklist of JWT ids.
"""
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import anyio
import bcrypt
from jose import JWTError, jwt

from app.core.config import get_settings

settings = get_settings()

# ---------- Passwords ----------
# We call the `bcrypt` library directly instead of going through passlib:
# passlib is unmaintained and breaks on bcrypt >= 4.1 (missing __about__)
# and bcrypt >= 5 (raises on >72-byte input). Hashes are standard $2b$
# strings, so existing password hashes created via passlib keep working.

_BCRYPT_MAX_BYTES = 72


def _pw_bytes(plain_password: str) -> bytes:
    # bcrypt only looks at the first 72 bytes; truncate explicitly so newer
    # bcrypt versions don't raise and behaviour matches what passlib did.
    return plain_password.encode("utf-8")[:_BCRYPT_MAX_BYTES]


def hash_password(plain_password: str) -> str:
    return bcrypt.hashpw(_pw_bytes(plain_password), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(_pw_bytes(plain_password), password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        # Malformed/legacy hash — treat as a failed login, never a 500.
        return False


# bcrypt is deliberately slow (~0.25 s per hash at the default cost). Calling
# it directly inside an async endpoint freezes the whole event loop for that
# time, stalling every other request. These wrappers run it in a worker
# thread instead (the bcrypt library releases the GIL while hashing).

async def hash_password_async(plain_password: str) -> str:
    return await anyio.to_thread.run_sync(hash_password, plain_password)


async def verify_password_async(plain_password: str, password_hash: str) -> bool:
    return await anyio.to_thread.run_sync(verify_password, plain_password, password_hash)


# Used when the email doesn't exist, so a failed login takes the same time
# either way and response timing can't reveal which emails are registered.
_DUMMY_HASH = hash_password("timing-equalizer-not-a-real-password")


async def verify_password_constant_time(plain_password: str, password_hash: str | None) -> bool:
    ok = await verify_password_async(plain_password, password_hash or _DUMMY_HASH)
    return ok and password_hash is not None


# ---------- Access tokens (JWT) ----------

def create_access_token(subject: str, role: str, status: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": subject,
        "role": role,
        "status": status,
        "type": "access",
        # Unique id per token: two tokens minted in the same second for the
        # same user would otherwise be byte-for-byte identical.
        "jti": secrets.token_hex(16),
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
    """
    Store only a keyed hash (HMAC-SHA256) of the refresh token, never the raw
    value. Refresh tokens are already 384 bits of randomness, so a slow
    password hash (bcrypt) adds nothing — and a deterministic HMAC lets us
    find the row with an indexed equality lookup instead of scanning and
    bcrypt-verifying every live token on each /auth/refresh (the old O(n)).
    """
    return hmac.new(
        settings.JWT_SECRET.encode("utf-8"), raw_token.encode("utf-8"), hashlib.sha256
    ).hexdigest()


def verify_refresh_token(raw_token: str, token_hash: str) -> bool:
    return hmac.compare_digest(hash_refresh_token(raw_token), token_hash)


def refresh_token_expiry() -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
