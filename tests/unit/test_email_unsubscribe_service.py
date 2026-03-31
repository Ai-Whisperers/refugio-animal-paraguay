"""Unit tests for email unsubscribe service.

Tests token generation, validation, and bulk email preference disabling
with mocked database sessions.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
from jose import jwt
from src.services.email_unsubscribe_service import (
    UNSUBSCRIBE_TOKEN_EXPIRE_DAYS,
    UNSUBSCRIBE_TOKEN_PURPOSE,
    generate_unsubscribe_token,
    unsubscribe_all_email,
    validate_unsubscribe_token,
)

TEST_SECRET = "test-secret-key-at-least-32-characters-long"
TEST_ALGORITHM = "HS256"


class TestGenerateUnsubscribeToken:
    """Tests for generate_unsubscribe_token function."""

    def test_returns_a_string(self) -> None:
        token = generate_unsubscribe_token(uuid4(), TEST_SECRET)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_token_encodes_user_id(self) -> None:
        user_id = uuid4()
        token = generate_unsubscribe_token(user_id, TEST_SECRET)
        payload = jwt.decode(token, TEST_SECRET, algorithms=[TEST_ALGORITHM])
        assert payload["sub"] == str(user_id)

    def test_token_has_unsubscribe_purpose(self) -> None:
        token = generate_unsubscribe_token(uuid4(), TEST_SECRET)
        payload = jwt.decode(token, TEST_SECRET, algorithms=[TEST_ALGORITHM])
        assert payload["purpose"] == UNSUBSCRIBE_TOKEN_PURPOSE

    def test_token_has_expiry(self) -> None:
        token = generate_unsubscribe_token(uuid4(), TEST_SECRET)
        payload = jwt.decode(token, TEST_SECRET, algorithms=[TEST_ALGORITHM])
        assert "exp" in payload

    def test_token_expires_in_30_days(self) -> None:
        before = datetime.now(UTC)
        token = generate_unsubscribe_token(uuid4(), TEST_SECRET)
        after = datetime.now(UTC)

        payload = jwt.decode(token, TEST_SECRET, algorithms=[TEST_ALGORITHM])
        expiry = datetime.fromtimestamp(payload["exp"], tz=UTC)

        expected_min = before + timedelta(days=UNSUBSCRIBE_TOKEN_EXPIRE_DAYS - 1)
        expected_max = after + timedelta(days=UNSUBSCRIBE_TOKEN_EXPIRE_DAYS + 1)
        assert expected_min <= expiry <= expected_max

    def test_different_users_get_different_tokens(self) -> None:
        token1 = generate_unsubscribe_token(uuid4(), TEST_SECRET)
        token2 = generate_unsubscribe_token(uuid4(), TEST_SECRET)
        assert token1 != token2


class TestValidateUnsubscribeToken:
    """Tests for validate_unsubscribe_token function."""

    def test_returns_correct_user_id(self) -> None:
        user_id = uuid4()
        token = generate_unsubscribe_token(user_id, TEST_SECRET)
        result = validate_unsubscribe_token(token, TEST_SECRET)
        assert result == user_id

    def test_raises_on_invalid_signature(self) -> None:
        token = generate_unsubscribe_token(uuid4(), TEST_SECRET)
        with pytest.raises(ValueError, match="Invalid or expired"):
            validate_unsubscribe_token(token, "wrong-secret-key-that-is-different-here")

    def test_raises_on_expired_token(self) -> None:
        user_id = uuid4()
        expired_payload = {
            "sub": str(user_id),
            "purpose": UNSUBSCRIBE_TOKEN_PURPOSE,
            "exp": datetime.now(UTC) - timedelta(seconds=1),
        }
        expired_token = jwt.encode(expired_payload, TEST_SECRET, algorithm=TEST_ALGORITHM)
        with pytest.raises(ValueError, match="Invalid or expired"):
            validate_unsubscribe_token(expired_token, TEST_SECRET)

    def test_raises_on_wrong_purpose(self) -> None:
        payload = {
            "sub": str(uuid4()),
            "purpose": "login",
            "exp": datetime.now(UTC) + timedelta(days=1),
        }
        token = jwt.encode(payload, TEST_SECRET, algorithm=TEST_ALGORITHM)
        with pytest.raises(ValueError, match="purpose"):
            validate_unsubscribe_token(token, TEST_SECRET)

    def test_raises_on_missing_sub(self) -> None:
        payload = {
            "purpose": UNSUBSCRIBE_TOKEN_PURPOSE,
            "exp": datetime.now(UTC) + timedelta(days=1),
        }
        token = jwt.encode(payload, TEST_SECRET, algorithm=TEST_ALGORITHM)
        with pytest.raises(ValueError, match="subject"):
            validate_unsubscribe_token(token, TEST_SECRET)

    def test_raises_on_invalid_uuid_sub(self) -> None:
        payload = {
            "sub": "not-a-uuid",
            "purpose": UNSUBSCRIBE_TOKEN_PURPOSE,
            "exp": datetime.now(UTC) + timedelta(days=1),
        }
        token = jwt.encode(payload, TEST_SECRET, algorithm=TEST_ALGORITHM)
        with pytest.raises(ValueError, match="UUID"):
            validate_unsubscribe_token(token, TEST_SECRET)

    def test_raises_on_garbage_token(self) -> None:
        with pytest.raises(ValueError, match="Invalid or expired"):
            validate_unsubscribe_token("garbage.token.here", TEST_SECRET)

    def test_returns_uuid_type(self) -> None:
        user_id = uuid4()
        token = generate_unsubscribe_token(user_id, TEST_SECRET)
        result = validate_unsubscribe_token(token, TEST_SECRET)
        assert isinstance(result, UUID)


class TestUnsubscribeAllEmail:
    """Tests for unsubscribe_all_email function."""

    @pytest.mark.asyncio
    async def test_returns_count_of_notification_types(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result
        db.flush = AsyncMock()

        from src.services.notification_preference_service import NOTIFICATION_TYPES

        count = await unsubscribe_all_email(db, uuid4())
        assert count == len(NOTIFICATION_TYPES)

    @pytest.mark.asyncio
    async def test_creates_new_preferences_when_missing(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result
        db.flush = AsyncMock()

        await unsubscribe_all_email(db, uuid4())

        # db.add should be called for each notification type
        assert db.add.call_count > 0

    @pytest.mark.asyncio
    async def test_updates_existing_preferences_to_disabled(self) -> None:
        db = AsyncMock()
        existing_pref = MagicMock()
        existing_pref.enabled = True
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_pref
        db.execute.return_value = mock_result
        db.flush = AsyncMock()

        await unsubscribe_all_email(db, uuid4())

        assert existing_pref.enabled is False

    @pytest.mark.asyncio
    async def test_flushes_after_updates(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result
        db.flush = AsyncMock()

        await unsubscribe_all_email(db, uuid4())

        db.flush.assert_awaited_once()
