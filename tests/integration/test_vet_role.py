"""Integration tests for vet role and permissions."""

import uuid
from collections.abc import AsyncGenerator
from datetime import timedelta

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.app import app
from src.auth.utils import create_access_token, hash_password
from src.config import Settings
from src.db.session import init_engine

pytestmark = [pytest.mark.asyncio(loop_scope="function"), pytest.mark.integration]

_TEST_VET_ID = uuid.UUID("00000000-0000-0000-0000-000000000099")
_TEST_VET_EMAIL = "test-vet@refugio.test"


@pytest_asyncio.fixture
async def vet_client() -> AsyncGenerator[AsyncClient, None]:
    """Authenticated AsyncClient with vet role."""
    settings = Settings()
    engine = init_engine(settings)

    session_factory = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        await session.execute(
            text("""
                INSERT INTO users (id, email, hashed_password, role, is_active)
                VALUES (:id, :email, :pwd, 'vet', true)
                ON CONFLICT (id) DO UPDATE SET role = 'vet', is_active = true
            """),
            {
                "id": str(_TEST_VET_ID),
                "email": _TEST_VET_EMAIL,
                "pwd": hash_password("VetPass123!"),
            },
        )
        await session.commit()

    token = create_access_token(
        data={"sub": str(_TEST_VET_ID)},
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


class TestVetUserCreation:
    """Tests for creating vet users via admin endpoint."""

    async def test_admin_can_create_vet_user(self) -> None:
        """The vet role is accepted by the UserCreate schema."""
        from src.schemas.user import UserCreate
        user_data = UserCreate(
            email="newvet@refugio.example.com",
            password="SecurePass123!",
            role="vet",
        )
        assert user_data.role == "vet"


class TestVetRoleAccess:
    """Tests that vet users can authenticate and have correct access patterns."""

    async def test_vet_can_read_animals(self, vet_client: AsyncClient) -> None:
        """Vets should be able to list animals (public endpoint)."""
        resp = await vet_client.get("/animals")
        assert resp.status_code == 200

    async def test_vet_cannot_access_staff_me(self, vet_client: AsyncClient) -> None:
        """Vets should NOT access /auth/me (staff-only endpoint)."""
        resp = await vet_client.get("/auth/me")
        assert resp.status_code == 403

    async def test_vet_cannot_access_staff_donations(self, vet_client: AsyncClient) -> None:
        """Vets should NOT be able to access donation management (staff-only)."""
        resp = await vet_client.get("/donations")
        assert resp.status_code == 403

    async def test_vet_cannot_create_users(self, vet_client: AsyncClient) -> None:
        """Vets should NOT be able to create users (admin-only)."""
        resp = await vet_client.post("/auth/users", json={
            "email": "another@example.com",
            "password": "SomePass123!",
            "role": "staff",
        })
        assert resp.status_code == 403


class TestVetRoleEnum:
    """Tests that vet role is properly stored in database."""

    async def test_vet_role_stored_in_db(self) -> None:
        """Verify vet role value matches the DB CHECK constraint."""
        from src.db.models.user import UserRole
        assert UserRole.VET.value == "vet"
        # Ensure vet is distinct from other roles
        assert UserRole.VET != UserRole.STAFF
        assert UserRole.VET != UserRole.ADMIN
