"""
Application configuration.

All values are loaded from environment variables (see .env.example).
Nothing sensitive should ever be hardcoded here.
"""
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- App ---
    APP_NAME: str = "MedRoute AI"
    APP_ENV: str = "development"
    API_V1_PREFIX: str = "/api/v1"

    # --- Database ---
    DATABASE_URL: str  # e.g. postgresql+asyncpg://user:pass@localhost:5432/medroute

    # --- JWT ---
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # --- CORS ---
    CORS_ORIGINS: str = "http://localhost:3000"

    # --- Rate limiting ---
    LOGIN_RATE_LIMIT: str = "5/minute"
    REGISTER_RATE_LIMIT: str = "3/minute"

    # --- Phase 2: Google Places ---
    GOOGLE_PLACES_API_KEY: str = ""
    GOOGLE_PLACES_ENABLED: bool = False
    # Reviews are capped when cached — Google's terms restrict how many/how
    # long you may store, and we only need enough for a useful profile view.
    GOOGLE_PLACES_MAX_CACHED_REVIEWS: int = 5

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

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
