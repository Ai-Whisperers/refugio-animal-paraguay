"""Integration tests for public animal browsing endpoints.

These test the /public/animals endpoints which are unauthenticated and
only return animals with status 'available'.
"""

import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.app import app
from src.config import Settings
from src.db.session import init_engine


@pytest_asyncio.fixture
async def public_client() -> AsyncClient:  # type: ignore[misc]
    """Unauthenticated client for public endpoints."""
    settings = Settings()
    engine = init_engine(settings)

    # Seed test animals with different statuses
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        # Clean up any previous test data
        await session.execute(text("DELETE FROM animals WHERE name LIKE 'PubTest%'"))
        await session.commit()

        # Insert test animals
        animals = [
            {
                "id": str(uuid.UUID("a0000000-0000-0000-0000-000000000001")),
                "name": "PubTestLuna",
                "species": "dog",
                "status": "available",
                "gender": "female",
                "size": "medium",
            },
            {
                "id": str(uuid.UUID("a0000000-0000-0000-0000-000000000002")),
                "name": "PubTestMax",
                "species": "cat",
                "status": "available",
                "gender": "male",
                "size": "small",
            },
            {
                "id": str(uuid.UUID("a0000000-0000-0000-0000-000000000003")),
                "name": "PubTestBuddy",
                "species": "dog",
                "status": "intake",
                "gender": "male",
                "size": "large",
            },
            {
                "id": str(uuid.UUID("a0000000-0000-0000-0000-000000000004")),
                "name": "PubTestMittens",
                "species": "cat",
                "status": "adopted",
                "gender": "female",
                "size": "small",
            },
            {
                "id": str(uuid.UUID("a0000000-0000-0000-0000-000000000005")),
                "name": "PubTestRex",
                "species": "dog",
                "status": "available",
                "gender": None,
                "size": None,
            },
        ]
        for a in animals:
            await session.execute(
                text(
                    "INSERT INTO animals (id, name, species, status, gender, size) "
                    "VALUES (:id, :name, :species, :status, :gender, :size) "
                    "ON CONFLICT (id) DO UPDATE SET "
                    "name=EXCLUDED.name, species=EXCLUDED.species, "
                    "status=EXCLUDED.status, gender=EXCLUDED.gender, "
                    "size=EXCLUDED.size"
                ),
                a,
            )
        await session.commit()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    # Cleanup
    async with session_factory() as session:
        await session.execute(text("DELETE FROM animals WHERE name LIKE 'PubTest%'"))
        await session.commit()


# -- List endpoint tests ------------------------------------------------


@pytest.mark.asyncio
async def test_list_public_animals_returns_only_available(
    public_client: AsyncClient,
) -> None:
    """Only animals with status 'available' should appear."""
    resp = await public_client.get("/public/animals")
    assert resp.status_code == 200
    data = resp.json()

    # Should have pagination structure
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "size" in data
    assert "pages" in data

    # All returned animals must be available
    names = [item["name"] for item in data["items"]]
    assert "PubTestLuna" in names
    assert "PubTestMax" in names
    assert "PubTestRex" in names
    # Non-available animals should NOT appear
    assert "PubTestBuddy" not in names  # intake
    assert "PubTestMittens" not in names  # adopted


@pytest.mark.asyncio
async def test_list_public_animals_filter_by_species(
    public_client: AsyncClient,
) -> None:
    resp = await public_client.get("/public/animals?species=cat")
    assert resp.status_code == 200
    data = resp.json()

    for item in data["items"]:
        assert item["species"] == "cat"

    names = [item["name"] for item in data["items"]]
    assert "PubTestMax" in names
    assert "PubTestLuna" not in names


@pytest.mark.asyncio
async def test_list_public_animals_filter_by_gender(
    public_client: AsyncClient,
) -> None:
    resp = await public_client.get("/public/animals?gender=female")
    assert resp.status_code == 200
    data = resp.json()

    for item in data["items"]:
        assert item["gender"] == "female"

    names = [item["name"] for item in data["items"]]
    assert "PubTestLuna" in names


@pytest.mark.asyncio
async def test_list_public_animals_filter_by_size(
    public_client: AsyncClient,
) -> None:
    resp = await public_client.get("/public/animals?size=small")
    assert resp.status_code == 200
    data = resp.json()

    for item in data["items"]:
        assert item["size"] == "small"

    names = [item["name"] for item in data["items"]]
    assert "PubTestMax" in names


@pytest.mark.asyncio
async def test_list_public_animals_search_by_name(
    public_client: AsyncClient,
) -> None:
    """Name search should be case-insensitive partial match."""
    resp = await public_client.get("/public/animals?search=pubtestrex")
    assert resp.status_code == 200
    data = resp.json()

    names = [item["name"] for item in data["items"]]
    assert "PubTestRex" in names


@pytest.mark.asyncio
async def test_list_public_animals_search_partial_match(
    public_client: AsyncClient,
) -> None:
    """Partial name search should work."""
    resp = await public_client.get("/public/animals?search=PubTest")
    assert resp.status_code == 200
    data = resp.json()

    # Should find all available PubTest animals
    assert data["total"] >= 3


@pytest.mark.asyncio
async def test_list_public_animals_combined_filters(
    public_client: AsyncClient,
) -> None:
    """Multiple filters should be combined (AND logic)."""
    resp = await public_client.get("/public/animals?species=dog&gender=female")
    assert resp.status_code == 200
    data = resp.json()

    names = [item["name"] for item in data["items"]]
    assert "PubTestLuna" in names
    assert "PubTestMax" not in names  # cat
    assert "PubTestRex" not in names  # no gender


@pytest.mark.asyncio
async def test_list_public_animals_pagination(
    public_client: AsyncClient,
) -> None:
    """Pagination should work with page and page_size params."""
    resp = await public_client.get("/public/animals?page_size=1&page=1")
    assert resp.status_code == 200
    data = resp.json()

    assert data["size"] == 1
    assert data["page"] == 1
    assert len(data["items"]) <= 1
    assert data["pages"] >= 1


@pytest.mark.asyncio
async def test_list_public_animals_empty_result(
    public_client: AsyncClient,
) -> None:
    """No matches should return empty items, not an error."""
    resp = await public_client.get("/public/animals?search=nonexistentanimal12345")
    assert resp.status_code == 200
    data = resp.json()

    assert data["items"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_list_public_animals_invalid_species_returns_422(
    public_client: AsyncClient,
) -> None:
    resp = await public_client.get("/public/animals?species=dragon")
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_list_public_animals_no_auth_required(
    public_client: AsyncClient,
) -> None:
    """Public endpoints should work without any auth token."""
    # public_client has no auth headers
    resp = await public_client.get("/public/animals")
    assert resp.status_code == 200


# -- Detail endpoint tests -----------------------------------------------


@pytest.mark.asyncio
async def test_get_public_animal_detail(
    public_client: AsyncClient,
) -> None:
    animal_id = "a0000000-0000-0000-0000-000000000001"  # PubTestLuna
    resp = await public_client.get(f"/public/animals/{animal_id}")
    assert resp.status_code == 200
    data = resp.json()

    assert data["name"] == "PubTestLuna"
    assert data["species"] == "dog"
    assert data["gender"] == "female"
    assert data["size"] == "medium"
    assert "photos" in data
    assert isinstance(data["photos"], list)


@pytest.mark.asyncio
async def test_get_public_animal_not_found(
    public_client: AsyncClient,
) -> None:
    fake_id = str(uuid.uuid4())
    resp = await public_client.get(f"/public/animals/{fake_id}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_public_animal_non_available_returns_404(
    public_client: AsyncClient,
) -> None:
    """Animals not in 'available' status should return 404."""
    # PubTestBuddy has status 'intake'
    animal_id = "a0000000-0000-0000-0000-000000000003"
    resp = await public_client.get(f"/public/animals/{animal_id}")
    assert resp.status_code == 404
