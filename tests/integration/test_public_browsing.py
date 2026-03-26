"""Integration tests for public animal browsing endpoints.

Tests:
  GET /public/animals         — paginated listing with filters and search
  GET /public/animals/{id}    — detail for a single available animal

These endpoints require NO authentication.
Only animals with status='available' are returned.
"""

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

# Unauthenticated client — public endpoints need no JWT
_BASE_URL = "http://test"

# Reuse same staff ID as integration/conftest.py
_STAFF_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
_STAFF_EMAIL = "test-staff@refugio.test"


@pytest_asyncio.fixture
async def public_client() -> AsyncGenerator[AsyncClient, None]:
    """Unauthenticated AsyncClient for public endpoints.

    Initializes the DB engine (same as the `client` fixture in conftest).
    """
    settings = Settings()
    init_engine(settings)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url=_BASE_URL,
    ) as ac:
        yield ac


@pytest_asyncio.fixture
async def staff_client() -> AsyncGenerator[AsyncClient, None]:
    """Authenticated AsyncClient for creating test data via staff endpoints."""
    settings = Settings()
    engine = init_engine(settings)

    session_factory = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        await session.execute(
            text(
                "INSERT INTO users (id, email, hashed_password, role, is_active) "
                "VALUES (:id, :email, :pwd, 'staff', true) "
                "ON CONFLICT (id) DO NOTHING"
            ),
            {
                "id": str(_STAFF_ID),
                "email": _STAFF_EMAIL,
                "pwd": hash_password("TestPass123!"),
            },
        )
        await session.commit()

    token = create_access_token(
        data={"sub": str(_STAFF_ID)},
        secret_key=settings.secret_key,
        algorithm=settings.algorithm,
        expires_delta=timedelta(minutes=30),
    )

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url=_BASE_URL,
        headers={"Authorization": f"Bearer {token}"},
    ) as ac:
        yield ac


async def _create_animal(
    staff_client: AsyncClient,
    *,
    name: str = "TestAnimal",
    species: str = "dog",
    status: str = "available",
    breed: str | None = None,
    size: str | None = None,
    gender: str | None = None,
    birth_date: str | None = None,
    description: str | None = None,
) -> dict:
    """Helper to create an animal via the staff API and return the response body."""
    payload: dict = {
        "name": name,
        "species": species,
        "status": status,
    }
    if breed is not None:
        payload["breed"] = breed
    if size is not None:
        payload["size"] = size
    if gender is not None:
        payload["gender"] = gender
    if birth_date is not None:
        payload["birth_date"] = birth_date
    if description is not None:
        payload["description"] = description

    resp = await staff_client.post("/animals", json=payload)
    assert resp.status_code == 201, f"Failed to create animal: {resp.text}"
    return resp.json()


# ── GET /public/animals — Listing ───────────────────────────────────────


@pytest.mark.integration
class TestPublicAnimalListing:
    @pytest.mark.asyncio
    async def test_returns_only_available_animals(
        self, public_client: AsyncClient, staff_client: AsyncClient
    ) -> None:
        """Animals with non-available status are excluded."""
        await _create_animal(staff_client, name="Available Dog", status="available")
        await _create_animal(staff_client, name="Intake Dog", status="intake")
        await _create_animal(staff_client, name="Quarantine Cat", species="cat", status="quarantine")

        resp = await public_client.get("/public/animals")
        assert resp.status_code == 200
        data = resp.json()
        names = [item["name"] for item in data["items"]]
        assert "Available Dog" in names
        assert "Intake Dog" not in names
        assert "Quarantine Cat" not in names

    @pytest.mark.asyncio
    async def test_pagination_metadata(
        self, public_client: AsyncClient, staff_client: AsyncClient
    ) -> None:
        """Response includes correct pagination metadata."""
        # Create enough animals to test pagination
        for i in range(5):
            await _create_animal(
                staff_client, name=f"PaginationDog{i}", status="available"
            )

        resp = await public_client.get("/public/animals?page=1&page_size=2")
        assert resp.status_code == 200
        data = resp.json()

        assert len(data["items"]) <= 2
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["page_size"] == 2
        assert data["pagination"]["total_items"] >= 5
        assert data["pagination"]["total_pages"] >= 3

    @pytest.mark.asyncio
    async def test_default_page_size(self, public_client: AsyncClient) -> None:
        """Default page size is 20."""
        resp = await public_client.get("/public/animals")
        assert resp.status_code == 200
        data = resp.json()
        assert data["pagination"]["page_size"] == 20

    @pytest.mark.asyncio
    async def test_page_size_maximum_enforced(self, public_client: AsyncClient) -> None:
        """Page size above 100 is rejected."""
        resp = await public_client.get("/public/animals?page_size=101")
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_filter_by_species(
        self, public_client: AsyncClient, staff_client: AsyncClient
    ) -> None:
        await _create_animal(staff_client, name="SpeciesDog", species="dog", status="available")
        await _create_animal(staff_client, name="SpeciesCat", species="cat", status="available")

        resp = await public_client.get("/public/animals?species=cat")
        assert resp.status_code == 200
        data = resp.json()
        for item in data["items"]:
            assert item["species"] == "cat"

    @pytest.mark.asyncio
    async def test_filter_by_gender(
        self, public_client: AsyncClient, staff_client: AsyncClient
    ) -> None:
        await _create_animal(
            staff_client, name="MaleDog", gender="male", status="available"
        )
        await _create_animal(
            staff_client, name="FemaleDog", gender="female", status="available"
        )

        resp = await public_client.get("/public/animals?gender=female")
        assert resp.status_code == 200
        data = resp.json()
        for item in data["items"]:
            assert item["gender"] == "female"

    @pytest.mark.asyncio
    async def test_filter_by_size(
        self, public_client: AsyncClient, staff_client: AsyncClient
    ) -> None:
        await _create_animal(
            staff_client, name="SmallCat", species="cat", size="small", status="available"
        )
        await _create_animal(
            staff_client, name="LargeDog", size="large", status="available"
        )

        resp = await public_client.get("/public/animals?size=small")
        assert resp.status_code == 200
        data = resp.json()
        for item in data["items"]:
            assert item["size"] == "small"

    @pytest.mark.asyncio
    async def test_filter_by_breed_case_insensitive(
        self, public_client: AsyncClient, staff_client: AsyncClient
    ) -> None:
        await _create_animal(
            staff_client, name="BreedDog", breed="Labrador", status="available"
        )
        await _create_animal(
            staff_client, name="OtherDog", breed="Poodle", status="available"
        )

        resp = await public_client.get("/public/animals?breed=labrador")
        assert resp.status_code == 200
        data = resp.json()
        for item in data["items"]:
            assert item["breed"].lower() == "labrador"

    @pytest.mark.asyncio
    async def test_search_by_name_partial_case_insensitive(
        self, public_client: AsyncClient, staff_client: AsyncClient
    ) -> None:
        await _create_animal(staff_client, name="Firulais", status="available")
        await _create_animal(staff_client, name="Luna", status="available")

        resp = await public_client.get("/public/animals?search=firu")
        assert resp.status_code == 200
        data = resp.json()
        names = [item["name"] for item in data["items"]]
        assert "Firulais" in names
        assert "Luna" not in names

    @pytest.mark.asyncio
    async def test_combined_filters(
        self, public_client: AsyncClient, staff_client: AsyncClient
    ) -> None:
        """Multiple filters can be combined."""
        await _create_animal(
            staff_client,
            name="ComboMatch",
            species="dog",
            gender="male",
            size="large",
            status="available",
        )
        await _create_animal(
            staff_client,
            name="ComboMismatch",
            species="dog",
            gender="female",
            size="large",
            status="available",
        )

        resp = await public_client.get(
            "/public/animals?species=dog&gender=male&size=large"
        )
        assert resp.status_code == 200
        data = resp.json()
        names = [item["name"] for item in data["items"]]
        assert "ComboMatch" in names
        assert "ComboMismatch" not in names

    @pytest.mark.asyncio
    async def test_empty_search_returns_all(
        self, public_client: AsyncClient
    ) -> None:
        """Empty search string is ignored (returns all available)."""
        resp = await public_client.get("/public/animals?search=")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_no_auth_required(self, public_client: AsyncClient) -> None:
        """Public endpoints work without any Authorization header."""
        resp = await public_client.get("/public/animals")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_invalid_species_filter_returns_422(
        self, public_client: AsyncClient
    ) -> None:
        resp = await public_client.get("/public/animals?species=fish")
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_zero_results_returns_empty_list(
        self, public_client: AsyncClient
    ) -> None:
        resp = await public_client.get("/public/animals?search=nonexistent_xyz_animal_name")
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert data["pagination"]["total_items"] == 0
        assert data["pagination"]["total_pages"] == 0

    @pytest.mark.asyncio
    async def test_response_includes_all_expected_fields(
        self, public_client: AsyncClient, staff_client: AsyncClient
    ) -> None:
        await _create_animal(
            staff_client,
            name="FieldCheckDog",
            species="dog",
            breed="Mixed",
            size="medium",
            gender="male",
            birth_date="2023-01-15",
            description="Test description",
            status="available",
        )

        resp = await public_client.get("/public/animals?search=FieldCheckDog")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) >= 1
        item = next(i for i in data["items"] if i["name"] == "FieldCheckDog")

        expected_fields = {
            "id", "name", "species", "breed", "size", "gender",
            "birth_date", "description", "primary_photo_url", "created_at",
        }
        assert expected_fields.issubset(set(item.keys()))

    @pytest.mark.asyncio
    async def test_json_content_type(self, public_client: AsyncClient) -> None:
        resp = await public_client.get("/public/animals")
        assert resp.status_code == 200
        assert "application/json" in resp.headers["content-type"]


# ── GET /public/animals/{id} — Detail ───────────────────────────────────


@pytest.mark.integration
class TestPublicAnimalDetail:
    @pytest.mark.asyncio
    async def test_returns_available_animal(
        self, public_client: AsyncClient, staff_client: AsyncClient
    ) -> None:
        animal = await _create_animal(
            staff_client,
            name="DetailDog",
            breed="Golden Retriever",
            size="large",
            gender="female",
            status="available",
        )
        animal_id = animal["id"]

        resp = await public_client.get(f"/public/animals/{animal_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == animal_id
        assert data["name"] == "DetailDog"
        assert data["breed"] == "Golden Retriever"
        assert data["size"] == "large"
        assert data["gender"] == "female"
        assert isinstance(data["photos"], list)

    @pytest.mark.asyncio
    async def test_non_available_animal_returns_404(
        self, public_client: AsyncClient, staff_client: AsyncClient
    ) -> None:
        """Animals not in 'available' status return 404 on the public endpoint."""
        animal = await _create_animal(
            staff_client, name="IntakeDog", status="intake"
        )
        animal_id = animal["id"]

        resp = await public_client.get(f"/public/animals/{animal_id}")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_nonexistent_animal_returns_404(
        self, public_client: AsyncClient
    ) -> None:
        fake_id = uuid.uuid4()
        resp = await public_client.get(f"/public/animals/{fake_id}")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_invalid_uuid_returns_422(
        self, public_client: AsyncClient
    ) -> None:
        resp = await public_client.get("/public/animals/not-a-uuid")
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_detail_includes_photos_array(
        self, public_client: AsyncClient, staff_client: AsyncClient
    ) -> None:
        animal = await _create_animal(
            staff_client, name="PhotoDog", status="available"
        )
        animal_id = animal["id"]

        # Add a photo via staff endpoint
        await staff_client.post(
            f"/animals/{animal_id}/photos",
            json={"url": "https://example.com/photo1.jpg", "caption": "Front view"},
        )

        resp = await public_client.get(f"/public/animals/{animal_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["photos"]) >= 1
        assert data["photos"][0]["url"] == "https://example.com/photo1.jpg"

    @pytest.mark.asyncio
    async def test_detail_nullable_fields_are_explicit_null(
        self, public_client: AsyncClient, staff_client: AsyncClient
    ) -> None:
        """Nullable fields appear as null in JSON, not omitted."""
        animal = await _create_animal(
            staff_client, name="NullFieldsDog", status="available"
        )
        animal_id = animal["id"]

        resp = await public_client.get(f"/public/animals/{animal_id}")
        assert resp.status_code == 200
        data = resp.json()
        # These fields should be present (as null), not missing
        assert "breed" in data
        assert "size" in data
        assert "gender" in data
        assert "birth_date" in data
        assert "description" in data

    @pytest.mark.asyncio
    async def test_no_auth_required(
        self, public_client: AsyncClient, staff_client: AsyncClient
    ) -> None:
        animal = await _create_animal(
            staff_client, name="NoAuthDog", status="available"
        )
        resp = await public_client.get(f"/public/animals/{animal['id']}")
        assert resp.status_code == 200
