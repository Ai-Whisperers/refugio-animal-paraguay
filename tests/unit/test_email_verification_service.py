"""Unit tests for email verification service."""

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from src.db.models.user import User
from src.db.models.verification_token import TokenType, VerificationToken
from src.services.email_verification_service import (
    VerificationResult,
    create_email_verification_token,
    verify_email,
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
    """Create a sample active user with unverified email."""
    user = MagicMock(spec=User)
    user.id = uuid.uuid4()
    user.email = "staff@refugio-shelter.org"
    user.is_active = True
    user.email_verified = False
    return user


@pytest.fixture()
def sample_verification_token():
    """Create a sample email verification token."""
    token = MagicMock(spec=VerificationToken)
    token.id = uuid.uuid4()
    token.user_id = uuid.uuid4()
    token.token = "test-verification-token"
    token.token_type = TokenType.EMAIL_VERIFICATION.value
    token.expires_at = datetime.now(UTC) + timedelta(hours=12)
    token.used_at = None
    return token


class TestCreateEmailVerificationToken:
    """Tests for create_email_verification_token."""

    @pytest.mark.asyncio()
    async def test_returns_token_for_valid_user(self, mock_db, sample_user):
        """Should return a token string when user exists."""
        mock_db.get.return_value = sample_user

        # Existing tokens query returns empty
        mock_existing = MagicMock()
        mock_existing.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_existing

        token = await create_email_verification_token(mock_db, str(sample_user.id))

        assert token is not None
        assert len(token) > 0
        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()

    @pytest.mark.asyncio()
    async def test_returns_none_for_unknown_user(self, mock_db):
        """Should return None when user does not exist."""
        mock_db.get.return_value = None

        token = await create_email_verification_token(mock_db, str(uuid.uuid4()))

        assert token is None
        mock_db.add.assert_not_called()

    @pytest.mark.asyncio()
    async def test_invalidates_existing_tokens(self, mock_db, sample_user):
        """Should mark existing unused tokens as used."""
        mock_db.get.return_value = sample_user

        old_token = MagicMock(spec=VerificationToken)
        old_token.used_at = None
        mock_existing = MagicMock()
        mock_existing.scalars.return_value.all.return_value = [old_token]
        mock_db.execute.return_value = mock_existing

        await create_email_verification_token(mock_db, str(sample_user.id))

        assert old_token.used_at is not None


class TestVerifyEmail:
    """Tests for verify_email with specific error codes."""

    @pytest.mark.asyncio()
    async def test_verifies_email_with_valid_token(
        self, mock_db, sample_user, sample_verification_token
    ):
        """Should set email_verified=True and mark token as used."""
        sample_verification_token.user_id = sample_user.id
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_verification_token
        mock_db.execute.return_value = mock_result
        mock_db.get.return_value = sample_user

        result = await verify_email(mock_db, "test-verification-token")

        assert result == VerificationResult.SUCCESS
        assert sample_user.email_verified is True
        assert sample_verification_token.used_at is not None

    @pytest.mark.asyncio()
    async def test_returns_invalid_token_for_nonexistent(self, mock_db):
        """Should return TOKEN_NOT_FOUND when token does not exist."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await verify_email(mock_db, "nonexistent-token")

        assert result == VerificationResult.TOKEN_NOT_FOUND

    @pytest.mark.asyncio()
    async def test_returns_token_expired_for_old_token(
        self, mock_db, sample_user, sample_verification_token
    ):
        """Should return TOKEN_EXPIRED when token is expired."""
        sample_verification_token.expires_at = datetime.now(UTC) - timedelta(hours=1)
        sample_verification_token.user_id = sample_user.id
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_verification_token
        mock_db.execute.return_value = mock_result

        result = await verify_email(mock_db, "test-verification-token")

        assert result == VerificationResult.TOKEN_EXPIRED

    @pytest.mark.asyncio()
    async def test_returns_token_already_used(self, mock_db, sample_verification_token):
        """Should return TOKEN_ALREADY_USED when token was previously consumed."""
        sample_verification_token.used_at = datetime.now(UTC) - timedelta(hours=1)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_verification_token
        mock_db.execute.return_value = mock_result

        result = await verify_email(mock_db, "test-verification-token")

        assert result == VerificationResult.TOKEN_ALREADY_USED

    @pytest.mark.asyncio()
    async def test_returns_user_not_found_for_inactive_user(
        self, mock_db, sample_user, sample_verification_token
    ):
        """Should return USER_NOT_FOUND when user is inactive."""
        sample_user.is_active = False
        sample_verification_token.user_id = sample_user.id
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_verification_token
        mock_db.execute.return_value = mock_result
        mock_db.get.return_value = sample_user

        result = await verify_email(mock_db, "test-verification-token")

        assert result == VerificationResult.USER_NOT_FOUND

    @pytest.mark.asyncio()
    async def test_idempotent_for_already_verified_user(
        self, mock_db, sample_user, sample_verification_token
    ):
        """Should return SUCCESS and mark token used if user already verified."""
        sample_user.email_verified = True
        sample_verification_token.user_id = sample_user.id
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_verification_token
        mock_db.execute.return_value = mock_result
        mock_db.get.return_value = sample_user

        result = await verify_email(mock_db, "test-verification-token")

        assert result == VerificationResult.SUCCESS
        assert sample_verification_token.used_at is not None

    @pytest.mark.asyncio()
    async def test_returns_user_not_found_for_missing_user(
        self, mock_db, sample_verification_token
    ):
        """Should return USER_NOT_FOUND when user does not exist."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_verification_token
        mock_db.execute.return_value = mock_result
        mock_db.get.return_value = None

        result = await verify_email(mock_db, "test-verification-token")

        assert result == VerificationResult.USER_NOT_FOUND


class TestVerificationResultEnum:
    """Tests for VerificationResult enum values."""

    def test_success_value(self) -> None:
        assert VerificationResult.SUCCESS == "success"

    def test_invalid_token_value(self) -> None:
        assert VerificationResult.TOKEN_NOT_FOUND == "invalid_token"

    def test_expired_value(self) -> None:
        assert VerificationResult.TOKEN_EXPIRED == "token_expired"

    def test_already_used_value(self) -> None:
        assert VerificationResult.TOKEN_ALREADY_USED == "token_already_used"

    def test_user_not_found_value(self) -> None:
        assert VerificationResult.USER_NOT_FOUND == "user_not_found"
