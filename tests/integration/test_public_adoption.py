"""Integration tests for public adoption application endpoint."""

import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from src.app import app
from src.config import Settings
from src.db.session import get_db, init_engine


@pytest_asyncio.fixture()
async def public_client():
    """Unauthenticated async HTTP client for public endpoint tests."""
    settings = Settings()
    init_engine(settings)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture()
async def seed_available_animal(public_client: AsyncClient):
    """Create an available animal for testing adoption applications."""
    animal_id = uuid.uuid4()

    async for session in get_db():
        db: AsyncSession = session
        await db.execute(
            text("""
                INSERT INTO animals (id, name, species, status, created_at, updated_at)
                VALUES (:id, :name, :species, :status, NOW(), NOW())
                ON CONFLICT (id) DO UPDATE SET status = :status
            """),
            {
                "id": str(animal_id),
                "name": "TestDog",
                "species": "dog",
                "status": "available",
            },
        )
        await db.commit()

    return animal_id


@pytest_asyncio.fixture()
async def seed_unavailable_animal(public_client: AsyncClient):
    """Create a non-available animal for testing rejection."""
    animal_id = uuid.uuid4()

    async for session in get_db():
        db: AsyncSession = session
        await db.execute(
            text("""
                INSERT INTO animals (id, name, species, status, created_at, updated_at)
                VALUES (:id, :name, :species, :status, NOW(), NOW())
                ON CONFLICT (id) DO UPDATE SET status = :status
            """),
            {
                "id": str(animal_id),
                "name": "SickCat",
                "species": "cat",
                "status": "under_treatment",
            },
        )
        await db.commit()

    return animal_id


@pytest.mark.asyncio
async def test_submit_adoption_application_success(
    public_client: AsyncClient, seed_available_animal: uuid.UUID
):
    """Successful adoption application creates adopter + request."""
    response = await public_client.post(
        "/public/adoption-applications",
        json={
            "animal_id": str(seed_available_animal),
            "full_name": "Maria Garcia",
            "email": f"maria-{uuid.uuid4().hex[:8]}@example.com",
            "phone": "+595981123456",
            "message": "I would love to adopt this dog!",
            "gdpr_consent": True,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "pending"
    assert data["animal_id"] == str(seed_available_animal)
    assert "id" in data
    assert "submitted_at" in data


@pytest.mark.asyncio
async def test_submit_adoption_application_minimal(
    public_client: AsyncClient, seed_available_animal: uuid.UUID
):
    """Minimal application (no phone or message) succeeds."""
    response = await public_client.post(
        "/public/adoption-applications",
        json={
            "animal_id": str(seed_available_animal),
            "full_name": "Juan Lopez",
            "email": f"juan-{uuid.uuid4().hex[:8]}@example.com",
            "gdpr_consent": True,
        },
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_submit_adoption_no_gdpr_consent_rejected(
    public_client: AsyncClient, seed_available_animal: uuid.UUID
):
    """Application without GDPR consent is rejected."""
    response = await public_client.post(
        "/public/adoption-applications",
        json={
            "animal_id": str(seed_available_animal),
            "full_name": "Test User",
            "email": "test@example.com",
            "gdpr_consent": False,
        },
    )
    assert response.status_code == 422
    assert "GDPR consent" in response.json()["message"]


@pytest.mark.asyncio
async def test_submit_adoption_nonexistent_animal(public_client: AsyncClient):
    """Application for non-existent animal returns 404."""
    response = await public_client.post(
        "/public/adoption-applications",
        json={
            "animal_id": str(uuid.uuid4()),
            "full_name": "Test User",
            "email": "test@example.com",
            "gdpr_consent": True,
        },
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_submit_adoption_unavailable_animal(
    public_client: AsyncClient, seed_unavailable_animal: uuid.UUID
):
    """Application for non-available animal is rejected."""
    response = await public_client.post(
        "/public/adoption-applications",
        json={
            "animal_id": str(seed_unavailable_animal),
            "full_name": "Test User",
            "email": f"test-{uuid.uuid4().hex[:8]}@example.com",
            "gdpr_consent": True,
        },
    )
    assert response.status_code == 422
    assert "not currently available" in response.json()["message"]


@pytest.mark.asyncio
async def test_submit_adoption_duplicate_pending_rejected(
    public_client: AsyncClient, seed_available_animal: uuid.UUID
):
    """Duplicate pending application for same animal is rejected."""
    unique_email = f"dup-{uuid.uuid4().hex[:8]}@example.com"
    payload = {
        "animal_id": str(seed_available_animal),
        "full_name": "Duplicate Tester",
        "email": unique_email,
        "gdpr_consent": True,
    }

    # First submission succeeds
    first = await public_client.post("/public/adoption-applications", json=payload)
    assert first.status_code == 201

    # Second submission for same animal+email is rejected
    second = await public_client.post("/public/adoption-applications", json=payload)
    assert second.status_code == 409
    assert "already have a pending" in second.json()["message"]


@pytest.mark.asyncio
async def test_submit_adoption_invalid_email(
    public_client: AsyncClient, seed_available_animal: uuid.UUID
):
    """Invalid email format returns 422."""
    response = await public_client.post(
        "/public/adoption-applications",
        json={
            "animal_id": str(seed_available_animal),
            "full_name": "Test User",
            "email": "not-an-email",
            "gdpr_consent": True,
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_submit_adoption_missing_name(
    public_client: AsyncClient, seed_available_animal: uuid.UUID
):
    """Missing name returns 422."""
    response = await public_client.post(
        "/public/adoption-applications",
        json={
            "animal_id": str(seed_available_animal),
            "email": "test@example.com",
            "gdpr_consent": True,
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_submit_adoption_no_auth_required(
    public_client: AsyncClient, seed_available_animal: uuid.UUID
):
    """Endpoint works without any auth headers."""
    response = await public_client.post(
        "/public/adoption-applications",
        json={
            "animal_id": str(seed_available_animal),
            "full_name": "No Auth User",
            "email": f"noauth-{uuid.uuid4().hex[:8]}@example.com",
            "gdpr_consent": True,
        },
    )
    # Should not get 401 or 403
    assert response.status_code in (201, 409)
