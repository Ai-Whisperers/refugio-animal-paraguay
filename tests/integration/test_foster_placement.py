"""Integration tests for foster placement matching endpoints (RAP-191).

Tests the GET /api/staff/foster/match/{animal_id} and
GET /api/staff/foster/{profile_id}/matches endpoints against a live database.

Requires a running PostgreSQL instance (refugio_dev) with the
foster_profiles and foster_placements tables.
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

_VALID_APPLICATION = {
    "motivation": "I have a spacious home and want to help animals find families.",
    "home_type": "house_with_yard",
    "has_outdoor_space": True,
    "has_other_pets": False,
    "max_animals": 2,
    "preferred_animal_types": ["dogs"],
    "experience_description": "Fostered 3 dogs previously.",
}


@pytest_asyncio.fixture(autouse=True)
async def _cleanup() -> None:  # type: ignore[return]
    """Remove test data after each test to keep tests isolated."""
    yield
    settings = Settings()
    engine = init_engine(settings)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        await session.execute(text("DELETE FROM foster_placements"))
        await session.execute(
            text(
                "DELETE FROM foster_profiles WHERE user_id != '00000000-0000-0000-0000-000000000001'"
            )
        )
        await session.execute(text("DELETE FROM animals WHERE name LIKE 'TestMatchAnimal%'"))
        await session.commit()
    await engine.dispose()


# ---------------------------------------------------------------------------
# Helper: create a test animal via SQL
# ---------------------------------------------------------------------------


async def _create_test_animal(
    species: str = "dog",
    size: str = "medium",
    status: str = "available",
    name_suffix: str = "",
) -> uuid.UUID:
    """Insert a minimal animal row and return its id."""
    settings = Settings()
    engine = init_engine(settings)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    animal_id = uuid.uuid4()
    async with session_factory() as session:
        await session.execute(
            text("""
                INSERT INTO animals (id, name, species, status, size)
                VALUES (:id, :name, :species, :status, :size)
                """),
            {
                "id": str(animal_id),
                "name": f"TestMatchAnimal{name_suffix}",
                "species": species,
                "status": status,
                "size": size,
            },
        )
        await session.commit()
    await engine.dispose()
    return animal_id


# ---------------------------------------------------------------------------
# GET /api/staff/foster/match/{animal_id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_match_foster_for_animal_no_approved_families(client: AsyncClient) -> None:
    """Returns empty list when no approved foster families exist."""
    animal_id = await _create_test_animal()
    resp = await client.get(f"/api/staff/foster/match/{animal_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert "matches" in data
    assert data["total_eligible"] == 0
    assert data["matches"] == []


@pytest.mark.asyncio
async def test_match_foster_for_animal_with_approved_family(client: AsyncClient) -> None:
    """Returns matched foster families for an available animal."""
    # Create and approve a foster family
    resp = await client.post("/api/foster/apply", json=_VALID_APPLICATION)
    assert resp.status_code == 201
    profile_id = resp.json()["id"]

    # Approve via staff endpoint
    resp = await client.put(
        f"/api/staff/foster/{profile_id}/review",
        json={"approved": True},
    )
    assert resp.status_code == 200

    animal_id = await _create_test_animal(species="dog", size="medium")
    resp = await client.get(f"/api/staff/foster/match/{animal_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_eligible"] >= 1
    assert len(data["matches"]) >= 1

    match = data["matches"][0]
    assert "foster_profile_id" in match
    assert "match_score" in match
    assert 0 < match["match_score"] <= 100
    assert "why_match" in match
    assert "why_not" in match
    assert "remaining_capacity" in match


@pytest.mark.asyncio
async def test_match_foster_for_nonexistent_animal(client: AsyncClient) -> None:
    """Returns empty result for an unknown animal_id."""
    fake_id = uuid.uuid4()
    resp = await client.get(f"/api/staff/foster/match/{fake_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["matches"] == []
    assert data["total_eligible"] == 0


@pytest.mark.asyncio
async def test_match_foster_for_animal_requires_staff(client: AsyncClient) -> None:
    """Unauthenticated requests are rejected."""
    animal_id = await _create_test_animal()
    from httpx import ASGITransport
    from httpx import AsyncClient as RawClient
    from src.app import app

    async with RawClient(transport=ASGITransport(app=app), base_url="http://test") as anon:
        resp = await anon.get(f"/api/staff/foster/match/{animal_id}")
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_match_foster_pagination_limit(client: AsyncClient) -> None:
    """Pagination limit parameter is respected."""
    animal_id = await _create_test_animal()
    resp = await client.get(f"/api/staff/foster/match/{animal_id}?limit=1&offset=0")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["matches"]) <= 1


# ---------------------------------------------------------------------------
# GET /api/staff/foster/{profile_id}/matches
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_animal_matches_for_unapproved_family(client: AsyncClient) -> None:
    """Returns empty list for a pending (not yet approved) foster family."""
    resp = await client.post("/api/foster/apply", json=_VALID_APPLICATION)
    assert resp.status_code == 201
    profile_id = resp.json()["id"]
    # Do NOT approve — still pending

    await _create_test_animal()

    resp = await client.get(f"/api/staff/foster/{profile_id}/matches")
    assert resp.status_code == 200
    data = resp.json()
    assert data["matches"] == []
    assert data["total_eligible"] == 0


@pytest.mark.asyncio
async def test_animal_matches_for_approved_family_with_animals(client: AsyncClient) -> None:
    """Returns ranked animals for an approved foster family."""
    # Apply and approve
    resp = await client.post("/api/foster/apply", json=_VALID_APPLICATION)
    assert resp.status_code == 201
    profile_id = resp.json()["id"]

    resp = await client.put(
        f"/api/staff/foster/{profile_id}/review",
        json={"approved": True},
    )
    assert resp.status_code == 200

    # Create fosterable animals
    await _create_test_animal(species="dog", size="medium", name_suffix="A")
    await _create_test_animal(species="cat", size="small", name_suffix="B")

    resp = await client.get(f"/api/staff/foster/{profile_id}/matches")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_eligible"] >= 1
    assert len(data["matches"]) >= 1

    animal_match = data["matches"][0]
    assert "animal_id" in animal_match
    assert "name" in animal_match
    assert "species" in animal_match
    assert "match_score" in animal_match
    assert 0 < animal_match["match_score"] <= 100


@pytest.mark.asyncio
async def test_animal_matches_for_nonexistent_profile(client: AsyncClient) -> None:
    """Returns empty result for an unknown profile_id."""
    fake_id = uuid.uuid4()
    resp = await client.get(f"/api/staff/foster/{fake_id}/matches")
    assert resp.status_code == 200
    data = resp.json()
    assert data["matches"] == []
    assert data["total_eligible"] == 0


@pytest.mark.asyncio
async def test_animal_matches_requires_staff(client: AsyncClient) -> None:
    """Unauthenticated requests are rejected."""
    fake_id = uuid.uuid4()
    from httpx import ASGITransport
    from httpx import AsyncClient as RawClient
    from src.app import app

    async with RawClient(transport=ASGITransport(app=app), base_url="http://test") as anon:
        resp = await anon.get(f"/api/staff/foster/{fake_id}/matches")
    assert resp.status_code in (401, 403)
