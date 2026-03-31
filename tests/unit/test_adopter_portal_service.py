"""Unit tests for adopter-portal service functions (get_adopter_applications)."""

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from src.db.models.user import User
from src.services.dashboard_service import ApplicationDetail, get_adopter_applications


@pytest.fixture()
def mock_db():
    """Create a mock async database session."""
    db = AsyncMock()
    db.execute = AsyncMock()
    return db


@pytest.fixture()
def adopter_user():
    """Create a mock adopter user."""
    user = MagicMock(spec=User)
    user.id = uuid.uuid4()
    user.email = "adopter-portal@refugio-shelter.org"
    user.full_name = "Ana Lopez"
    user.role = "adopter"
    return user


def _mock_execute(mock_db, rows: list) -> None:
    """Configure mock_db.execute to return the given rows."""
    mock_result = MagicMock()
    mock_result.all.return_value = rows
    mock_db.execute.return_value = mock_result


class TestGetAdopterApplications:
    """Tests for get_adopter_applications service function."""

    @pytest.mark.asyncio()
    async def test_returns_empty_list_when_no_applications(self, mock_db, adopter_user) -> None:
        """Should return empty list when user has no adoption applications."""
        _mock_execute(mock_db, [])

        result = await get_adopter_applications(mock_db, adopter_user)

        assert result == []
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio()
    async def test_returns_application_details_for_user(self, mock_db, adopter_user) -> None:
        """Should map query rows to ApplicationDetail objects."""
        app_id = uuid.uuid4()
        animal_id = uuid.uuid4()
        submitted = datetime.now(UTC)

        row = MagicMock()
        row.id = app_id
        row.animal_id = animal_id
        row.name = "Firulais"
        row.species = "dog"
        row.submitted_at = submitted
        row.decided_at = None
        row.status = "pending"
        row.notes = None

        _mock_execute(mock_db, [row])

        result = await get_adopter_applications(mock_db, adopter_user)

        assert len(result) == 1
        app = result[0]
        assert app.id == app_id
        assert app.animal_id == animal_id
        assert app.animal_name == "Firulais"
        assert app.animal_species == "dog"
        assert app.status == "pending"
        assert app.decided_at is None
        assert app.notes is None

    @pytest.mark.asyncio()
    async def test_returns_multiple_applications(self, mock_db, adopter_user) -> None:
        """Should return all applications for the user."""
        rows = []
        for i in range(3):
            row = MagicMock()
            row.id = uuid.uuid4()
            row.animal_id = uuid.uuid4()
            row.name = f"Animal{i}"
            row.species = "cat"
            row.submitted_at = datetime.now(UTC)
            row.decided_at = None
            row.status = "pending"
            row.notes = None
            rows.append(row)

        _mock_execute(mock_db, rows)

        result = await get_adopter_applications(mock_db, adopter_user)

        assert len(result) == 3
        assert result[0].animal_name == "Animal0"
        assert result[2].animal_name == "Animal2"

    @pytest.mark.asyncio()
    async def test_includes_decision_info_when_approved(self, mock_db, adopter_user) -> None:
        """Should include decided_at and notes when application has a decision."""
        decided_at = datetime.now(UTC)

        row = MagicMock()
        row.id = uuid.uuid4()
        row.animal_id = uuid.uuid4()
        row.name = "Luna"
        row.species = "cat"
        row.submitted_at = datetime.now(UTC)
        row.decided_at = decided_at
        row.status = "approved"
        row.notes = "Excelente candidato para adopcion"

        _mock_execute(mock_db, [row])

        result = await get_adopter_applications(mock_db, adopter_user)

        assert len(result) == 1
        app = result[0]
        assert app.status == "approved"
        assert app.decided_at == decided_at
        assert app.notes == "Excelente candidato para adopcion"

    @pytest.mark.asyncio()
    async def test_includes_notes_when_rejected(self, mock_db, adopter_user) -> None:
        """Should include decision notes for rejected applications."""
        row = MagicMock()
        row.id = uuid.uuid4()
        row.animal_id = uuid.uuid4()
        row.name = "Rex"
        row.species = "dog"
        row.submitted_at = datetime.now(UTC)
        row.decided_at = datetime.now(UTC)
        row.status = "rejected"
        row.notes = "No cuenta con espacio adecuado"

        _mock_execute(mock_db, [row])

        result = await get_adopter_applications(mock_db, adopter_user)

        assert result[0].status == "rejected"
        assert result[0].notes == "No cuenta con espacio adecuado"


class TestApplicationDetail:
    """Tests for ApplicationDetail data structure."""

    def test_stores_all_fields(self) -> None:
        """Should store all fields correctly."""
        app_id = uuid.uuid4()
        animal_id = uuid.uuid4()
        submitted = datetime.now(UTC)
        decided = datetime.now(UTC)

        detail = ApplicationDetail(
            id=app_id,
            animal_id=animal_id,
            animal_name="Milo",
            animal_species="cat",
            submitted_at=submitted,
            decided_at=decided,
            status="approved",
            notes="Recomendado",
        )

        assert detail.id == app_id
        assert detail.animal_id == animal_id
        assert detail.animal_name == "Milo"
        assert detail.animal_species == "cat"
        assert detail.submitted_at == submitted
        assert detail.decided_at == decided
        assert detail.status == "approved"
        assert detail.notes == "Recomendado"

    def test_stores_none_fields(self) -> None:
        """Should store None for optional fields."""
        detail = ApplicationDetail(
            id=uuid.uuid4(),
            animal_id=uuid.uuid4(),
            animal_name="Pepe",
            animal_species="dog",
            submitted_at=datetime.now(UTC),
            decided_at=None,
            status="pending",
            notes=None,
        )

        assert detail.decided_at is None
        assert detail.notes is None
