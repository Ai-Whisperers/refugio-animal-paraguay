"""Unit tests for rescuer emergency creation endpoint.

Tests:
  POST /api/portal/emergencies — create emergency (verified rescuer)
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from src.api.rescuer_emergencies import router
from src.db.models.user import User

# ---------------------------------------------------------------------------
# App fixture
# ---------------------------------------------------------------------------

_app = FastAPI()
_app.include_router(router)


def _fake_user(role: str = "staff") -> User:
    """Return a mock user."""
    user = MagicMock(spec=User)
    user.id = uuid4()
    user.role = role
    return user


def _future_deadline(hours: int = 72) -> str:
    """Return an ISO datetime string in the future."""
    return (datetime.now(UTC) + timedelta(hours=hours)).isoformat()


def _valid_body(deadline: str | None = None) -> dict:
    """Return a valid request body."""
    return {
        "title": "Dog hit by car needs surgery",
        "description": "Found injured dog on Route 3, needs immediate surgery",
        "amount_needed_cents": 50000,
        "currency": "USD",
        "deadline": deadline or _future_deadline(),
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestCreateRescuerEmergency:
    """Tests for POST /api/portal/emergencies."""

    @pytest.mark.asyncio
    async def test_creates_emergency_successfully(self) -> None:
        """Valid request returns 201 with emergency data."""
        user = _fake_user()

        mock_case = MagicMock()
        mock_case.id = uuid4()
        mock_case.title = "Dog hit by car needs surgery"
        mock_case.description = "Found injured dog on Route 3"
        mock_case.animal_id = None
        mock_case.rescuer_id = user.id
        mock_case.campaign_id = None
        mock_case.photos = []
        mock_case.amount_needed_cents = 50000
        mock_case.amount_raised_cents = 0
        mock_case.currency = "USD"
        mock_case.deadline = datetime.now(UTC) + timedelta(hours=72)
        mock_case.status = "active"
        mock_case.urgency = "high"
        mock_case.created_at = datetime.now(UTC)

        mock_db = AsyncMock()
        mock_db.commit = AsyncMock()

        from src.auth.dependencies import require_verified_rescuer
        from src.db.session import get_async_session

        _app.dependency_overrides[require_verified_rescuer] = lambda: user
        _app.dependency_overrides[get_async_session] = lambda: mock_db

        try:
            with patch(
                "src.api.rescuer_emergencies.create_emergency_case",
                new_callable=AsyncMock,
                return_value=mock_case,
            ):
                async with AsyncClient(
                    transport=ASGITransport(app=_app),
                    base_url="http://test",
                ) as client:
                    response = await client.post(
                        "/api/portal/emergencies",
                        json=_valid_body(),
                    )
        finally:
            _app.dependency_overrides.clear()

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Dog hit by car needs surgery"
        assert data["status"] == "active"
        assert data["urgency"] == "high"

    @pytest.mark.asyncio
    async def test_rejects_missing_title(self) -> None:
        """Missing title returns 422."""
        user = _fake_user()

        from src.auth.dependencies import require_verified_rescuer
        from src.db.session import get_async_session

        _app.dependency_overrides[require_verified_rescuer] = lambda: user
        _app.dependency_overrides[get_async_session] = lambda: AsyncMock()

        try:
            async with AsyncClient(
                transport=ASGITransport(app=_app),
                base_url="http://test",
            ) as client:
                body = _valid_body()
                del body["title"]
                response = await client.post("/api/portal/emergencies", json=body)
        finally:
            _app.dependency_overrides.clear()

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_rejects_invalid_currency(self) -> None:
        """Invalid currency returns 422."""
        user = _fake_user()

        from src.auth.dependencies import require_verified_rescuer
        from src.db.session import get_async_session

        _app.dependency_overrides[require_verified_rescuer] = lambda: user
        _app.dependency_overrides[get_async_session] = lambda: AsyncMock()

        try:
            async with AsyncClient(
                transport=ASGITransport(app=_app),
                base_url="http://test",
            ) as client:
                body = _valid_body()
                body["currency"] = "EUR"
                response = await client.post("/api/portal/emergencies", json=body)
        finally:
            _app.dependency_overrides.clear()

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_rejects_deadline_too_soon(self) -> None:
        """Deadline less than 24 hours from now returns 422."""
        user = _fake_user()

        from src.auth.dependencies import require_verified_rescuer
        from src.db.session import get_async_session

        _app.dependency_overrides[require_verified_rescuer] = lambda: user
        _app.dependency_overrides[get_async_session] = lambda: AsyncMock()

        try:
            async with AsyncClient(
                transport=ASGITransport(app=_app),
                base_url="http://test",
            ) as client:
                body = _valid_body(deadline=(datetime.now(UTC) + timedelta(hours=1)).isoformat())
                response = await client.post("/api/portal/emergencies", json=body)
        finally:
            _app.dependency_overrides.clear()

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_rejects_deadline_too_far(self) -> None:
        """Deadline more than 30 days returns 422."""
        user = _fake_user()

        from src.auth.dependencies import require_verified_rescuer
        from src.db.session import get_async_session

        _app.dependency_overrides[require_verified_rescuer] = lambda: user
        _app.dependency_overrides[get_async_session] = lambda: AsyncMock()

        try:
            async with AsyncClient(
                transport=ASGITransport(app=_app),
                base_url="http://test",
            ) as client:
                body = _valid_body(deadline=(datetime.now(UTC) + timedelta(days=60)).isoformat())
                response = await client.post("/api/portal/emergencies", json=body)
        finally:
            _app.dependency_overrides.clear()

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_rejects_zero_amount(self) -> None:
        """Zero amount returns 422."""
        user = _fake_user()

        from src.auth.dependencies import require_verified_rescuer
        from src.db.session import get_async_session

        _app.dependency_overrides[require_verified_rescuer] = lambda: user
        _app.dependency_overrides[get_async_session] = lambda: AsyncMock()

        try:
            async with AsyncClient(
                transport=ASGITransport(app=_app),
                base_url="http://test",
            ) as client:
                body = _valid_body()
                body["amount_needed_cents"] = 0
                response = await client.post("/api/portal/emergencies", json=body)
        finally:
            _app.dependency_overrides.clear()

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_limits_photos_to_three(self) -> None:
        """Photos list is trimmed to 3 max."""
        user = _fake_user()

        mock_case = MagicMock()
        mock_case.id = uuid4()
        mock_case.title = "Test"
        mock_case.description = "Test desc"
        mock_case.animal_id = None
        mock_case.rescuer_id = user.id
        mock_case.campaign_id = None
        mock_case.photos = ["a.jpg", "b.jpg", "c.jpg"]
        mock_case.amount_needed_cents = 10000
        mock_case.amount_raised_cents = 0
        mock_case.currency = "USD"
        mock_case.deadline = datetime.now(UTC) + timedelta(hours=72)
        mock_case.status = "active"
        mock_case.urgency = "high"
        mock_case.created_at = datetime.now(UTC)

        mock_db = AsyncMock()
        mock_db.commit = AsyncMock()

        from src.auth.dependencies import require_verified_rescuer
        from src.db.session import get_async_session

        _app.dependency_overrides[require_verified_rescuer] = lambda: user
        _app.dependency_overrides[get_async_session] = lambda: mock_db

        captured_kwargs = {}

        async def capture_create(**kwargs):
            captured_kwargs.update(kwargs)
            return mock_case

        try:
            with patch(
                "src.api.rescuer_emergencies.create_emergency_case",
                side_effect=capture_create,
            ):
                async with AsyncClient(
                    transport=ASGITransport(app=_app),
                    base_url="http://test",
                ) as client:
                    body = _valid_body()
                    body["photos"] = ["a.jpg", "b.jpg", "c.jpg", "d.jpg", "e.jpg"]
                    response = await client.post("/api/portal/emergencies", json=body)
        finally:
            _app.dependency_overrides.clear()

        assert response.status_code == 201
        # Verify photos were trimmed
        assert len(captured_kwargs.get("photos", [])) <= 3


class TestRequireVerifiedRescuer:
    """Tests for the require_verified_rescuer dependency."""

    @pytest.mark.asyncio
    async def test_staff_bypasses_rescuer_check(self) -> None:
        """Staff users are allowed without rescuer profile."""
        from src.auth.dependencies import require_verified_rescuer

        user = MagicMock(spec=User)
        user.id = uuid4()
        user.role = "staff"

        result = await require_verified_rescuer(user=user, db=AsyncMock())
        assert result == user

    @pytest.mark.asyncio
    async def test_admin_bypasses_rescuer_check(self) -> None:
        """Admin users are allowed without rescuer profile."""
        from src.auth.dependencies import require_verified_rescuer

        user = MagicMock(spec=User)
        user.id = uuid4()
        user.role = "admin"

        result = await require_verified_rescuer(user=user, db=AsyncMock())
        assert result == user

    @pytest.mark.asyncio
    async def test_non_rescuer_gets_403(self) -> None:
        """Non-rescuer user without profile gets 403."""
        from fastapi import HTTPException
        from src.auth.dependencies import require_verified_rescuer

        user = MagicMock(spec=User)
        user.id = uuid4()
        user.role = "adopter"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(HTTPException) as exc_info:
            await require_verified_rescuer(user=user, db=mock_db)

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_verified_rescuer_passes(self) -> None:
        """User with verified rescuer profile is allowed."""
        from src.auth.dependencies import require_verified_rescuer

        user = MagicMock(spec=User)
        user.id = uuid4()
        user.role = "adopter"

        mock_profile = MagicMock()
        mock_profile.is_verified = True

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_profile

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await require_verified_rescuer(user=user, db=mock_db)
        assert result == user
