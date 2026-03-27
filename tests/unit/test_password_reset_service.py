"""Unit tests for password reset service."""

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from src.db.models.user import User
from src.db.models.verification_token import TokenType, VerificationToken
from src.services.password_reset_service import (
    create_password_reset_token,
    reset_password,
    validate_reset_token,
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
def sample_user():
    """Create a sample active user."""
    user = MagicMock(spec=User)
    user.id = uuid.uuid4()
    user.email = "staff@refugio.test"
    user.is_active = True
    user.hashed_password = "hashed_old_password"
    return user


@pytest.fixture()
def sample_token():
    """Create a sample verification token."""
    token = MagicMock(spec=VerificationToken)
    token.id = uuid.uuid4()
    token.user_id = uuid.uuid4()
    token.token = "test-reset-token-value"
    token.token_type = TokenType.PASSWORD_RESET.value
    token.expires_at = datetime.now(UTC) + timedelta(hours=1)
    token.used_at = None
    return token


class TestCreatePasswordResetToken:
    """Tests for create_password_reset_token."""

    @pytest.mark.asyncio()
    async def test_returns_token_for_active_user(self, mock_db, sample_user):
        """Should return a token string when user exists and is active."""
        # Arrange: user lookup returns sample_user
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user
        # Existing tokens query returns empty
        mock_existing = MagicMock()
        mock_existing.scalars.return_value.all.return_value = []
        mock_db.execute.side_effect = [mock_result, mock_existing]

        # Act
        token = await create_password_reset_token(mock_db, "staff@refugio.test")

        # Assert
        assert token is not None
        assert len(token) > 0
        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()

    @pytest.mark.asyncio()
    async def test_returns_none_for_unknown_email(self, mock_db):
        """Should return None when email does not exist."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        token = await create_password_reset_token(mock_db, "unknown@test.com")

        assert token is None
        mock_db.add.assert_not_called()

    @pytest.mark.asyncio()
    async def test_returns_none_for_inactive_user(self, mock_db, sample_user):
        """Should return None when user is inactive."""
        sample_user.is_active = False
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user
        mock_db.execute.return_value = mock_result

        token = await create_password_reset_token(mock_db, "staff@refugio.test")

        assert token is None

    @pytest.mark.asyncio()
    async def test_invalidates_existing_tokens(self, mock_db, sample_user):
        """Should mark existing unused tokens as used."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user

        old_token = MagicMock(spec=VerificationToken)
        old_token.used_at = None
        mock_existing = MagicMock()
        mock_existing.scalars.return_value.all.return_value = [old_token]

        mock_db.execute.side_effect = [mock_result, mock_existing]

        await create_password_reset_token(mock_db, "staff@refugio.test")

        assert old_token.used_at is not None


class TestValidateResetToken:
    """Tests for validate_reset_token."""

    @pytest.mark.asyncio()
    async def test_returns_token_when_valid(self, mock_db, sample_token):
        """Should return the token record when valid and not expired."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_token
        mock_db.execute.return_value = mock_result

        result = await validate_reset_token(mock_db, "test-reset-token-value")

        assert result is sample_token

    @pytest.mark.asyncio()
    async def test_returns_none_when_not_found(self, mock_db):
        """Should return None when token does not exist."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await validate_reset_token(mock_db, "nonexistent-token")

        assert result is None

    @pytest.mark.asyncio()
    async def test_returns_none_when_expired(self, mock_db, sample_token):
        """Should return None when token is expired."""
        sample_token.expires_at = datetime.now(UTC) - timedelta(hours=1)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_token
        mock_db.execute.return_value = mock_result

        result = await validate_reset_token(mock_db, "test-reset-token-value")

        assert result is None


class TestResetPassword:
    """Tests for reset_password."""

    @pytest.mark.asyncio()
    async def test_resets_password_with_valid_token(self, mock_db, sample_user, sample_token):
        """Should update password and mark token as used."""
        sample_token.user_id = sample_user.id
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_token
        mock_db.execute.return_value = mock_result
        mock_db.get.return_value = sample_user

        with patch("src.services.password_reset_service.hash_password", return_value="new_hashed"):
            success = await reset_password(mock_db, "test-reset-token-value", "NewPass123!")

        assert success is True
        assert sample_user.hashed_password == "new_hashed"
        assert sample_token.used_at is not None

    @pytest.mark.asyncio()
    async def test_returns_false_for_invalid_token(self, mock_db):
        """Should return False when token is invalid."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        success = await reset_password(mock_db, "bad-token", "NewPass123!")

        assert success is False

    @pytest.mark.asyncio()
    async def test_returns_false_for_inactive_user(self, mock_db, sample_user, sample_token):
        """Should return False when user is inactive."""
        sample_user.is_active = False
        sample_token.user_id = sample_user.id
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_token
        mock_db.execute.return_value = mock_result
        mock_db.get.return_value = sample_user

        success = await reset_password(mock_db, "test-reset-token-value", "NewPass123!")

        assert success is False
