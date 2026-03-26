"""Shared fixtures for integration tests.

All integration tests require a live PostgreSQL database (refugio_dev).
The `client` fixture creates an authenticated AsyncClient pre-loaded with
a staff JWT so mutation endpoints (POST/PATCH/DELETE) work without
per-test auth setup.
"""

import uuid
from collections.abc import AsyncGenerator
from datetime import timedelta

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from src.app import app
from src.auth.utils import create_access_token, hash_password
from src.config import Settings
from src.db.session import init_engine

# Deterministic test user — created once, reused across all test runs.
_TEST_STAFF_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
_TEST_STAFF_EMAIL = "test-staff@refugio.test"


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Authenticated AsyncClient wired to the live test database.

    Creates a deterministic staff user if it does not yet exist, mints a
    JWT for that user, and injects the Bearer token into every request so
    mutation endpoints don't return 401.
    """
    settings = Settings()
    engine = init_engine(settings)

    # Upsert test staff user (ON CONFLICT keeps idempotent across runs)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        await session.execute(
            text("""
                INSERT INTO users (id, email, hashed_password, role, is_active)
                VALUES (:id, :email, :pwd, 'staff', true)
                ON CONFLICT (email) DO NOTHING
                """),
            {
                "id": str(_TEST_STAFF_ID),
                "email": _TEST_STAFF_EMAIL,
                "pwd": hash_password("TestPass123!"),
            },
        )
        await session.commit()

    token = create_access_token(
        data={"sub": str(_TEST_STAFF_ID)},
        secret_key=settings.secret_key,
        algorithm=settings.algorithm,
        expires_delta=timedelta(minutes=30),
    )

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"Authorization": f"Bearer {token}"},
    ) as ac:
        yield ac
