"""Integration tests for volunteer onboarding checklist API (RAP-642).

Tests the new onboarding endpoints against the live test database:
  GET  /api/volunteers/onboarding                        -- get own checklist
  POST /api/staff/volunteers/{id}/onboarding             -- initialize checklist
  PUT  /api/staff/volunteers/{id}/onboarding/{item_key}  -- mark item complete

Requires a running PostgreSQL instance (refugio_dev).
"""

import uuid
from collections.abc import AsyncGenerator
from datetime import timedelta

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from src.auth.utils import create_access_token, hash_password
from src.config import Settings
from src.db.models.volunteer_onboarding import MANDATORY_ITEM_KEYS, ONBOARDING_ITEMS
from src.db.session import init_engine

# Deterministic test volunteer user — separate from the conftest staff user
_TEST_VOLUNTEER_ID = uuid.UUID("00000000-0000-0000-0000-000000000042")
_TEST_VOLUNTEER_EMAIL = "test-volunteer@refugio.test"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def volunteer_client() -> AsyncGenerator[AsyncClient, None]:
    """AsyncClient authenticated as a regular volunteer user.

    Creates a deterministic volunteer user in the DB if absent, then mints a
    JWT for that user. The volunteer profile is NOT pre-created — individual
    tests manage their own profile state.
    """
    from src.app import app

    settings = Settings()
    engine = init_engine(settings)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        await session.execute(
            text("""
                INSERT INTO users (id, email, hashed_password, role, is_active)
                VALUES (:id, :email, :pwd, 'volunteer', true)
                ON CONFLICT (email) DO NOTHING
            """),
            {
                "id": str(_TEST_VOLUNTEER_ID),
                "email": _TEST_VOLUNTEER_EMAIL,
                "pwd": hash_password("TestPass123!"),
            },
        )
        await session.commit()

    from httpx import ASGITransport

    token = create_access_token(
        data={"sub": str(_TEST_VOLUNTEER_ID)},
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
async def approved_volunteer_profile(client: AsyncClient) -> dict:
    """Create an approved volunteer profile via direct DB insert.

    Returns a dict with 'volunteer_id' (volunteer_profiles.id) and
    'user_id' (users.id) for use in tests.

    The profile is created for a unique user per test run to avoid
    conflicts between test runs.
    """
    settings = Settings()
    engine = init_engine(settings)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    user_id = uuid.uuid4()
    profile_id = uuid.uuid4()
    email = f"onboarding-vol-{user_id.hex[:8]}@refugio.test"

    async with session_factory() as session:
        # Create volunteer user
        await session.execute(
            text("""
                INSERT INTO users (id, email, hashed_password, role, is_active)
                VALUES (:id, :email, :pwd, 'volunteer', true)
            """),
            {"id": str(user_id), "email": email, "pwd": hash_password("TestPass123!")},
        )
        # Create approved volunteer profile
        await session.execute(
            text("""
                INSERT INTO volunteer_profiles
                    (id, user_id, motivation, status)
                VALUES (:id, :user_id, :motivation, 'approved')
            """),
            {
                "id": str(profile_id),
                "user_id": str(user_id),
                "motivation": "Quiero ayudar a los animales del refugio de corazón.",
            },
        )
        await session.commit()

    return {"volunteer_id": profile_id, "user_id": user_id}


# ---------------------------------------------------------------------------
# GET /api/volunteers/onboarding — unauthenticated / no profile / not approved
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_onboarding_requires_auth(volunteer_client: AsyncClient) -> None:
    """Unauthenticated request returns 401 or 403."""
    resp = await volunteer_client.get(
        "/api/volunteers/onboarding",
        headers={"Authorization": ""},
    )
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_onboarding_without_volunteer_profile_returns_404(
    volunteer_client: AsyncClient,
) -> None:
    """User with no volunteer profile gets 404."""
    # The volunteer_client user has no profile by default
    resp = await volunteer_client.get("/api/volunteers/onboarding")
    assert resp.status_code == 404


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_onboarding_pending_volunteer_returns_403(
    volunteer_client: AsyncClient,
) -> None:
    """Volunteer with pending status cannot view onboarding checklist."""
    # Apply (creates pending profile)
    apply_resp = await volunteer_client.post(
        "/api/volunteers/apply",
        json={
            "motivation": "Tengo experiencia con animales y quiero colaborar con el refugio.",
            "skills": ["animal_care"],
        },
    )
    # 201 = new profile; 409 = profile already exists from prior run (still pending or approved)
    assert apply_resp.status_code in (201, 409)

    # If the application already exists in approved state, we can't test the 403 path
    if apply_resp.status_code == 409:
        pytest.skip("Volunteer already has a profile — cannot test pending 403 in isolation")

    resp = await volunteer_client.get("/api/volunteers/onboarding")
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# POST /api/staff/volunteers/{id}/onboarding — initialize checklist
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_initialize_onboarding_unknown_volunteer_returns_404(
    client: AsyncClient,
) -> None:
    """Staff gets 404 when initializing checklist for non-existent volunteer."""
    resp = await client.post(f"/api/staff/volunteers/{uuid.uuid4()}/onboarding")
    assert resp.status_code == 404


@pytest.mark.asyncio
@pytest.mark.integration
async def test_initialize_onboarding_creates_all_items(
    client: AsyncClient,
    approved_volunteer_profile: dict,
) -> None:
    """Staff can initialize the onboarding checklist for an approved volunteer."""
    volunteer_id = approved_volunteer_profile["volunteer_id"]

    resp = await client.post(f"/api/staff/volunteers/{volunteer_id}/onboarding")
    assert resp.status_code == 201

    body = resp.json()
    assert body["total"] == len(ONBOARDING_ITEMS)
    assert body["completed_count"] == 0
    assert body["mandatory_complete"] is False

    item_keys = {item["item_key"] for item in body["items"]}
    assert item_keys == set(ONBOARDING_ITEMS.keys())


@pytest.mark.asyncio
@pytest.mark.integration
async def test_initialize_onboarding_mandatory_flags_are_correct(
    client: AsyncClient,
    approved_volunteer_profile: dict,
) -> None:
    """Items in MANDATORY_ITEM_KEYS are flagged is_mandatory=True."""
    volunteer_id = approved_volunteer_profile["volunteer_id"]

    resp = await client.post(f"/api/staff/volunteers/{volunteer_id}/onboarding")
    assert resp.status_code == 201

    for item in resp.json()["items"]:
        if item["item_key"] in MANDATORY_ITEM_KEYS:
            assert item["is_mandatory"] is True, f"{item['item_key']} should be mandatory"
        else:
            assert item["is_mandatory"] is False, f"{item['item_key']} should not be mandatory"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_initialize_onboarding_is_idempotent(
    client: AsyncClient,
    approved_volunteer_profile: dict,
) -> None:
    """Calling initialize twice does not create duplicate items."""
    volunteer_id = approved_volunteer_profile["volunteer_id"]

    first = await client.post(f"/api/staff/volunteers/{volunteer_id}/onboarding")
    assert first.status_code == 201

    second = await client.post(f"/api/staff/volunteers/{volunteer_id}/onboarding")
    assert second.status_code == 201

    assert second.json()["total"] == first.json()["total"]
    assert second.json()["total"] == len(ONBOARDING_ITEMS)


# ---------------------------------------------------------------------------
# PUT /api/staff/volunteers/{id}/onboarding/{item_key} — mark complete
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_update_onboarding_item_unknown_returns_404(
    client: AsyncClient,
    approved_volunteer_profile: dict,
) -> None:
    """Marking an item that doesn't exist returns 404."""
    volunteer_id = approved_volunteer_profile["volunteer_id"]

    resp = await client.put(
        f"/api/staff/volunteers/{volunteer_id}/onboarding/nonexistent_key",
        json={"completed": True},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
@pytest.mark.integration
async def test_mark_onboarding_item_complete(
    client: AsyncClient,
    approved_volunteer_profile: dict,
) -> None:
    """Staff can mark an onboarding item as complete."""
    volunteer_id = approved_volunteer_profile["volunteer_id"]

    # Initialize the checklist first
    init_resp = await client.post(f"/api/staff/volunteers/{volunteer_id}/onboarding")
    assert init_resp.status_code == 201

    # Mark orientation complete
    resp = await client.put(
        f"/api/staff/volunteers/{volunteer_id}/onboarding/orientation",
        json={"completed": True, "notes": "Completado en la sesión de inducción grupal."},
    )
    assert resp.status_code == 200

    body = resp.json()
    assert body["item_key"] == "orientation"
    assert body["completed"] is True
    assert body["completed_at"] is not None
    assert body["notes"] == "Completado en la sesión de inducción grupal."


@pytest.mark.asyncio
@pytest.mark.integration
async def test_mark_onboarding_item_incomplete_clears_timestamp(
    client: AsyncClient,
    approved_volunteer_profile: dict,
) -> None:
    """Reverting an item to incomplete clears the completed_at timestamp."""
    volunteer_id = approved_volunteer_profile["volunteer_id"]

    # Initialize + mark complete first
    await client.post(f"/api/staff/volunteers/{volunteer_id}/onboarding")
    await client.put(
        f"/api/staff/volunteers/{volunteer_id}/onboarding/shelter_rules",
        json={"completed": True},
    )

    # Now revert to incomplete
    resp = await client.put(
        f"/api/staff/volunteers/{volunteer_id}/onboarding/shelter_rules",
        json={"completed": False},
    )
    assert resp.status_code == 200

    body = resp.json()
    assert body["completed"] is False
    assert body["completed_at"] is None


# ---------------------------------------------------------------------------
# Full flow: initialize → mark all mandatory → verify checklist state
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_full_onboarding_flow_mandatory_complete(
    client: AsyncClient,
    approved_volunteer_profile: dict,
) -> None:
    """After marking all mandatory items complete, mandatory_complete becomes True."""
    volunteer_id = approved_volunteer_profile["volunteer_id"]

    # Initialize checklist
    init_resp = await client.post(f"/api/staff/volunteers/{volunteer_id}/onboarding")
    assert init_resp.status_code == 201

    # Mark all mandatory items complete
    for item_key in MANDATORY_ITEM_KEYS:
        resp = await client.put(
            f"/api/staff/volunteers/{volunteer_id}/onboarding/{item_key}",
            json={"completed": True},
        )
        assert resp.status_code == 200

    # Re-initialize returns updated state
    checklist_resp = await client.post(f"/api/staff/volunteers/{volunteer_id}/onboarding")
    assert checklist_resp.status_code == 201
    body = checklist_resp.json()

    # All mandatory should be complete now
    mandatory_items = [it for it in body["items"] if it["is_mandatory"]]
    assert all(it["completed"] for it in mandatory_items)
    assert body["mandatory_complete"] is True
    assert body["completed_count"] == len(MANDATORY_ITEM_KEYS)
