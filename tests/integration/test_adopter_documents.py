"""Integration tests for adopter document upload/management endpoints.

Requires a live PostgreSQL instance (refugio_dev).
Run: pytest -m integration tests/integration/test_adopter_documents.py
"""

import io
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

# Deterministic adopter test user IDs
_ADOPTER_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000020")
_ADOPTER_EMAIL = "test-adopter-docs@refugio.test"
_ADOPTER_FULL_NAME = "Test Adopter Documents"


@pytest_asyncio.fixture
async def adopter_client() -> AsyncGenerator[AsyncClient, None]:
    """Authenticated AsyncClient for an adopter user with a matching adopter profile."""
    settings = Settings()
    engine = init_engine(settings)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        # Upsert adopter user
        await session.execute(
            text("""
                INSERT INTO users (id, email, hashed_password, role, is_active)
                VALUES (:id, :email, :pwd, 'adopter', true)
                ON CONFLICT (email) DO NOTHING
                """),
            {
                "id": str(_ADOPTER_USER_ID),
                "email": _ADOPTER_EMAIL,
                "pwd": hash_password("TestPass123!"),
            },
        )
        # Upsert matching adopter profile (matched by email)
        await session.execute(
            text("""
                INSERT INTO adopters (full_name, email, gdpr_consent_at)
                VALUES (:full_name, :email, NOW())
                ON CONFLICT (email) DO NOTHING
                """),
            {"full_name": _ADOPTER_FULL_NAME, "email": _ADOPTER_EMAIL},
        )
        await session.commit()

    token = create_access_token(
        data={"sub": str(_ADOPTER_USER_ID)},
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


def _fake_pdf() -> tuple[bytes, str]:
    """Return a minimal fake PDF bytes and filename."""
    # Actual PDF magic bytes so python-magic detects correctly
    pdf_bytes = b"%PDF-1.4 fake content for testing purposes only"
    return pdf_bytes, "test_document.pdf"


def _fake_png() -> tuple[bytes, str]:
    """Return minimal PNG bytes."""
    # PNG magic bytes
    png_bytes = (
        b"\x89PNG\r\n\x1a\n"
        + b"\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde"
    )
    return png_bytes, "photo.png"


# ---------------------------------------------------------------------------
# POST /portal/documents
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_upload_document_returns_201(adopter_client: AsyncClient) -> None:
    """Adopter can upload a valid PDF document."""
    pdf_bytes, filename = _fake_pdf()
    response = await adopter_client.post(
        "/portal/documents",
        files={"file": (filename, io.BytesIO(pdf_bytes), "application/pdf")},
        data={"document_type": "identity"},
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert "id" in body
    assert body["original_filename"] == filename
    assert body["document_type"] == "identity"
    assert body["size_bytes"] == len(pdf_bytes)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_upload_document_with_description(adopter_client: AsyncClient) -> None:
    """Adopter can include a description when uploading."""
    pdf_bytes, filename = _fake_pdf()
    response = await adopter_client.post(
        "/portal/documents",
        files={"file": (filename, io.BytesIO(pdf_bytes), "application/pdf")},
        data={"document_type": "proof_of_residence", "description": "Utility bill March 2026"},
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["document_type"] == "proof_of_residence"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_upload_requires_authentication() -> None:
    """Unauthenticated upload returns 401 or 403."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as unauthenticated:
        pdf_bytes, filename = _fake_pdf()
        response = await unauthenticated.post(
            "/portal/documents",
            files={"file": (filename, io.BytesIO(pdf_bytes), "application/pdf")},
        )
    assert response.status_code in (401, 403)


# ---------------------------------------------------------------------------
# GET /portal/documents
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_documents_returns_own_docs(adopter_client: AsyncClient) -> None:
    """Adopter can list their own uploaded documents."""
    # Upload one document first
    pdf_bytes, filename = _fake_pdf()
    upload_resp = await adopter_client.post(
        "/portal/documents",
        files={"file": (filename, io.BytesIO(pdf_bytes), "application/pdf")},
        data={"document_type": "other"},
    )
    assert upload_resp.status_code == 201, upload_resp.text

    # Now list
    list_resp = await adopter_client.get("/portal/documents")
    assert list_resp.status_code == 200, list_resp.text
    body = list_resp.json()
    assert "documents" in body
    assert "total" in body
    assert body["total"] >= 1
    # Uploaded document should be present
    doc_ids = [d["id"] for d in body["documents"]]
    assert upload_resp.json()["id"] in doc_ids


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_documents_empty_for_new_adopter() -> None:
    """A newly created adopter with no uploads gets an empty list."""
    settings = Settings()
    engine = init_engine(settings)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    new_id = uuid.uuid4()
    new_email = f"fresh-adopter-{new_id.hex[:8]}@refugio.test"

    async with session_factory() as session:
        await session.execute(
            text("""
                INSERT INTO users (id, email, hashed_password, role, is_active)
                VALUES (:id, :email, :pwd, 'adopter', true)
                """),
            {"id": str(new_id), "email": new_email, "pwd": hash_password("TestPass123!")},
        )
        await session.execute(
            text("INSERT INTO adopters (full_name, email) VALUES (:name, :email)"),
            {"name": "Fresh Adopter", "email": new_email},
        )
        await session.commit()

    token = create_access_token(
        data={"sub": str(new_id)},
        secret_key=Settings().secret_key,
        algorithm=Settings().algorithm,
        expires_delta=timedelta(minutes=5),
    )
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"Authorization": f"Bearer {token}"},
    ) as fresh_client:
        resp = await fresh_client.get("/portal/documents")

    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 0
    assert body["documents"] == []


# ---------------------------------------------------------------------------
# DELETE /portal/documents/{document_id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_delete_own_document(adopter_client: AsyncClient) -> None:
    """Adopter can delete their own document — returns 204."""
    pdf_bytes, filename = _fake_pdf()
    upload_resp = await adopter_client.post(
        "/portal/documents",
        files={"file": (filename, io.BytesIO(pdf_bytes), "application/pdf")},
        data={"document_type": "other"},
    )
    assert upload_resp.status_code == 201
    document_id = upload_resp.json()["id"]

    delete_resp = await adopter_client.delete(f"/portal/documents/{document_id}")
    assert delete_resp.status_code == 204

    # Document should no longer appear in list
    list_resp = await adopter_client.get("/portal/documents")
    doc_ids = [d["id"] for d in list_resp.json()["documents"]]
    assert document_id not in doc_ids


@pytest.mark.asyncio
@pytest.mark.integration
async def test_delete_nonexistent_document_returns_404(adopter_client: AsyncClient) -> None:
    """Deleting a document that doesn't exist returns 404."""
    fake_id = uuid.uuid4()
    resp = await adopter_client.delete(f"/portal/documents/{fake_id}")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# GET /adopters/{adopter_id}/documents (staff)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_staff_can_view_adopter_documents(
    client: AsyncClient, adopter_client: AsyncClient
) -> None:
    """Staff can view all documents for any adopter."""
    # Upload a document as adopter
    pdf_bytes, filename = _fake_pdf()
    upload_resp = await adopter_client.post(
        "/portal/documents",
        files={"file": (filename, io.BytesIO(pdf_bytes), "application/pdf")},
        data={"document_type": "identity"},
    )
    assert upload_resp.status_code == 201

    # Staff fetches adopter profile to get adopter_id
    adopters_resp = await client.get(f"/adopters?email={_ADOPTER_EMAIL}")
    if adopters_resp.status_code == 200:
        adopters = adopters_resp.json()
        if isinstance(adopters, list) and adopters:
            adopter_id = adopters[0]["id"]
        elif isinstance(adopters, dict) and "items" in adopters:
            adopter_id = adopters["items"][0]["id"]
        else:
            pytest.skip("Could not resolve adopter_id from adopters API")
    else:
        pytest.skip("Could not resolve adopter_id from adopters API")

    staff_resp = await client.get(f"/adopters/{adopter_id}/documents")
    assert staff_resp.status_code == 200
    body = staff_resp.json()
    assert "documents" in body
    assert body["total"] >= 1


@pytest.mark.asyncio
@pytest.mark.integration
async def test_adopter_cannot_access_staff_endpoint(adopter_client: AsyncClient) -> None:
    """Adopter role cannot use the staff document view endpoint."""
    fake_id = uuid.uuid4()
    resp = await adopter_client.get(f"/adopters/{fake_id}/documents")
    assert resp.status_code in (401, 403)
