"""Integration tests for foster family registration and approval API (RAP-190).

Requires a running PostgreSQL instance (refugio_dev) with foster_profiles table created.
"""

import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from src.config import Settings
from src.db.session import init_engine

pytestmark = pytest.mark.integration

# Valid application payload reused across tests
_VALID_APPLICATION = {
    "motivation": "I have a large house and want to help animals find homes temporarily.",
    "home_type": "house_with_yard",
    "has_outdoor_space": True,
    "has_other_pets": False,
    "max_animals": 2,
    "preferred_animal_types": ["dogs", "cats"],
}


@pytest_asyncio.fixture(autouse=True)
async def _cleanup_foster_profiles() -> None:  # type: ignore[return]
    """Delete all foster_profiles after each test to keep tests isolated."""
    yield
    settings = Settings()
    engine = init_engine(settings)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        await session.execute(text("DELETE FROM foster_profiles"))
        await session.commit()
    await engine.dispose()


# ---------------------------------------------------------------------------
# GET /api/foster/home-types
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_home_types(client: AsyncClient) -> None:
    """Home types endpoint returns all valid values."""
    resp = await client.get("/api/foster/home-types")
    assert resp.status_code == 200
    data = resp.json()
    assert "home_types" in data
    expected = {
        "house_with_yard",
        "house_without_yard",
        "apartment",
        "farm",
        "other",
    }
    assert set(data["home_types"]) == expected


# ---------------------------------------------------------------------------
# GET /api/foster/animal-types
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_animal_types(client: AsyncClient) -> None:
    """Animal types endpoint returns all valid preference values."""
    resp = await client.get("/api/foster/animal-types")
    assert resp.status_code == 200
    data = resp.json()
    assert "animal_types" in data
    expected = {"dogs", "cats", "small_animals", "any"}
    assert set(data["animal_types"]) == expected


# ---------------------------------------------------------------------------
# POST /api/foster/apply
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_apply_as_foster_success(client: AsyncClient) -> None:
    """Authenticated user can submit a foster application."""
    resp = await client.post("/api/foster/apply", json=_VALID_APPLICATION)
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "pending"
    assert data["home_type"] == "house_with_yard"
    assert data["has_outdoor_space"] is True
    assert data["max_animals"] == 2
    assert set(data["preferred_animal_types"]) == {"dogs", "cats"}
    assert data["reviewed_at"] is None
    assert data["rejection_reason"] is None
    assert "id" in data
    assert "user_id" in data


@pytest.mark.asyncio
@pytest.mark.integration
async def test_apply_as_foster_minimal_fields(client: AsyncClient) -> None:
    """Foster application works with only required fields."""
    resp = await client.post(
        "/api/foster/apply",
        json={"motivation": "I want to help stray animals find permanent homes."},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "pending"
    assert data["home_type"] == "apartment"
    assert data["has_outdoor_space"] is False
    assert data["has_other_pets"] is False
    assert data["max_animals"] == 1
    assert data["preferred_animal_types"] == []


@pytest.mark.asyncio
@pytest.mark.integration
async def test_apply_twice_returns_409(client: AsyncClient) -> None:
    """Submitting a second application from the same user returns 409."""
    first = await client.post("/api/foster/apply", json=_VALID_APPLICATION)
    assert first.status_code == 201

    second = await client.post("/api/foster/apply", json=_VALID_APPLICATION)
    assert second.status_code == 409
    body = second.json()
    # Custom error middleware returns "message" rather than "detail"
    error_text = body.get("message") or body.get("detail", "")
    assert "already exists" in error_text


@pytest.mark.asyncio
@pytest.mark.integration
async def test_apply_short_motivation_returns_422(client: AsyncClient) -> None:
    """Motivation shorter than 20 characters returns 422."""
    resp = await client.post(
        "/api/foster/apply",
        json={"motivation": "Too short"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
@pytest.mark.integration
async def test_apply_invalid_home_type_returns_422(client: AsyncClient) -> None:
    """Invalid home_type value returns 422."""
    resp = await client.post(
        "/api/foster/apply",
        json={
            "motivation": "I want to help stray animals find permanent homes.",
            "home_type": "tent",
        },
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /api/foster/me
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_my_foster_profile(client: AsyncClient) -> None:
    """User can retrieve their own foster profile after applying."""
    await client.post("/api/foster/apply", json=_VALID_APPLICATION)

    resp = await client.get("/api/foster/me")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "pending"
    assert data["home_type"] == "house_with_yard"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_my_foster_profile_not_found(client: AsyncClient) -> None:
    """Returns 404 if the user has no foster application."""
    resp = await client.get("/api/foster/me")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# GET /api/staff/foster
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_foster_applications_empty(client: AsyncClient) -> None:
    """Staff can list foster applications (empty result)."""
    resp = await client.get("/api/staff/foster")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["items"] == []
    assert data["page"] == 1


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_foster_applications_with_data(client: AsyncClient) -> None:
    """Staff can list foster applications after a submission."""
    await client.post("/api/foster/apply", json=_VALID_APPLICATION)

    resp = await client.get("/api/staff/foster")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["status"] == "pending"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_foster_applications_filter_by_status(client: AsyncClient) -> None:
    """Staff can filter applications by status."""
    await client.post("/api/foster/apply", json=_VALID_APPLICATION)

    # Filter for pending — should return 1
    pending_resp = await client.get("/api/staff/foster?foster_status=pending")
    assert pending_resp.status_code == 200
    assert pending_resp.json()["total"] == 1

    # Filter for approved — should return 0
    approved_resp = await client.get("/api/staff/foster?foster_status=approved")
    assert approved_resp.status_code == 200
    assert approved_resp.json()["total"] == 0


# ---------------------------------------------------------------------------
# GET /api/staff/foster/{id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_foster_application_by_id(client: AsyncClient) -> None:
    """Staff can retrieve a single foster application by ID."""
    create_resp = await client.post("/api/foster/apply", json=_VALID_APPLICATION)
    profile_id = create_resp.json()["id"]

    resp = await client.get(f"/api/staff/foster/{profile_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == profile_id


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_foster_application_not_found(client: AsyncClient) -> None:
    """Getting a non-existent foster profile returns 404."""
    resp = await client.get(f"/api/staff/foster/{uuid.uuid4()}")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# PUT /api/staff/foster/{id}/review
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_approve_foster_application(client: AsyncClient) -> None:
    """Staff can approve a pending foster application."""
    create_resp = await client.post("/api/foster/apply", json=_VALID_APPLICATION)
    profile_id = create_resp.json()["id"]

    review_resp = await client.put(
        f"/api/staff/foster/{profile_id}/review",
        json={"approved": True},
    )
    assert review_resp.status_code == 200
    data = review_resp.json()
    assert data["status"] == "approved"
    assert data["rejection_reason"] is None
    assert data["reviewed_at"] is not None
    assert data["reviewed_by"] is not None


@pytest.mark.asyncio
@pytest.mark.integration
async def test_reject_foster_application(client: AsyncClient) -> None:
    """Staff can reject a pending foster application with a reason."""
    create_resp = await client.post("/api/foster/apply", json=_VALID_APPLICATION)
    profile_id = create_resp.json()["id"]

    review_resp = await client.put(
        f"/api/staff/foster/{profile_id}/review",
        json={"approved": False, "rejection_reason": "No outdoor space for large dogs."},
    )
    assert review_resp.status_code == 200
    data = review_resp.json()
    assert data["status"] == "rejected"
    assert data["rejection_reason"] == "No outdoor space for large dogs."
    assert data["reviewed_at"] is not None


@pytest.mark.asyncio
@pytest.mark.integration
async def test_reject_without_reason_returns_400(client: AsyncClient) -> None:
    """Rejecting without a reason returns 400."""
    create_resp = await client.post("/api/foster/apply", json=_VALID_APPLICATION)
    profile_id = create_resp.json()["id"]

    review_resp = await client.put(
        f"/api/staff/foster/{profile_id}/review",
        json={"approved": False},
    )
    assert review_resp.status_code == 400
    body = review_resp.json()
    error_text = body.get("message") or body.get("detail", "")
    assert "rejection reason" in error_text.lower()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_review_already_reviewed_returns_422(client: AsyncClient) -> None:
    """Reviewing an already-approved application returns 422."""
    create_resp = await client.post("/api/foster/apply", json=_VALID_APPLICATION)
    profile_id = create_resp.json()["id"]

    # First review — approve
    await client.put(
        f"/api/staff/foster/{profile_id}/review",
        json={"approved": True},
    )

    # Second review attempt — should fail
    second_resp = await client.put(
        f"/api/staff/foster/{profile_id}/review",
        json={"approved": False, "rejection_reason": "Changed decision."},
    )
    assert second_resp.status_code == 422
    body = second_resp.json()
    error_text = body.get("message") or body.get("detail", "")
    assert "pending" in error_text


@pytest.mark.asyncio
@pytest.mark.integration
async def test_review_nonexistent_application_returns_404(client: AsyncClient) -> None:
    """Reviewing a non-existent foster application returns 404."""
    resp = await client.put(
        f"/api/staff/foster/{uuid.uuid4()}/review",
        json={"approved": True},
    )
    assert resp.status_code == 404
