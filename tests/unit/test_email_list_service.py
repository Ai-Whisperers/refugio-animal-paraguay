"""Unit tests for email list service — segmentation and unsubscribe logic.

Tests:
- populate_from_segment with various segment types
- Duplicate skipping behaviour
- unsubscribe_by_token happy path and invalid token
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from src.db.models.email_list import EmailList, EmailListMember, EmailListType, MemberStatus
from src.services.email_list_service import populate_from_segment, unsubscribe_by_token

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

LIST_ID = uuid4()
NOW = datetime.now(tz=UTC)


def _make_list(**overrides) -> MagicMock:
    defaults = {
        "id": LIST_ID,
        "name": "Test List",
        "list_type": EmailListType.DONORS,
        "status": "active",
        "created_at": NOW,
        "updated_at": NOW,
    }
    defaults.update(overrides)
    obj = MagicMock(spec=EmailList)
    for key, value in defaults.items():
        setattr(obj, key, value)
    return obj


def _make_member(**overrides) -> MagicMock:
    defaults = {
        "id": uuid4(),
        "email_list_id": LIST_ID,
        "email": "test@example.com",
        "name": "Test User",
        "status": MemberStatus.SUBSCRIBED,
        "unsubscribe_token": "validtoken123",
        "source_type": "donor",
        "source_id": uuid4(),
        "subscribed_at": NOW,
        "unsubscribed_at": None,
    }
    defaults.update(overrides)
    obj = MagicMock(spec=EmailListMember)
    for key, value in defaults.items():
        setattr(obj, key, value)
    return obj


# ---------------------------------------------------------------------------
# populate_from_segment
# ---------------------------------------------------------------------------


class TestPopulateFromSegment:
    """Tests for populate_from_segment service function."""

    @pytest.mark.asyncio
    async def test_returns_zero_counts_when_no_rows(self):
        """Returns zero counts when segment query returns nothing."""
        db = AsyncMock()
        email_list = _make_list(list_type=EmailListType.GENERAL)

        with patch(
            "src.services.email_list_service._fetch_segment_emails",
            new=AsyncMock(return_value=[]),
        ):
            result = await populate_from_segment(db, email_list)

        assert result["imported"] == 0
        assert result["skipped"] == 0
        assert result["total_after"] == 0

    @pytest.mark.asyncio
    async def test_imports_new_emails(self):
        """Imports emails not already on the list."""
        db = AsyncMock()
        email_list = _make_list(list_type=EmailListType.DONORS)

        donor_id = uuid4()
        segment_rows = [("alice@example.com", "Alice", donor_id, "donor")]

        # Existing members query returns empty
        existing_result = MagicMock()
        existing_result.all.return_value = []

        # Total-after count
        total_result = MagicMock()
        total_result.scalars.return_value.all.return_value = [MagicMock()]

        db.execute = AsyncMock(side_effect=[existing_result, total_result])

        with patch(
            "src.services.email_list_service._fetch_segment_emails",
            new=AsyncMock(return_value=segment_rows),
        ):
            result = await populate_from_segment(db, email_list)

        assert result["imported"] == 1
        assert result["skipped"] == 0
        assert result["total_after"] == 1
        db.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_skips_existing_emails(self):
        """Skips emails already present in the list."""
        db = AsyncMock()
        email_list = _make_list(list_type=EmailListType.DONORS)

        donor_id = uuid4()
        segment_rows = [("alice@example.com", "Alice", donor_id, "donor")]

        # Existing members query returns alice's email
        existing_result = MagicMock()
        existing_result.all.return_value = [("alice@example.com",)]

        # Total-after count
        total_result = MagicMock()
        total_result.scalars.return_value.all.return_value = [MagicMock()]

        db.execute = AsyncMock(side_effect=[existing_result, total_result])

        with patch(
            "src.services.email_list_service._fetch_segment_emails",
            new=AsyncMock(return_value=segment_rows),
        ):
            result = await populate_from_segment(db, email_list)

        assert result["imported"] == 0
        assert result["skipped"] == 1
        db.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_overwrite_mode_ignores_existing(self):
        """In overwrite mode, existing emails are not fetched for comparison."""
        db = AsyncMock()
        email_list = _make_list(list_type=EmailListType.DONORS)

        donor_id = uuid4()
        segment_rows = [("alice@example.com", "Alice", donor_id, "donor")]

        # Only one execute call — total_after count (no existing lookup)
        total_result = MagicMock()
        total_result.scalars.return_value.all.return_value = [MagicMock()]
        db.execute = AsyncMock(return_value=total_result)

        with patch(
            "src.services.email_list_service._fetch_segment_emails",
            new=AsyncMock(return_value=segment_rows),
        ):
            result = await populate_from_segment(db, email_list, overwrite=True)

        assert result["imported"] == 1


# ---------------------------------------------------------------------------
# unsubscribe_by_token
# ---------------------------------------------------------------------------


class TestUnsubscribeByToken:
    """Tests for unsubscribe_by_token service function."""

    @pytest.mark.asyncio
    async def test_returns_none_for_invalid_token(self):
        """Returns None when token does not match any member."""
        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=result_mock)

        result = await unsubscribe_by_token(db, "badtoken")
        assert result is None

    @pytest.mark.asyncio
    async def test_unsubscribes_active_member(self):
        """Sets status to UNSUBSCRIBED and records unsubscribed_at timestamp."""
        db = AsyncMock()
        member = _make_member(status=MemberStatus.SUBSCRIBED, unsubscribed_at=None)

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = member
        db.execute = AsyncMock(return_value=result_mock)

        result = await unsubscribe_by_token(db, "validtoken123")

        assert result is member
        assert member.status == MemberStatus.UNSUBSCRIBED
        assert member.unsubscribed_at is not None

    @pytest.mark.asyncio
    async def test_already_unsubscribed_member_is_returned_unchanged(self):
        """Returns already-unsubscribed member without changing unsubscribed_at."""
        db = AsyncMock()
        original_time = datetime(2026, 1, 1, tzinfo=UTC)
        member = _make_member(
            status=MemberStatus.UNSUBSCRIBED,
            unsubscribed_at=original_time,
        )

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = member
        db.execute = AsyncMock(return_value=result_mock)

        result = await unsubscribe_by_token(db, "validtoken123")

        assert result is member
        # Status and time should remain unchanged
        assert member.unsubscribed_at == original_time


# ---------------------------------------------------------------------------
# Schema validation
# ---------------------------------------------------------------------------


class TestEmailListSchemas:
    """Tests for Pydantic schema validation."""

    def test_email_list_create_requires_name(self):
        """EmailListCreate rejects empty name."""
        from pydantic import ValidationError
        from src.schemas.email_list import EmailListCreate

        with pytest.raises(ValidationError):
            EmailListCreate(name="", list_type="general")

    def test_member_add_normalizes_email(self):
        """MemberAdd accepts valid email."""
        from src.schemas.email_list import MemberAdd

        member = MemberAdd(email="Test@EXAMPLE.COM")
        assert "@" in member.email

    def test_segment_request_defaults(self):
        """SegmentRequest has sensible defaults."""
        from src.schemas.email_list import SegmentRequest

        req = SegmentRequest(list_type="donors")
        assert req.overwrite is False
