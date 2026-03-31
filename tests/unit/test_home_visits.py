"""Unit tests for home visit scheduling endpoints."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from src.api.home_visits import (
    HomeVisitCompleteRequest,
    HomeVisitCreateRequest,
    HomeVisitUpdateRequest,
    _serialise,
    complete_home_visit,
    create_home_visit,
    list_home_visits_admin,
    list_home_visits_public,
    update_home_visit,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_visit(**overrides):
    """Build a mock HomeVisit."""
    v = MagicMock()
    v.id = overrides.get("id", uuid4())
    v.adoption_request_id = overrides.get("adoption_request_id", uuid4())
    v.scheduled_at = overrides.get("scheduled_at", datetime(2026, 4, 1, 10, 0, tzinfo=UTC))
    v.address = overrides.get("address", "Av. Espana 123, Asuncion")
    v.staff_id = overrides.get("staff_id", uuid4())
    v.status = overrides.get("status", "scheduled")
    v.notes = overrides.get("notes")
    v.photos = overrides.get("photos")
    v.is_deleted = overrides.get("is_deleted", False)
    v.created_at = overrides.get("created_at", datetime(2026, 3, 1, 10, 0, tzinfo=UTC))
    v.updated_at = overrides.get("updated_at", datetime(2026, 3, 1, 10, 0, tzinfo=UTC))
    return v


def _mock_db():
    """Build an async mock database session."""
    db = AsyncMock()
    db.add = MagicMock()
    return db


def _fake_refresh_factory(**defaults):
    """Return an async refresh function that populates server-default fields."""

    async def fake_refresh(obj):
        if not hasattr(obj, "id") or obj.id is None:
            obj.id = defaults.get("id", uuid4())
        if not hasattr(obj, "created_at") or obj.created_at is None:
            obj.created_at = defaults.get("created_at", datetime(2026, 3, 1, 10, 0, tzinfo=UTC))
        if hasattr(obj, "updated_at") and obj.updated_at is None:
            obj.updated_at = defaults.get("updated_at", datetime(2026, 3, 1, 10, 0, tzinfo=UTC))

    return fake_refresh


# ---------------------------------------------------------------------------
# Test _serialise
# ---------------------------------------------------------------------------


class TestSerialise:
    def test_all_fields(self):
        v = _make_visit(notes="Test notes", photos=["p1.jpg", "p2.jpg"])
        result = _serialise(v)
        assert result["status"] == "scheduled"
        assert result["notes"] == "Test notes"
        assert result["photos"] == ["p1.jpg", "p2.jpg"]
        assert "scheduled_at" in result
        assert "created_at" in result

    def test_none_photos_becomes_empty_list(self):
        v = _make_visit(photos=None)
        result = _serialise(v)
        assert result["photos"] == []


# ---------------------------------------------------------------------------
# Test create_home_visit
# ---------------------------------------------------------------------------


class TestCreateHomeVisit:
    @pytest.mark.asyncio
    async def test_creates_visit(self):
        adoption_id = uuid4()
        staff_id = uuid4()
        db = _mock_db()

        # Adoption exists
        adoption = MagicMock()
        staff = MagicMock()

        async def fake_get(model, obj_id):
            from src.db.models.adoption_request import AdoptionRequest
            from src.db.models.user import User

            if model is AdoptionRequest:
                return adoption
            if model is User:
                return staff
            return None

        db.get = AsyncMock(side_effect=fake_get)
        visit_id = uuid4()
        db.refresh = _fake_refresh_factory(id=visit_id)

        future = datetime.now(UTC) + timedelta(days=7)
        payload = HomeVisitCreateRequest(
            scheduled_at=future,
            address="Av. Espana 123, Asuncion",
            staff_id=staff_id,
        )
        result = await create_home_visit(adoption_id, payload, db)
        assert result["status"] == "scheduled"
        assert result["address"] == "Av. Espana 123, Asuncion"
        db.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_404_adoption_not_found(self):
        db = _mock_db()
        db.get = AsyncMock(return_value=None)

        future = datetime.now(UTC) + timedelta(days=7)
        payload = HomeVisitCreateRequest(
            scheduled_at=future,
            address="Av. Espana 123, Asuncion",
        )
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await create_home_visit(uuid4(), payload, db)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_422_past_date(self):
        adoption_id = uuid4()
        db = _mock_db()

        adoption = MagicMock()
        db.get = AsyncMock(return_value=adoption)

        past = datetime(2020, 1, 1, tzinfo=UTC)
        payload = HomeVisitCreateRequest(
            scheduled_at=past,
            address="Av. Espana 123, Asuncion",
        )
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await create_home_visit(adoption_id, payload, db)
        assert exc_info.value.status_code == 422


# ---------------------------------------------------------------------------
# Test list_home_visits_admin
# ---------------------------------------------------------------------------


class TestListHomeVisitsAdmin:
    @pytest.mark.asyncio
    async def test_returns_visits(self):
        db = _mock_db()
        visit = _make_visit()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [visit]
        db.execute = AsyncMock(return_value=mock_result)

        result = await list_home_visits_admin(uuid4(), db)
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_returns_empty(self):
        db = _mock_db()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        db.execute = AsyncMock(return_value=mock_result)

        result = await list_home_visits_admin(uuid4(), db)
        assert result == []


# ---------------------------------------------------------------------------
# Test update_home_visit
# ---------------------------------------------------------------------------


class TestUpdateHomeVisit:
    @pytest.mark.asyncio
    async def test_updates_address(self):
        visit = _make_visit(status="scheduled")
        db = _mock_db()
        db.get = AsyncMock(return_value=visit)
        db.refresh = _fake_refresh_factory()

        payload = HomeVisitUpdateRequest(address="Nueva Direccion 456")
        await update_home_visit(visit.id, payload, db)
        assert visit.address == "Nueva Direccion 456"

    @pytest.mark.asyncio
    async def test_404_not_found(self):
        db = _mock_db()
        db.get = AsyncMock(return_value=None)

        payload = HomeVisitUpdateRequest(address="Test Address 123")
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await update_home_visit(uuid4(), payload, db)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_409_completed_visit(self):
        visit = _make_visit(status="completed")
        db = _mock_db()
        db.get = AsyncMock(return_value=visit)

        payload = HomeVisitUpdateRequest(address="Test Address 123")
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await update_home_visit(visit.id, payload, db)
        assert exc_info.value.status_code == 409


# ---------------------------------------------------------------------------
# Test complete_home_visit
# ---------------------------------------------------------------------------


class TestCompleteHomeVisit:
    @pytest.mark.asyncio
    async def test_completes_visit(self):
        visit = _make_visit(status="scheduled")
        db = _mock_db()
        db.get = AsyncMock(return_value=visit)
        db.refresh = _fake_refresh_factory()

        payload = HomeVisitCompleteRequest(
            notes="Good conditions",
            photos=["photo1.jpg"],
        )
        result = await complete_home_visit(visit.id, payload, db)
        assert result["status"] == "completed"
        assert "photo1.jpg" in result["photos"]

    @pytest.mark.asyncio
    async def test_404_not_found(self):
        db = _mock_db()
        db.get = AsyncMock(return_value=None)

        payload = HomeVisitCompleteRequest()
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await complete_home_visit(uuid4(), payload, db)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_409_already_completed(self):
        visit = _make_visit(status="completed")
        db = _mock_db()
        db.get = AsyncMock(return_value=visit)

        payload = HomeVisitCompleteRequest()
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await complete_home_visit(visit.id, payload, db)
        assert exc_info.value.status_code == 409


# ---------------------------------------------------------------------------
# Test list_home_visits_public
# ---------------------------------------------------------------------------


class TestListHomeVisitsPublic:
    @pytest.mark.asyncio
    async def test_returns_visits(self):
        db = _mock_db()
        visit = _make_visit()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [visit]
        db.execute = AsyncMock(return_value=mock_result)

        result = await list_home_visits_public(uuid4(), db)
        assert len(result) == 1
