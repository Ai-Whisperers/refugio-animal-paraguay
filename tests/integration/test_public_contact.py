"""Integration tests for public contact and inquiry form endpoints."""

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
async def seed_animal(public_client: AsyncClient):
    """Create an animal for testing inquiry submissions."""
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


VALID_CONTACT_PAYLOAD = {
    "visitor_name": "Maria Garcia",
    "visitor_email": "maria@example.com",
    "subject": "Adoption inquiry about your shelter",
    "message": "I would like to know more about your adoption process and requirements.",
}


# --- Contact Form Tests ---


@pytest.mark.asyncio
async def test_submit_contact_form_success(public_client: AsyncClient):
    """Successful contact form submission returns 201."""
    payload = {
        **VALID_CONTACT_PAYLOAD,
        "visitor_email": f"contact-{uuid.uuid4().hex[:8]}@example.com",
    }
    response = await public_client.post("/public/contact", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["form_type"] == "general"
    assert "id" in data
    assert "submitted_at" in data


@pytest.mark.asyncio
async def test_submit_contact_missing_subject(public_client: AsyncClient):
    """Contact form without subject returns 422."""
    payload = {
        "visitor_name": "Test User",
        "visitor_email": "test@example.com",
        "message": "This is a valid message body text.",
    }
    response = await public_client.post("/public/contact", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_submit_contact_message_too_short(public_client: AsyncClient):
    """Contact form with message under 20 chars returns 422."""
    payload = {
        **VALID_CONTACT_PAYLOAD,
        "message": "Too short",
    }
    response = await public_client.post("/public/contact", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_submit_contact_name_too_short(public_client: AsyncClient):
    """Contact form with name under 3 chars returns 422."""
    payload = {
        **VALID_CONTACT_PAYLOAD,
        "visitor_name": "AB",
    }
    response = await public_client.post("/public/contact", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_submit_contact_invalid_email(public_client: AsyncClient):
    """Contact form with invalid email returns 422."""
    payload = {
        **VALID_CONTACT_PAYLOAD,
        "visitor_email": "not-an-email",
    }
    response = await public_client.post("/public/contact", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_submit_contact_no_auth_required(public_client: AsyncClient):
    """Contact form works without any auth headers."""
    payload = {
        **VALID_CONTACT_PAYLOAD,
        "visitor_email": f"noauth-{uuid.uuid4().hex[:8]}@example.com",
    }
    response = await public_client.post("/public/contact", json=payload)
    assert response.status_code in (201, 429)


# --- Animal Inquiry Tests ---


@pytest.mark.asyncio
async def test_submit_animal_inquiry_success(public_client: AsyncClient, seed_animal: uuid.UUID):
    """Successful animal inquiry returns 201."""
    payload = {
        "visitor_name": "Juan Lopez",
        "visitor_email": f"inquiry-{uuid.uuid4().hex[:8]}@example.com",
        "message": "I am very interested in adopting this animal. Can you tell me more?",
    }
    response = await public_client.post(f"/public/animals/{seed_animal}/inquiries", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["form_type"] == "animal_inquiry"
    assert "id" in data


@pytest.mark.asyncio
async def test_submit_animal_inquiry_nonexistent_animal(
    public_client: AsyncClient,
):
    """Inquiry for non-existent animal returns 404."""
    payload = {
        "visitor_name": "Test User",
        "visitor_email": "test@example.com",
        "message": "I am interested in adopting this animal please.",
    }
    response = await public_client.post(f"/public/animals/{uuid.uuid4()}/inquiries", json=payload)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_submit_animal_inquiry_invalid_message(
    public_client: AsyncClient, seed_animal: uuid.UUID
):
    """Inquiry with too-short message returns 422."""
    payload = {
        "visitor_name": "Test User",
        "visitor_email": "test@example.com",
        "message": "Too short",
    }
    response = await public_client.post(f"/public/animals/{seed_animal}/inquiries", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_submit_animal_inquiry_no_auth_required(
    public_client: AsyncClient, seed_animal: uuid.UUID
):
    """Inquiry endpoint works without auth headers."""
    payload = {
        "visitor_name": "No Auth User",
        "visitor_email": f"noauth-{uuid.uuid4().hex[:8]}@example.com",
        "message": "I would like to learn more about this animal please.",
    }
    response = await public_client.post(f"/public/animals/{seed_animal}/inquiries", json=payload)
    assert response.status_code in (201, 429)
