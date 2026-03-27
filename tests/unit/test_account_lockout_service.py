"""Unit tests for the account lockout service."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
from src.services.account_lockout_service import (
    MAX_FAILED_ATTEMPTS,
    is_account_locked,
    lockout_remaining_seconds,
    record_failed_attempt,
    reset_failed_attempts,
)


def _make_user(
    failed_attempts: int = 0,
    locked_until: datetime | None = None,
) -> MagicMock:
    user = MagicMock()
    user.id = UUID("00000000-0000-0000-0000-000000000001")
    user.failed_login_attempts = failed_attempts
    user.locked_until = locked_until
    return user


# --- is_account_locked ---


def test_not_locked_when_locked_until_is_none() -> None:
    user = _make_user()
    assert is_account_locked(user) is False


def test_not_locked_when_lockout_expired() -> None:
    past = datetime.now(UTC) - timedelta(minutes=1)
    user = _make_user(locked_until=past)
    assert is_account_locked(user) is False


def test_locked_when_lockout_active() -> None:
    future = datetime.now(UTC) + timedelta(minutes=10)
    user = _make_user(failed_attempts=MAX_FAILED_ATTEMPTS, locked_until=future)
    assert is_account_locked(user) is True


# --- lockout_remaining_seconds ---


def test_remaining_zero_when_no_lockout() -> None:
    user = _make_user()
    assert lockout_remaining_seconds(user) == 0


def test_remaining_zero_when_lockout_expired() -> None:
    past = datetime.now(UTC) - timedelta(seconds=30)
    user = _make_user(locked_until=past)
    assert lockout_remaining_seconds(user) == 0


def test_remaining_positive_when_locked() -> None:
    future = datetime.now(UTC) + timedelta(minutes=5)
    user = _make_user(locked_until=future)
    remaining = lockout_remaining_seconds(user)
    assert 290 <= remaining <= 300  # ~5 minutes


# --- record_failed_attempt ---


@pytest.mark.asyncio
async def test_record_increments_counter() -> None:
    db = AsyncMock()
    user = _make_user(failed_attempts=0)
    locked = await record_failed_attempt(db, user)
    assert user.failed_login_attempts == 1
    assert locked is False
    db.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_record_locks_at_threshold() -> None:
    db = AsyncMock()
    user = _make_user(failed_attempts=MAX_FAILED_ATTEMPTS - 1)
    locked = await record_failed_attempt(db, user)
    assert user.failed_login_attempts == MAX_FAILED_ATTEMPTS
    assert locked is True
    assert user.locked_until is not None


@pytest.mark.asyncio
async def test_record_does_not_lock_below_threshold() -> None:
    db = AsyncMock()
    user = _make_user(failed_attempts=2)
    locked = await record_failed_attempt(db, user)
    assert user.failed_login_attempts == 3
    assert locked is False


# --- reset_failed_attempts ---


@pytest.mark.asyncio
async def test_reset_clears_counter_and_lockout() -> None:
    db = AsyncMock()
    future = datetime.now(UTC) + timedelta(minutes=10)
    user = _make_user(failed_attempts=5, locked_until=future)
    await reset_failed_attempts(db, user)
    assert user.failed_login_attempts == 0
    assert user.locked_until is None
    db.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_reset_noop_when_already_zero() -> None:
    db = AsyncMock()
    user = _make_user(failed_attempts=0, locked_until=None)
    await reset_failed_attempts(db, user)
    db.flush.assert_not_awaited()
