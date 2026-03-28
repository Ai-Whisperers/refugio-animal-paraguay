"""Unit tests for emergency update endpoints.

Tests:
  POST /api/emergencies/{id}/updates    -- create update (staff)
  GET  /api/emergencies/{id}/updates     -- list updates (staff)
  GET  /api/public/emergencies/{id}/updates -- public timeline
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from src.api.emergency_updates import public_router, staff_router
from src.db.models.user import User

# ---------------------------------------------------------------------------
# App fixture -- mount both routers without real auth
# ---------------------------------------------------------------------------

_app = FastAPI()


def _fake_staff_user() -> User:
    """Return a mock staff user."""
    user = MagicMock(spec=User)
    user.id = uuid4()
    user.role = "staff"
    return user


# Override require_staff for all staff endpoints
_app.include_router(staff_router)
_app.include_router(public_router)


def _make_emergency(emergency_id=None, status="active"):
    """Create a mock EmergencyCase row."""
    case = MagicMock()
    case.id = emergency_id or uuid4()
    case.status = status
    case.is_deleted = False
    return case


def _make_update(emergency_id, text="Update text", is_resolution=False, outcome=None):
    """Create a mock EmergencyUpdate row."""
    update = MagicMock()
    update.id = uuid4()
    update.emergency_id = emergency_id
    update.text = text
    update.photos = []
    update.posted_by = uuid4()
    update.is_resolution = is_resolution
    update.outcome = outcome
    update.created_at = datetime(2026, 3, 28, 12, 0, 0, tzinfo=UTC)
    return update


# ---------------------------------------------------------------------------
# POST tests
# ---------------------------------------------------------------------------


class TestCreateEmergencyUpdate:
    """Tests for POST /api/emergencies/{id}/updates."""

    @pytest.mark.asyncio
    async def test_creates_update_successfully(self) -> None:
        """Creating an update with valid data returns 201."""
        emergency_id = uuid4()
        case = _make_emergency(emergency_id)

        mock_db = AsyncMock()
        # _verify_emergency_exists query
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = case
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()

        # After refresh, return the update with created_at
        async def fake_refresh(obj):
            obj.id = uuid4()
            obj.created_at = datetime(2026, 3, 28, 12, 0, 0, tzinfo=UTC)

        mock_db.refresh = AsyncMock(side_effect=fake_refresh)

        user = _fake_staff_user()

        from src.auth.dependencies import require_staff
        from src.db.session import get_async_session

        _app.dependency_overrides[require_staff] = lambda: user
        _app.dependency_overrides[get_async_session] = lambda: mock_db

        try:
            async with AsyncClient(
                transport=ASGITransport(app=_app),
                base_url="http://test",
            ) as client:
                response = await client.post(
                    f"/api/emergencies/{emergency_id}/updates",
                    json={"text": "Animal is recovering well", "photos": ["photo1.jpg"]},
                )
        finally:
            _app.dependency_overrides.clear()

        assert response.status_code == 201
        data = response.json()
        assert data["text"] == "Animal is recovering well"
        assert data["is_resolution"] is False

    @pytest.mark.asyncio
    async def test_resolution_requires_outcome(self) -> None:
        """Resolution update without outcome returns 400."""
        emergency_id = uuid4()
        case = _make_emergency(emergency_id)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = case

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=mock_result)

        user = _fake_staff_user()

        from src.auth.dependencies import require_staff
        from src.db.session import get_async_session

        _app.dependency_overrides[require_staff] = lambda: user
        _app.dependency_overrides[get_async_session] = lambda: mock_db

        try:
            async with AsyncClient(
                transport=ASGITransport(app=_app),
                base_url="http://test",
            ) as client:
                response = await client.post(
                    f"/api/emergencies/{emergency_id}/updates",
                    json={"text": "Case resolved", "is_resolution": True},
                )
        finally:
            _app.dependency_overrides.clear()

        assert response.status_code == 400
        assert "outcome is required" in response.json()["detail"]["error"]

    @pytest.mark.asyncio
    async def test_resolution_with_invalid_outcome(self) -> None:
        """Resolution with invalid outcome returns 400."""
        emergency_id = uuid4()
        case = _make_emergency(emergency_id)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = case

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=mock_result)

        user = _fake_staff_user()

        from src.auth.dependencies import require_staff
        from src.db.session import get_async_session

        _app.dependency_overrides[require_staff] = lambda: user
        _app.dependency_overrides[get_async_session] = lambda: mock_db

        try:
            async with AsyncClient(
                transport=ASGITransport(app=_app),
                base_url="http://test",
            ) as client:
                response = await client.post(
                    f"/api/emergencies/{emergency_id}/updates",
                    json={
                        "text": "Case resolved",
                        "is_resolution": True,
                        "outcome": "invalid_outcome",
                    },
                )
        finally:
            _app.dependency_overrides.clear()

        assert response.status_code == 400
        assert "Invalid outcome" in response.json()["detail"]["error"]

    @pytest.mark.asyncio
    async def test_nonexistent_emergency_returns_404(self) -> None:
        """Posting to a nonexistent emergency returns 404."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=mock_result)

        user = _fake_staff_user()

        from src.auth.dependencies import require_staff
        from src.db.session import get_async_session

        _app.dependency_overrides[require_staff] = lambda: user
        _app.dependency_overrides[get_async_session] = lambda: mock_db

        try:
            async with AsyncClient(
                transport=ASGITransport(app=_app),
                base_url="http://test",
            ) as client:
                response = await client.post(
                    f"/api/emergencies/{uuid4()}/updates",
                    json={"text": "Update text"},
                )
        finally:
            _app.dependency_overrides.clear()

        assert response.status_code == 404


# ---------------------------------------------------------------------------
# GET tests (staff)
# ---------------------------------------------------------------------------


class TestListEmergencyUpdates:
    """Tests for GET /api/emergencies/{id}/updates."""

    @pytest.mark.asyncio
    async def test_returns_updates_list(self) -> None:
        """Listing updates returns paginated results."""
        emergency_id = uuid4()
        case = _make_emergency(emergency_id)
        update1 = _make_update(emergency_id, text="First update")
        update2 = _make_update(emergency_id, text="Second update")

        call_count = 0

        async def mock_execute(stmt):
            nonlocal call_count
            call_count += 1
            result = MagicMock()
            if call_count == 1:
                # _verify_emergency_exists
                result.scalar_one_or_none.return_value = case
            elif call_count == 2:
                # count query
                result.scalar_one.return_value = 2
            else:
                # list query
                result.scalars.return_value.all.return_value = [update2, update1]
            return result

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(side_effect=mock_execute)

        user = _fake_staff_user()

        from src.auth.dependencies import require_staff
        from src.db.session import get_async_session

        _app.dependency_overrides[require_staff] = lambda: user
        _app.dependency_overrides[get_async_session] = lambda: mock_db

        try:
            async with AsyncClient(
                transport=ASGITransport(app=_app),
                base_url="http://test",
            ) as client:
                response = await client.get(f"/api/emergencies/{emergency_id}/updates")
        finally:
            _app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2


# ---------------------------------------------------------------------------
# Public GET tests
# ---------------------------------------------------------------------------


class TestPublicEmergencyUpdates:
    """Tests for GET /api/public/emergencies/{id}/updates."""

    @pytest.mark.asyncio
    async def test_returns_public_timeline(self) -> None:
        """Public endpoint returns updates without auth."""
        emergency_id = uuid4()
        case = _make_emergency(emergency_id)

        call_count = 0

        async def mock_execute(stmt):
            nonlocal call_count
            call_count += 1
            result = MagicMock()
            if call_count == 1:
                result.scalar_one_or_none.return_value = case
            elif call_count == 2:
                result.scalar_one.return_value = 0
            else:
                result.scalars.return_value.all.return_value = []
            return result

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(side_effect=mock_execute)

        from src.db.session import get_async_session

        _app.dependency_overrides[get_async_session] = lambda: mock_db

        try:
            async with AsyncClient(
                transport=ASGITransport(app=_app),
                base_url="http://test",
            ) as client:
                response = await client.get(f"/api/public/emergencies/{emergency_id}/updates")
        finally:
            _app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []

    @pytest.mark.asyncio
    async def test_public_nonexistent_returns_404(self) -> None:
        """Public endpoint returns 404 for nonexistent emergency."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=mock_result)

        from src.db.session import get_async_session

        _app.dependency_overrides[get_async_session] = lambda: mock_db

        try:
            async with AsyncClient(
                transport=ASGITransport(app=_app),
                base_url="http://test",
            ) as client:
                response = await client.get(f"/api/public/emergencies/{uuid4()}/updates")
        finally:
            _app.dependency_overrides.clear()

        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------


class TestEmergencyUpdateModel:
    """Tests for the EmergencyUpdate ORM model definition."""

    def test_model_table_name(self) -> None:
        """Table name is emergency_updates."""
        from src.db.models.emergency_update import EmergencyUpdate

        assert EmergencyUpdate.__tablename__ == "emergency_updates"

    def test_outcome_enum_values(self) -> None:
        """EmergencyOutcome enum has expected values."""
        from src.db.models.emergency_update import EmergencyOutcome

        assert set(EmergencyOutcome) == {
            EmergencyOutcome.RECOVERED,
            EmergencyOutcome.ADOPTED,
            EmergencyOutcome.IN_CARE,
            EmergencyOutcome.DECEASED,
            EmergencyOutcome.OTHER,
        }
