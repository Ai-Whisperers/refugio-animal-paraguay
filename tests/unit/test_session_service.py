"""Unit tests for session service."""

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.db.models.active_session import ActiveSession
from src.services.session_service import (
    SESSION_INACTIVITY_TIMEOUT_MINUTES,
    create_session,
    list_active_sessions,
    revoke_all_user_sessions,
    revoke_session,
    validate_session,
)


@pytest.fixture()
def mock_db():
    """Create a mock async database session."""
    db = AsyncMock()
    db.execute = AsyncMock()
    db.flush = AsyncMock()
    db.add = MagicMock()
    db.get = AsyncMock()
    return db


@pytest.fixture()
def active_session():
    """Create a sample active session."""
    session = MagicMock(spec=ActiveSession)
    session.id = uuid.uuid4()
    session.user_id = uuid.uuid4()
    session.jti = "test-jti-value"
    session.created_at = datetime.now(UTC)
    session.last_activity = datetime.now(UTC)
    session.expires_at = datetime.now(UTC) + timedelta(hours=1)
    session.revoked_at = None
    session.ip_address = "127.0.0.1"
    session.user_agent = "TestAgent/1.0"
    return session


class TestCreateSession:
    """Tests for create_session."""

    @pytest.mark.asyncio()
    async def test_creates_session_and_returns_jti(self, mock_db):
        """Should create a session record and return a JTI string."""
        user_id = str(uuid.uuid4())
        expires_at = datetime.now(UTC) + timedelta(hours=1)

        jti = await create_session(
            mock_db,
            user_id=user_id,
            token_expires_at=expires_at,
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
        )

        assert jti is not None
        assert len(jti) == 32  # uuid4().hex is 32 chars
        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()


class TestValidateSession:
    """Tests for validate_session."""

    @pytest.mark.asyncio()
    async def test_returns_session_when_valid(self, mock_db, active_session):
        """Should return session when not revoked, not expired, not timed out."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = active_session
        mock_db.execute.return_value = mock_result

        result = await validate_session(mock_db, "test-jti-value")

        assert result is active_session

    @pytest.mark.asyncio()
    async def test_returns_none_when_not_found(self, mock_db):
        """Should return None when session JTI does not exist."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await validate_session(mock_db, "nonexistent-jti")

        assert result is None

    @pytest.mark.asyncio()
    async def test_returns_none_when_expired(self, mock_db, active_session):
        """Should return None when session JWT has expired."""
        active_session.expires_at = datetime.now(UTC) - timedelta(hours=1)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = active_session
        mock_db.execute.return_value = mock_result

        result = await validate_session(mock_db, "test-jti-value")

        assert result is None

    @pytest.mark.asyncio()
    async def test_returns_none_when_timed_out(self, mock_db, active_session):
        """Should return None when session has been inactive too long."""
        active_session.last_activity = datetime.now(UTC) - timedelta(
            minutes=SESSION_INACTIVITY_TIMEOUT_MINUTES + 1
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = active_session
        mock_db.execute.return_value = mock_result

        result = await validate_session(mock_db, "test-jti-value")

        assert result is None


class TestRevokeSession:
    """Tests for revoke_session."""

    @pytest.mark.asyncio()
    async def test_revokes_active_session(self, mock_db, active_session):
        """Should mark session as revoked."""
        mock_db.get.return_value = active_session

        result = await revoke_session(mock_db, str(active_session.id))

        assert result is True
        assert active_session.revoked_at is not None

    @pytest.mark.asyncio()
    async def test_returns_false_for_nonexistent_session(self, mock_db):
        """Should return False when session not found."""
        mock_db.get.return_value = None

        result = await revoke_session(mock_db, str(uuid.uuid4()))

        assert result is False

    @pytest.mark.asyncio()
    async def test_returns_false_for_already_revoked(self, mock_db, active_session):
        """Should return False when session is already revoked."""
        active_session.revoked_at = datetime.now(UTC)
        mock_db.get.return_value = active_session

        result = await revoke_session(mock_db, str(active_session.id))

        assert result is False


class TestRevokeAllUserSessions:
    """Tests for revoke_all_user_sessions."""

    @pytest.mark.asyncio()
    async def test_revokes_all_active_sessions(self, mock_db):
        """Should revoke all active sessions for a user."""
        session1 = MagicMock(spec=ActiveSession)
        session1.revoked_at = None
        session2 = MagicMock(spec=ActiveSession)
        session2.revoked_at = None

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [session1, session2]
        mock_db.execute.return_value = mock_result

        count = await revoke_all_user_sessions(mock_db, str(uuid.uuid4()))

        assert count == 2
        assert session1.revoked_at is not None
        assert session2.revoked_at is not None
