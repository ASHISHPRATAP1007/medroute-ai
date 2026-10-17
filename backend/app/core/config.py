"""
Application configuration.

All values are loaded from environment variables (see .env.example).
Nothing sensitive should ever be hardcoded here.
"""
from datetime import date, datetime
from functools import lru_cache
from zoneinfo import ZoneInfo
from typing import List
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _asyncpg_compatible_query(url: str) -> str:
    """
    asyncpg doesn't understand libpq query params that Neon/Render put in
    their connection strings (`sslmode=require`, `channel_binding=require`)
    and fails at connect time. Translate sslmode -> ssl and drop the rest.
    """
    parts = urlsplit(url)
    if not parts.query:
        return url
    params = []
    for key, value in parse_qsl(parts.query, keep_blank_values=True):
        if key == "sslmode":
            if value != "disable":
                params.append(("ssl", "require" if value in ("require", "prefer", "allow") else value))
        elif key in ("channel_binding", "gssencmode", "target_session_attrs"):
            continue
        else:
            params.append((key, value))
    return urlunsplit(parts._replace(query=urlencode(params)))


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- App ---
    APP_NAME: str = "MedRoute AI"
    APP_ENV: str = "development"
    API_V1_PREFIX: str = "/api/v1"

    # --- Database ---
    DATABASE_URL: str  # e.g. postgresql+asyncpg://user:pass@localhost:5432/medroute
    SQL_ECHO: bool = False  # log every SQL statement (noisy; debugging only)

    # --- JWT ---
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Business timezone: decides what "today" is for visits (planned visits
    # from earlier days become MISSED, follow-ups are "upcoming", etc.).
    APP_TIMEZONE: str = "Asia/Kolkata"

    # --- CORS ---
    CORS_ORIGINS: str = "http://localhost:3000"

    # --- Rate limiting ---
    LOGIN_RATE_LIMIT: str = "5/minute"
    REGISTER_RATE_LIMIT: str = "3/minute"

    # --- First-run bootstrap (python -m app.bootstrap, run on container start) ---
    # If no SUPER_ADMIN exists yet and both of these are set, one is created.
    INITIAL_ADMIN_EMAIL: str = ""
    INITIAL_ADMIN_PASSWORD: str = ""
    INITIAL_ADMIN_NAME: str = "Super Admin"
    INITIAL_ADMIN_PHONE: str = "9000000000"
    # Load the public demo dataset (Demo@1234 accounts). Never in production.
    SEED_DEMO_DATA: bool = False

    # --- Phase 2: Google Places ---
    GOOGLE_PLACES_API_KEY: str = ""
    GOOGLE_PLACES_ENABLED: bool = False
    # Reviews are capped when cached — Google's terms restrict how many/how
    # long you may store, and we only need enough for a useful profile view.
    GOOGLE_PLACES_MAX_CACHED_REVIEWS: int = 5

    @model_validator(mode="after")
    def _normalize_and_check(self) -> "Settings":
        # Render/Heroku/Neon hand out "postgres://" or "postgresql://" URLs;
        # SQLAlchemy's async engine needs an explicit async driver.
        url = self.DATABASE_URL
        if url.startswith("postgres://"):
            url = "postgresql://" + url[len("postgres://"):]
        if url.startswith("postgresql://"):
            url = "postgresql+asyncpg://" + url[len("postgresql://"):]
        if url.startswith("postgresql+asyncpg://"):
            url = _asyncpg_compatible_query(url)
        self.DATABASE_URL = url

        if self.is_production:
            weak = {"", "change-this-to-a-long-random-value", "test-secret", "secret"}
            if self.JWT_SECRET in weak or len(self.JWT_SECRET) < 32:
                raise ValueError(
                    "JWT_SECRET is missing or too weak for APP_ENV=production — "
                    "generate one with: python -c \"import secrets; print(secrets.token_urlsafe(64))\""
                )
        return self

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    def today(self) -> date:
        return datetime.now(ZoneInfo(self.APP_TIMEZONE)).date()

    @property
    def is_production(self) -> bool:
        return self.APP_ENV.lower() == "production"

    @property
    def google_places_configured(self) -> bool:
        return bool(self.GOOGLE_PLACES_ENABLED and self.GOOGLE_PLACES_API_KEY)


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance — env is read once per process."""
    return Settings()
