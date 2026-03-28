"""Unit tests for anti-gaming protection service."""

from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from src.services.anti_gaming_service import (
    MAX_DAILY_ATTEMPTS_PER_ANIMAL,
    MAX_DAILY_ATTEMPTS_PER_USER,
    MIN_ATTEMPT_INTERVAL_SECONDS,
    SAME_ANIMAL_COOLDOWN_MINUTES,
    AntiGamingError,
    check_rate_limits,
)

# --- Test AntiGamingError ---


class TestAntiGamingError:
    """Tests for AntiGamingError exception."""

    def test_exception_attributes(self) -> None:
        exc = AntiGamingError(
            rule="rapid_fire",
            message="Too fast",
            retry_after_seconds=10,
        )
        assert exc.rule == "rapid_fire"
        assert exc.message == "Too fast"
        assert exc.retry_after_seconds == 10

    def test_exception_without_retry(self) -> None:
        exc = AntiGamingError(
            rule="daily_limit",
            message="Limit reached",
        )
        assert exc.retry_after_seconds is None

    def test_exception_is_exception(self) -> None:
        exc = AntiGamingError(rule="test", message="test")
        assert isinstance(exc, Exception)


# --- Test check_rate_limits ---


class TestCheckRateLimits:
    """Tests for check_rate_limits."""

    @pytest.mark.asyncio
    async def test_passes_when_no_previous_attempts(self) -> None:
        db = AsyncMock()
        user_id = uuid4()
        animal_id = uuid4()

        # No previous attempts
        rapid_result = MagicMock()
        rapid_result.scalar_one_or_none.return_value = None

        same_animal_result = MagicMock()
        same_animal_result.scalar_one.return_value = 0

        daily_result = MagicMock()
        daily_result.scalar_one.return_value = 0

        db.execute = AsyncMock(side_effect=[rapid_result, same_animal_result, daily_result])

        # Should not raise
        await check_rate_limits(db, user_id, animal_id)

    @pytest.mark.asyncio
    async def test_rapid_fire_violation(self) -> None:
        db = AsyncMock()
        user_id = uuid4()
        animal_id = uuid4()

        # Last attempt was 2 seconds ago
        recent_time = datetime.now() - timedelta(seconds=2)
        rapid_result = MagicMock()
        rapid_result.scalar_one_or_none.return_value = recent_time

        db.execute = AsyncMock(return_value=rapid_result)

        with pytest.raises(AntiGamingError) as exc_info:
            await check_rate_limits(db, user_id, animal_id)

        assert exc_info.value.rule == "rapid_fire"
        assert exc_info.value.retry_after_seconds is not None
        assert exc_info.value.retry_after_seconds > 0

    @pytest.mark.asyncio
    async def test_same_animal_cooldown_violation(self) -> None:
        db = AsyncMock()
        user_id = uuid4()
        animal_id = uuid4()

        # No rapid fire
        rapid_result = MagicMock()
        rapid_result.scalar_one_or_none.return_value = None

        # Max attempts for this animal reached
        same_animal_result = MagicMock()
        same_animal_result.scalar_one.return_value = MAX_DAILY_ATTEMPTS_PER_ANIMAL

        db.execute = AsyncMock(side_effect=[rapid_result, same_animal_result])

        with pytest.raises(AntiGamingError) as exc_info:
            await check_rate_limits(db, user_id, animal_id)

        assert exc_info.value.rule == "same_animal_cooldown"
        assert str(MAX_DAILY_ATTEMPTS_PER_ANIMAL) in exc_info.value.message

    @pytest.mark.asyncio
    async def test_daily_limit_violation(self) -> None:
        db = AsyncMock()
        user_id = uuid4()
        animal_id = uuid4()

        # No rapid fire
        rapid_result = MagicMock()
        rapid_result.scalar_one_or_none.return_value = None

        # Under animal limit
        same_animal_result = MagicMock()
        same_animal_result.scalar_one.return_value = 1

        # Over daily limit
        daily_result = MagicMock()
        daily_result.scalar_one.return_value = MAX_DAILY_ATTEMPTS_PER_USER

        db.execute = AsyncMock(side_effect=[rapid_result, same_animal_result, daily_result])

        with pytest.raises(AntiGamingError) as exc_info:
            await check_rate_limits(db, user_id, animal_id)

        assert exc_info.value.rule == "daily_limit"
        assert exc_info.value.retry_after_seconds is None

    @pytest.mark.asyncio
    async def test_old_attempt_does_not_trigger_rapid_fire(self) -> None:
        db = AsyncMock()
        user_id = uuid4()
        animal_id = uuid4()

        # Last attempt was 60 seconds ago (well beyond MIN_ATTEMPT_INTERVAL_SECONDS)
        old_time = datetime.now() - timedelta(seconds=60)
        rapid_result = MagicMock()
        rapid_result.scalar_one_or_none.return_value = old_time

        same_animal_result = MagicMock()
        same_animal_result.scalar_one.return_value = 0

        daily_result = MagicMock()
        daily_result.scalar_one.return_value = 0

        db.execute = AsyncMock(side_effect=[rapid_result, same_animal_result, daily_result])

        # Should not raise
        await check_rate_limits(db, user_id, animal_id)


# --- Test constants ---


class TestConstants:
    """Tests for anti-gaming constants."""

    def test_cooldown_is_positive(self) -> None:
        assert SAME_ANIMAL_COOLDOWN_MINUTES > 0

    def test_daily_limits_are_positive(self) -> None:
        assert MAX_DAILY_ATTEMPTS_PER_USER > 0
        assert MAX_DAILY_ATTEMPTS_PER_ANIMAL > 0

    def test_animal_limit_less_than_daily(self) -> None:
        assert MAX_DAILY_ATTEMPTS_PER_ANIMAL < MAX_DAILY_ATTEMPTS_PER_USER

    def test_min_interval_is_positive(self) -> None:
        assert MIN_ATTEMPT_INTERVAL_SECONDS > 0
