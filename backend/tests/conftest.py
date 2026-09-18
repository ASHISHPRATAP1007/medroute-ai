"""
Shared pytest fixtures.

These tests require a real PostgreSQL database (set DATABASE_URL to a
throwaway test database before running `pytest`) because the app uses
Postgres-only types (UUID, ENUM, INET) that don't work on SQLite. This
sandbox has no network/Postgres access, so these tests are written but
UNVERIFIED — run them yourself with a local Postgres instance:

    createdb medroute_test
    DATABASE_URL=postgresql+asyncpg://user:pass@localhost/medroute_test \\
        JWT_SECRET=test-secret pytest
"""
import asyncio

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Base, AsyncSessionLocal, engine
from app.main import app


@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
