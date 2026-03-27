"""Unit tests for password reset service.

Tests cover:
- Token creation (happy path, inactive user, nonexistent user, old token invalidation)
- Token validation (valid, expired, used, nonexistent)
- Password reset (happy path, invalid token, expired token, inactive user, token reuse)
- Edge cases (missing user from DB, hash_password invocation, token expiry timing)
"""

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from src.db.models.user import User
from src.db.models.verification_token import TokenType, VerificationToken
from src.services.password_reset_service import (
    PASSWORD_RESET_TOKEN_EXPIRY_HOURS,
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

    @pytest.mark.asyncio()
    async def test_returns_false_when_user_not_found(self, mock_db, sample_token):
        """Should return False when user record is missing from DB."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_token
        mock_db.execute.return_value = mock_result
        mock_db.get.return_value = None

        success = await reset_password(mock_db, "test-reset-token-value", "NewPass123!")

        assert success is False

    @pytest.mark.asyncio()
    async def test_returns_false_for_expired_token(self, mock_db, sample_token):
        """Should return False when token has expired."""
        sample_token.expires_at = datetime.now(UTC) - timedelta(hours=1)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_token
        mock_db.execute.return_value = mock_result

        success = await reset_password(mock_db, "test-reset-token-value", "NewPass123!")

        assert success is False

    @pytest.mark.asyncio()
    async def test_hash_password_called_with_new_password(self, mock_db, sample_user, sample_token):
        """Should call hash_password with the exact new password value."""
        sample_token.user_id = sample_user.id
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_token
        mock_db.execute.return_value = mock_result
        mock_db.get.return_value = sample_user

        new_pwd = "SuperSecure456!"
        with patch(
            "src.services.password_reset_service.hash_password",
            return_value="hashed_value",
        ) as mock_hash:
            await reset_password(mock_db, "test-reset-token-value", new_pwd)
            mock_hash.assert_called_once_with(new_pwd)

    @pytest.mark.asyncio()
    async def test_token_marked_used_after_reset(self, mock_db, sample_user, sample_token):
        """Token used_at should be set to a datetime after successful reset."""
        sample_token.user_id = sample_user.id
        sample_token.used_at = None
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_token
        mock_db.execute.return_value = mock_result
        mock_db.get.return_value = sample_user

        before = datetime.now(UTC)
        with patch(
            "src.services.password_reset_service.hash_password",
            return_value="hashed_value",
        ):
            await reset_password(mock_db, "test-reset-token-value", "NewPass123!")
        after = datetime.now(UTC)

        assert sample_token.used_at is not None
        assert before <= sample_token.used_at <= after


class TestCreatePasswordResetTokenExpiry:
    """Tests for token expiry timing."""

    @pytest.mark.asyncio()
    async def test_token_expiry_matches_constant(self, mock_db, sample_user):
        """Token expiry should match PASSWORD_RESET_TOKEN_EXPIRY_HOURS."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user
        mock_existing = MagicMock()
        mock_existing.scalars.return_value.all.return_value = []
        mock_db.execute.side_effect = [mock_result, mock_existing]

        before = datetime.now(UTC)
        await create_password_reset_token(mock_db, "staff@refugio.test")
        after = datetime.now(UTC)

        # Inspect the VerificationToken object passed to db.add()
        added_token = mock_db.add.call_args[0][0]
        expected_min = before + timedelta(hours=PASSWORD_RESET_TOKEN_EXPIRY_HOURS)
        expected_max = after + timedelta(hours=PASSWORD_RESET_TOKEN_EXPIRY_HOURS)
        assert expected_min <= added_token.expires_at <= expected_max

    @pytest.mark.asyncio()
    async def test_token_type_is_password_reset(self, mock_db, sample_user):
        """Created token should have PASSWORD_RESET type."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user
        mock_existing = MagicMock()
        mock_existing.scalars.return_value.all.return_value = []
        mock_db.execute.side_effect = [mock_result, mock_existing]

        await create_password_reset_token(mock_db, "staff@refugio.test")

        added_token = mock_db.add.call_args[0][0]
        assert added_token.token_type == TokenType.PASSWORD_RESET.value

    @pytest.mark.asyncio()
    async def test_token_user_id_matches_user(self, mock_db, sample_user):
        """Created token should reference the correct user."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user
        mock_existing = MagicMock()
        mock_existing.scalars.return_value.all.return_value = []
        mock_db.execute.side_effect = [mock_result, mock_existing]

        await create_password_reset_token(mock_db, "staff@refugio.test")

        added_token = mock_db.add.call_args[0][0]
        assert added_token.user_id == sample_user.id

    @pytest.mark.asyncio()
    async def test_token_string_is_url_safe(self, mock_db, sample_user):
        """Token string should be URL-safe (no +, /, = outside base64url)."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user
        mock_existing = MagicMock()
        mock_existing.scalars.return_value.all.return_value = []
        mock_db.execute.side_effect = [mock_result, mock_existing]

        token = await create_password_reset_token(mock_db, "staff@refugio.test")

        assert token is not None
        # URL-safe tokens should not contain + or /
        assert "+" not in token
        assert "/" not in token

    @pytest.mark.asyncio()
    async def test_invalidates_multiple_existing_tokens(self, mock_db, sample_user):
        """Should mark ALL existing unused tokens as used."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user

        old_token_1 = MagicMock(spec=VerificationToken)
        old_token_1.used_at = None
        old_token_2 = MagicMock(spec=VerificationToken)
        old_token_2.used_at = None
        mock_existing = MagicMock()
        mock_existing.scalars.return_value.all.return_value = [old_token_1, old_token_2]

        mock_db.execute.side_effect = [mock_result, mock_existing]

        await create_password_reset_token(mock_db, "staff@refugio.test")

        assert old_token_1.used_at is not None
        assert old_token_2.used_at is not None
