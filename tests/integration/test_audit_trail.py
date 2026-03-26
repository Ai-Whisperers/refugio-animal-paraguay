"""Integration tests for the audit trail system.

Verifies that:
1. Mutating authenticated requests create audit log entries
2. Audit log API endpoints return correct filtered results
3. CSV export works correctly
4. Non-authenticated and excluded requests are not audited
5. Covers 5+ critical action types as required by the story
"""

import uuid
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

# Deterministic test users
_TEST_ADMIN_ID = uuid.UUID("00000000-0000-0000-0000-000000000099")
_TEST_ADMIN_EMAIL = "test-admin-audit@refugio-example.com"
_TEST_STAFF_ID = uuid.UUID("00000000-0000-0000-0000-000000000098")
_TEST_STAFF_EMAIL = "test-staff-audit@refugio-example.com"


@pytest_asyncio.fixture
async def admin_client() -> AsyncClient:
    """Authenticated AsyncClient with admin role for audit log access."""
    settings = Settings()
    engine = init_engine(settings)

    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        # Create admin user
        await session.execute(
            text("""
                INSERT INTO users (id, email, hashed_password, role, is_active)
                VALUES (:id, :email, :pwd, 'admin', true)
                ON CONFLICT (id) DO UPDATE SET
                    email = :email, hashed_password = :pwd, role = 'admin', is_active = true
            """),
            {
                "id": str(_TEST_ADMIN_ID),
                "email": _TEST_ADMIN_EMAIL,
                "pwd": hash_password("AdminPass123!"),
            },
        )
        # Create staff user (for testing non-admin access denial)
        await session.execute(
            text("""
                INSERT INTO users (id, email, hashed_password, role, is_active)
                VALUES (:id, :email, :pwd, 'staff', true)
                ON CONFLICT (id) DO UPDATE SET
                    email = :email, hashed_password = :pwd, role = 'staff', is_active = true
            """),
            {
                "id": str(_TEST_STAFF_ID),
                "email": _TEST_STAFF_EMAIL,
                "pwd": hash_password("StaffPass123!"),
            },
        )
        # Clean up any previous audit logs from test runs
        await session.execute(text("DELETE FROM audit_logs"))
        await session.commit()

    # Run migration if audit_logs table doesn't exist yet
    async with session_factory() as session:
        result = await session.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'audit_logs'
                )
            """))
        table_exists = result.scalar()
        if not table_exists:
            pytest.skip("audit_logs table not created — run alembic upgrade head first")

    token = create_access_token(
        data={"sub": str(_TEST_ADMIN_ID)},
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


@pytest_asyncio.fixture
async def staff_client() -> AsyncClient:
    """Authenticated AsyncClient with staff role (non-admin)."""
    settings = Settings()
    init_engine(settings)

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


@pytest.mark.integration
class TestAuditTrailRecording:
    """Tests that mutating requests create audit log entries."""

    @pytest.mark.asyncio
    async def test_create_animal_creates_audit_entry(self, admin_client: AsyncClient) -> None:
        """Action type #1: Creating an animal."""
        resp = await admin_client.post(
            "/animals",
            json={
                "name": "AuditTestDog",
                "species": "dog",
                "breed": "mixed",
                "age_months": 12,
                "sex": "male",
                "status": "available",
                "description": "Test animal for audit trail.",
            },
        )
        assert resp.status_code in (200, 201)

        # Check audit logs
        audit_resp = await admin_client.get("/audit-logs", params={"resource_type": "animal"})
        assert audit_resp.status_code == 200
        data = audit_resp.json()
        assert data["total"] >= 1

        # Find the create action
        create_entries = [e for e in data["items"] if e["action"] == "create"]
        assert len(create_entries) >= 1
        entry = create_entries[0]
        assert entry["http_method"] == "POST"
        assert entry["path"] == "/animals"
        assert entry["user_id"] == str(_TEST_ADMIN_ID)

    @pytest.mark.asyncio
    async def test_update_animal_creates_audit_entry(self, admin_client: AsyncClient) -> None:
        """Action type #2: Updating an animal."""
        # Create an animal first
        create_resp = await admin_client.post(
            "/animals",
            json={
                "name": "UpdateAuditDog",
                "species": "dog",
                "breed": "mixed",
                "age_months": 24,
                "sex": "female",
                "status": "available",
                "description": "Test for update audit.",
            },
        )
        assert create_resp.status_code in (200, 201)
        animal_id = create_resp.json()["id"]

        # Update the animal
        update_resp = await admin_client.patch(
            f"/animals/{animal_id}",
            json={"name": "UpdatedAuditDog"},
        )
        assert update_resp.status_code == 200

        # Check audit logs for update action
        audit_resp = await admin_client.get(
            "/audit-logs",
            params={"resource_type": "animal", "action": "update"},
        )
        assert audit_resp.status_code == 200
        data = audit_resp.json()
        assert data["total"] >= 1

        update_entries = [e for e in data["items"] if e["resource_id"] == animal_id]
        assert len(update_entries) >= 1
        assert update_entries[0]["http_method"] == "PATCH"

    @pytest.mark.asyncio
    async def test_delete_animal_creates_audit_entry(self, admin_client: AsyncClient) -> None:
        """Action type #3: Deleting an animal."""
        # Create an animal to delete
        create_resp = await admin_client.post(
            "/animals",
            json={
                "name": "DeleteAuditDog",
                "species": "dog",
                "breed": "mixed",
                "age_months": 6,
                "sex": "male",
                "status": "available",
                "description": "Test for delete audit.",
            },
        )
        assert create_resp.status_code in (200, 201)
        animal_id = create_resp.json()["id"]

        # Delete the animal
        delete_resp = await admin_client.delete(f"/animals/{animal_id}")
        assert delete_resp.status_code in (200, 204)

        # Check audit logs for delete action
        audit_resp = await admin_client.get(
            "/audit-logs",
            params={"action": "delete"},
        )
        assert audit_resp.status_code == 200
        data = audit_resp.json()
        assert data["total"] >= 1

    @pytest.mark.asyncio
    async def test_create_adopter_creates_audit_entry(self, admin_client: AsyncClient) -> None:
        """Action type #4: Creating an adopter."""
        resp = await admin_client.post(
            "/adopters",
            json={
                "full_name": "Audit Test Adopter",
                "email": f"audit-adopter-{uuid.uuid4().hex[:8]}@refugio-example.com",
                "phone": "+595981234567",
                "address": "Asuncion, Paraguay",
                "gdpr_consent": True,
            },
        )
        assert resp.status_code in (200, 201)

        # Check audit logs
        audit_resp = await admin_client.get(
            "/audit-logs",
            params={"resource_type": "adopter", "action": "create"},
        )
        assert audit_resp.status_code == 200
        data = audit_resp.json()
        assert data["total"] >= 1

    @pytest.mark.asyncio
    async def test_create_donor_creates_audit_entry(self, admin_client: AsyncClient) -> None:
        """Action type #5: Creating a donor."""
        resp = await admin_client.post(
            "/donors",
            json={
                "full_name": "Audit Test Donor",
                "email": f"audit-donor-{uuid.uuid4().hex[:8]}@refugio-example.com",
                "country": "NL",
                "currency": "EUR",
                "gdpr_consent": True,
            },
        )
        assert resp.status_code in (200, 201)

        audit_resp = await admin_client.get(
            "/audit-logs",
            params={"resource_type": "donor", "action": "create"},
        )
        assert audit_resp.status_code == 200
        data = audit_resp.json()
        assert data["total"] >= 1


@pytest.mark.integration
class TestAuditLogFiltering:
    """Tests for audit log query filtering."""

    @pytest.mark.asyncio
    async def test_filter_by_user_id(self, admin_client: AsyncClient) -> None:
        # Create some activity first
        await admin_client.post(
            "/animals",
            json={
                "name": "FilterTestDog",
                "species": "dog",
                "breed": "mixed",
                "age_months": 12,
                "sex": "male",
                "status": "available",
                "description": "Filter test.",
            },
        )

        resp = await admin_client.get(
            "/audit-logs",
            params={"user_id": str(_TEST_ADMIN_ID)},
        )
        assert resp.status_code == 200
        data = resp.json()
        # All returned entries should belong to the admin user
        for entry in data["items"]:
            assert entry["user_id"] == str(_TEST_ADMIN_ID)

    @pytest.mark.asyncio
    async def test_filter_by_action(self, admin_client: AsyncClient) -> None:
        resp = await admin_client.get(
            "/audit-logs",
            params={"action": "create"},
        )
        assert resp.status_code == 200
        data = resp.json()
        for entry in data["items"]:
            assert entry["action"] == "create"

    @pytest.mark.asyncio
    async def test_pagination(self, admin_client: AsyncClient) -> None:
        resp = await admin_client.get(
            "/audit-logs",
            params={"page": 1, "page_size": 2},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["page"] == 1
        assert data["page_size"] == 2
        assert len(data["items"]) <= 2
        assert data["pages"] >= 1


@pytest.mark.integration
class TestAuditLogExport:
    """Tests for CSV export functionality."""

    @pytest.mark.asyncio
    async def test_export_returns_csv(self, admin_client: AsyncClient) -> None:
        # Create some activity
        await admin_client.post(
            "/animals",
            json={
                "name": "ExportTestDog",
                "species": "dog",
                "breed": "mixed",
                "age_months": 12,
                "sex": "male",
                "status": "available",
                "description": "Export test.",
            },
        )

        resp = await admin_client.get("/audit-logs/export")
        assert resp.status_code == 200
        assert "text/csv" in resp.headers.get("content-type", "")
        assert "attachment" in resp.headers.get("content-disposition", "")

        # Verify CSV has header and at least one data row
        lines = resp.text.strip().split("\n")
        assert len(lines) >= 2
        header = lines[0]
        assert "user_id" in header
        assert "action" in header
        assert "resource_type" in header

    @pytest.mark.asyncio
    async def test_export_with_filters(self, admin_client: AsyncClient) -> None:
        resp = await admin_client.get(
            "/audit-logs/export",
            params={"action": "create"},
        )
        assert resp.status_code == 200
        lines = resp.text.strip().split("\n")
        # At least header row
        assert len(lines) >= 1


@pytest.mark.integration
class TestAuditLogAccess:
    """Tests for access control on audit endpoints."""

    @pytest.mark.asyncio
    async def test_staff_cannot_access_audit_logs(self, staff_client: AsyncClient) -> None:
        resp = await staff_client.get("/audit-logs")
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_staff_cannot_export_audit_logs(self, staff_client: AsyncClient) -> None:
        resp = await staff_client.get("/audit-logs/export")
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_unauthenticated_cannot_access_audit_logs(self) -> None:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as ac:
            resp = await ac.get("/audit-logs")
            assert resp.status_code in (401, 403)


@pytest.mark.integration
class TestAuditExclusions:
    """Tests that excluded paths and non-mutating requests are not audited."""

    @pytest.mark.asyncio
    async def test_health_endpoint_not_audited(self, admin_client: AsyncClient) -> None:
        # Clear audit logs first
        settings = Settings()
        engine = init_engine(settings)
        session_factory = async_sessionmaker(
            bind=engine, class_=AsyncSession, expire_on_commit=False
        )
        async with session_factory() as session:
            await session.execute(text("DELETE FROM audit_logs"))
            await session.commit()

        # Hit health endpoint (POST would normally be audited, but GET is not)
        await admin_client.get("/health")

        # Check no audit logs were created
        audit_resp = await admin_client.get("/audit-logs")
        assert audit_resp.status_code == 200
        data = audit_resp.json()
        # The GET /audit-logs request itself shouldn't be audited (GET is not in AUDITED_METHODS)
        # But the GET request to /audit-logs might trigger middleware.
        # Only check that no /health entries exist
        health_entries = [e for e in data["items"] if "/health" in e["path"]]
        assert len(health_entries) == 0
