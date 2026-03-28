"""Unit tests for rescuer-voucher integration service."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from src.services.rescuer_voucher_integration_service import (
    MAX_REQUEST_NOTES_LENGTH,
    UNVERIFIED_RESCUER_VOUCHER_LIMIT,
    VALID_SERVICE_CATEGORIES,
    VERIFIED_RESCUER_VOUCHER_LIMIT,
    InvalidServiceCategoryError,
    RescuerProfileRequiredError,
    RescuerVoucherError,
    VoucherLimitExceededError,
    check_voucher_request_eligibility,
    get_rescuer_voucher_eligibility,
    get_rescuer_voucher_history,
    get_rescuer_voucher_stats,
    validate_request_notes,
    validate_service_category,
)

# ---------------------------------------------------------------------------
# Validation tests
# ---------------------------------------------------------------------------


class TestValidateServiceCategory:
    """Tests for service category validation."""

    def test_accepts_none(self) -> None:
        validate_service_category(None)

    def test_accepts_valid_categories(self) -> None:
        for cat in VALID_SERVICE_CATEGORIES:
            validate_service_category(cat)

    def test_rejects_invalid_category(self) -> None:
        with pytest.raises(InvalidServiceCategoryError, match="Invalid service category"):
            validate_service_category("invalid_category")

    def test_accepts_empty_string_as_none(self) -> None:
        # Empty string is falsy, treated same as None (no category filter)
        validate_service_category("")


class TestValidateRequestNotes:
    """Tests for request notes validation."""

    def test_accepts_none(self) -> None:
        validate_request_notes(None)

    def test_accepts_valid(self) -> None:
        validate_request_notes("Need vaccination for rescued puppy")

    def test_rejects_too_long(self) -> None:
        with pytest.raises(RescuerVoucherError, match="Notes too long"):
            validate_request_notes("A" * (MAX_REQUEST_NOTES_LENGTH + 1))

    def test_accepts_max_length(self) -> None:
        validate_request_notes("A" * MAX_REQUEST_NOTES_LENGTH)


# ---------------------------------------------------------------------------
# Helper mocks
# ---------------------------------------------------------------------------


def _mock_profile(is_verified: bool = False) -> MagicMock:
    """Create a mock rescuer profile."""
    profile = MagicMock()
    profile.id = uuid4()
    profile.user_id = uuid4()
    profile.is_verified = is_verified
    return profile


def _mock_db_no_profile() -> AsyncMock:
    """Mock DB that returns no profile."""
    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    db.execute.return_value = mock_result
    return db


def _mock_db_eligibility(
    profile: MagicMock,
    active_count: int = 0,
    redeemed_count: int = 0,
    total_redeemed_pyg: int = 0,
) -> AsyncMock:
    """Mock DB for eligibility check (4 queries: profile, active, redeemed, value)."""
    db = AsyncMock()
    call_count = 0

    def mock_execute(query):
        nonlocal call_count
        result = MagicMock()
        if call_count == 0:
            # _get_rescuer_profile
            result.scalar_one_or_none.return_value = profile
        elif call_count == 1:
            # _count_active_vouchers
            result.scalar_one.return_value = active_count
        elif call_count == 2:
            # redeemed count
            result.scalar_one.return_value = redeemed_count
        else:
            # total redeemed value
            result.scalar_one.return_value = total_redeemed_pyg
        call_count += 1
        return result

    db.execute = AsyncMock(side_effect=mock_execute)
    return db


# ---------------------------------------------------------------------------
# get_rescuer_voucher_eligibility tests
# ---------------------------------------------------------------------------


class TestGetRescuerVoucherEligibility:
    """Tests for voucher eligibility check."""

    @pytest.mark.asyncio
    async def test_verified_rescuer_eligibility(self) -> None:
        profile = _mock_profile(is_verified=True)
        db = _mock_db_eligibility(
            profile, active_count=2, redeemed_count=5, total_redeemed_pyg=500000
        )

        result = await get_rescuer_voucher_eligibility(profile.user_id, db)

        assert result["is_verified"] is True
        assert result["voucher_limit"] == VERIFIED_RESCUER_VOUCHER_LIMIT
        assert result["active_vouchers"] == 2
        assert result["remaining_slots"] == VERIFIED_RESCUER_VOUCHER_LIMIT - 2
        assert result["can_request_more"] is True
        assert result["lifetime_redeemed"] == 5
        assert result["lifetime_redeemed_pyg"] == 500000

    @pytest.mark.asyncio
    async def test_unverified_rescuer_eligibility(self) -> None:
        profile = _mock_profile(is_verified=False)
        db = _mock_db_eligibility(profile, active_count=0)

        result = await get_rescuer_voucher_eligibility(profile.user_id, db)

        assert result["is_verified"] is False
        assert result["voucher_limit"] == UNVERIFIED_RESCUER_VOUCHER_LIMIT
        assert result["can_request_more"] is True

    @pytest.mark.asyncio
    async def test_at_limit_cannot_request_more(self) -> None:
        profile = _mock_profile(is_verified=False)
        db = _mock_db_eligibility(profile, active_count=UNVERIFIED_RESCUER_VOUCHER_LIMIT)

        result = await get_rescuer_voucher_eligibility(profile.user_id, db)

        assert result["can_request_more"] is False
        assert result["remaining_slots"] == 0

    @pytest.mark.asyncio
    async def test_rejects_no_profile(self) -> None:
        db = _mock_db_no_profile()
        with pytest.raises(RescuerProfileRequiredError):
            await get_rescuer_voucher_eligibility(uuid4(), db)


# ---------------------------------------------------------------------------
# get_rescuer_voucher_history tests
# ---------------------------------------------------------------------------


class TestGetRescuerVoucherHistory:
    """Tests for voucher history retrieval."""

    @pytest.mark.asyncio
    async def test_returns_vouchers(self) -> None:
        profile = _mock_profile()
        mock_vouchers = [MagicMock() for _ in range(3)]
        db = AsyncMock()
        call_count = 0

        def mock_execute(query):
            nonlocal call_count
            result = MagicMock()
            if call_count == 0:
                result.scalar_one_or_none.return_value = profile
            else:
                result.scalars.return_value.all.return_value = mock_vouchers
            call_count += 1
            return result

        db.execute = AsyncMock(side_effect=mock_execute)

        result = await get_rescuer_voucher_history(profile.user_id, db)
        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_rejects_no_profile(self) -> None:
        db = _mock_db_no_profile()
        with pytest.raises(RescuerProfileRequiredError):
            await get_rescuer_voucher_history(uuid4(), db)

    @pytest.mark.asyncio
    async def test_rejects_invalid_category(self) -> None:
        profile = _mock_profile()
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = profile
        db.execute.return_value = mock_result

        with pytest.raises(InvalidServiceCategoryError):
            await get_rescuer_voucher_history(profile.user_id, db, service_category="nonexistent")


# ---------------------------------------------------------------------------
# get_rescuer_voucher_stats tests
# ---------------------------------------------------------------------------


class TestGetRescuerVoucherStats:
    """Tests for voucher statistics."""

    @pytest.mark.asyncio
    async def test_returns_stats(self) -> None:
        profile = _mock_profile(is_verified=True)
        db = AsyncMock()
        call_count = 0

        def mock_execute(query):
            nonlocal call_count
            result = MagicMock()
            if call_count == 0:
                result.scalar_one_or_none.return_value = profile
            elif call_count == 1:
                # status counts
                result.all.return_value = [("assigned", 2), ("redeemed", 5)]
            elif call_count == 2:
                # status values
                result.all.return_value = [("assigned", 200000), ("redeemed", 500000)]
            else:
                # category counts
                result.all.return_value = [("vaccination", 3), ("sterilization", 2)]
            call_count += 1
            return result

        db.execute = AsyncMock(side_effect=mock_execute)

        result = await get_rescuer_voucher_stats(profile.user_id, db)
        assert result["is_verified"] is True
        assert result["total_vouchers"] == 7
        assert result["total_value_pyg"] == 700000
        assert result["by_category"] == {"vaccination": 3, "sterilization": 2}

    @pytest.mark.asyncio
    async def test_rejects_no_profile(self) -> None:
        db = _mock_db_no_profile()
        with pytest.raises(RescuerProfileRequiredError):
            await get_rescuer_voucher_stats(uuid4(), db)


# ---------------------------------------------------------------------------
# check_voucher_request_eligibility tests
# ---------------------------------------------------------------------------


class TestCheckVoucherRequestEligibility:
    """Tests for voucher request pre-check."""

    @pytest.mark.asyncio
    async def test_eligible_rescuer(self) -> None:
        profile = _mock_profile(is_verified=True)
        db = AsyncMock()
        call_count = 0

        def mock_execute(query):
            nonlocal call_count
            result = MagicMock()
            if call_count == 0:
                result.scalar_one_or_none.return_value = profile
            else:
                result.scalar_one.return_value = 2
            call_count += 1
            return result

        db.execute = AsyncMock(side_effect=mock_execute)

        result = await check_voucher_request_eligibility(profile.user_id, "vaccination", db)
        assert result["eligible"] is True
        assert result["remaining_slots"] == VERIFIED_RESCUER_VOUCHER_LIMIT - 2

    @pytest.mark.asyncio
    async def test_rejects_at_limit(self) -> None:
        profile = _mock_profile(is_verified=False)
        db = AsyncMock()
        call_count = 0

        def mock_execute(query):
            nonlocal call_count
            result = MagicMock()
            if call_count == 0:
                result.scalar_one_or_none.return_value = profile
            else:
                result.scalar_one.return_value = UNVERIFIED_RESCUER_VOUCHER_LIMIT
            call_count += 1
            return result

        db.execute = AsyncMock(side_effect=mock_execute)

        with pytest.raises(VoucherLimitExceededError):
            await check_voucher_request_eligibility(profile.user_id, "vaccination", db)

    @pytest.mark.asyncio
    async def test_rejects_invalid_category(self) -> None:
        with pytest.raises(InvalidServiceCategoryError):
            await check_voucher_request_eligibility(uuid4(), "nonexistent", AsyncMock())

    @pytest.mark.asyncio
    async def test_accepts_none_category(self) -> None:
        profile = _mock_profile()
        db = AsyncMock()
        call_count = 0

        def mock_execute(query):
            nonlocal call_count
            result = MagicMock()
            if call_count == 0:
                result.scalar_one_or_none.return_value = profile
            else:
                result.scalar_one.return_value = 0
            call_count += 1
            return result

        db.execute = AsyncMock(side_effect=mock_execute)

        result = await check_voucher_request_eligibility(profile.user_id, None, db)
        assert result["eligible"] is True


# ---------------------------------------------------------------------------
# Error class tests
# ---------------------------------------------------------------------------


class TestErrorClasses:
    """Tests for custom exception classes."""

    def test_base_error(self) -> None:
        err = RescuerVoucherError("bad", details="detail")
        assert err.message == "bad"
        assert err.details == "detail"

    def test_profile_required_error(self) -> None:
        uid = uuid4()
        err = RescuerProfileRequiredError(uid)
        assert "Rescuer profile required" in err.message

    def test_voucher_limit_exceeded_error(self) -> None:
        err = VoucherLimitExceededError(10)
        assert "Voucher limit exceeded" in err.message
        assert "10" in err.details

    def test_invalid_service_category_error(self) -> None:
        err = InvalidServiceCategoryError("bad_cat")
        assert "Invalid service category" in err.message
        assert "bad_cat" in err.details


# ---------------------------------------------------------------------------
# Constants tests
# ---------------------------------------------------------------------------


class TestConstants:
    """Verify service constants."""

    def test_valid_categories(self) -> None:
        expected = {
            "vaccination",
            "sterilization",
            "consultation",
            "emergency",
            "surgery",
            "dental",
            "deworming",
            "general",
        }
        assert expected == VALID_SERVICE_CATEGORIES

    def test_verified_limit(self) -> None:
        assert VERIFIED_RESCUER_VOUCHER_LIMIT == 20

    def test_unverified_limit(self) -> None:
        assert UNVERIFIED_RESCUER_VOUCHER_LIMIT == 5

    def test_max_request_notes(self) -> None:
        assert MAX_REQUEST_NOTES_LENGTH == 1000
