"""Unit tests for referral tracking service."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.services.referral_service import (
    REFERRAL_EXPIRY_DAYS,
    VALID_CONVERSION_TYPES,
    InvalidConversionTypeError,
    ReferralError,
    ReferralExpiredError,
    ReferralNotFoundError,
    SelfReferralError,
    convert_referral,
    create_referral,
    get_referral_analytics,
    get_referral_metrics,
    get_referrer_leaderboard,
    validate_conversion_type,
)


def _make_referral(**overrides):
    """Create a mock Referral object with sensible defaults."""
    now = datetime.now(UTC)
    defaults = {
        "id": uuid4(),
        "referrer_user_id": uuid4(),
        "referred_user_id": None,
        "conversion_type": None,
        "conversion_entity_id": None,
        "landing_path": "/animals/123",
        "ip_address": "192.168.1.1",
        "converted_at": None,
        "expires_at": now + timedelta(days=REFERRAL_EXPIRY_DAYS),
        "created_at": now,
    }
    defaults.update(overrides)
    mock = MagicMock()
    for key, value in defaults.items():
        setattr(mock, key, value)
    return mock


class TestErrorClasses:
    """Tests for referral error hierarchy."""

    def test_referral_error_base(self) -> None:
        err = ReferralError("test error", details="some detail")
        assert str(err) == "test error"
        assert err.message == "test error"
        assert err.details == "some detail"

    def test_referral_not_found_error(self) -> None:
        err = ReferralNotFoundError("abc-123")
        assert err.message == "Referral not found"
        assert "abc-123" in err.details

    def test_invalid_conversion_type_error(self) -> None:
        err = InvalidConversionTypeError("bad_type")
        assert err.message == "Invalid conversion type"
        assert err.details is not None

    def test_referral_expired_error(self) -> None:
        err = ReferralExpiredError("ref-456")
        assert err.message == "Referral expired"
        assert "ref-456" in err.details
        assert str(REFERRAL_EXPIRY_DAYS) in err.details

    def test_self_referral_error(self) -> None:
        err = SelfReferralError()
        assert err.message == "Self-referral not allowed"
        assert err.details is not None


class TestValidateConversionType:
    """Tests for conversion type validation."""

    def test_valid_types_accepted(self) -> None:
        for ct in VALID_CONVERSION_TYPES:
            validate_conversion_type(ct)

    def test_invalid_type_raises(self) -> None:
        with pytest.raises(InvalidConversionTypeError):
            validate_conversion_type("invalid_type")

    def test_empty_string_raises(self) -> None:
        with pytest.raises(InvalidConversionTypeError):
            validate_conversion_type("")


class TestCreateReferral:
    """Tests for create_referral."""

    @pytest.mark.asyncio
    async def test_creates_referral_with_expiry(self) -> None:
        db = AsyncMock()
        referrer_id = uuid4()
        referral = await create_referral(
            referrer_user_id=referrer_id,
            landing_path="/animals/42",
            ip_address="10.0.0.1",
            db=db,
        )
        assert referral.referrer_user_id == referrer_id
        assert referral.landing_path == "/animals/42"
        assert referral.ip_address == "10.0.0.1"
        assert referral.expires_at is not None
        assert referral.converted_at is None
        db.add.assert_called_once()
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_creates_referral_without_optional_fields(self) -> None:
        db = AsyncMock()
        referrer_id = uuid4()
        referral = await create_referral(referrer_user_id=referrer_id, db=db)
        assert referral.referrer_user_id == referrer_id
        assert referral.landing_path is None
        assert referral.ip_address is None

    @pytest.mark.asyncio
    async def test_expiry_is_30_days_from_now(self) -> None:
        db = AsyncMock()
        before = datetime.now(UTC)
        referral = await create_referral(referrer_user_id=uuid4(), db=db)
        after = datetime.now(UTC)
        expected_min = before + timedelta(days=REFERRAL_EXPIRY_DAYS)
        expected_max = after + timedelta(days=REFERRAL_EXPIRY_DAYS)
        assert expected_min <= referral.expires_at <= expected_max


class TestConvertReferral:
    """Tests for convert_referral."""

    @pytest.mark.asyncio
    async def test_converts_referral_successfully(self) -> None:
        referral = _make_referral()
        referred_id = uuid4()
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = referral
        db.execute.return_value = mock_result
        result = await convert_referral(
            referral_id=referral.id,
            referred_user_id=referred_id,
            conversion_type="donation",
            conversion_entity_id=uuid4(),
            db=db,
        )
        assert result.referred_user_id == referred_id
        assert result.conversion_type == "donation"
        assert result.converted_at is not None
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_raises_not_found_for_missing_referral(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result
        with pytest.raises(ReferralNotFoundError):
            await convert_referral(
                referral_id=uuid4(),
                referred_user_id=uuid4(),
                conversion_type="donation",
                db=db,
            )

    @pytest.mark.asyncio
    async def test_raises_expired_for_old_referral(self) -> None:
        referral = _make_referral(expires_at=datetime.now(UTC) - timedelta(days=1))
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = referral
        db.execute.return_value = mock_result
        with pytest.raises(ReferralExpiredError):
            await convert_referral(
                referral_id=referral.id,
                referred_user_id=uuid4(),
                conversion_type="donation",
                db=db,
            )

    @pytest.mark.asyncio
    async def test_raises_self_referral_error(self) -> None:
        user_id = uuid4()
        referral = _make_referral(referrer_user_id=user_id)
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = referral
        db.execute.return_value = mock_result
        with pytest.raises(SelfReferralError):
            await convert_referral(
                referral_id=referral.id,
                referred_user_id=user_id,
                conversion_type="donation",
                db=db,
            )

    @pytest.mark.asyncio
    async def test_raises_invalid_conversion_type(self) -> None:
        db = AsyncMock()
        with pytest.raises(InvalidConversionTypeError):
            await convert_referral(
                referral_id=uuid4(),
                referred_user_id=uuid4(),
                conversion_type="invalid",
                db=db,
            )

    @pytest.mark.asyncio
    async def test_converts_with_all_valid_types(self) -> None:
        for ct in VALID_CONVERSION_TYPES:
            referral = _make_referral()
            db = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = referral
            db.execute.return_value = mock_result
            result = await convert_referral(
                referral_id=referral.id,
                referred_user_id=uuid4(),
                conversion_type=ct,
                db=db,
            )
            assert result.conversion_type == ct


class TestGetReferralMetrics:
    """Tests for get_referral_metrics."""

    @pytest.mark.asyncio
    async def test_returns_metrics_dict(self) -> None:
        db = AsyncMock()
        total_result = MagicMock()
        total_result.scalar_one.return_value = 100
        referrers_result = MagicMock()
        referrers_result.scalar_one.return_value = 25
        conversions_result = MagicMock()
        conversions_result.all.return_value = [("donation", 10), ("registration", 5)]
        db.execute.side_effect = [total_result, referrers_result, conversions_result]
        metrics = await get_referral_metrics(db, days=30)
        assert metrics["total_referrals"] == 100
        assert metrics["total_referrers"] == 25
        assert metrics["total_conversions"] == 15
        assert metrics["conversions_by_type"] == {"donation": 10, "registration": 5}
        assert metrics["conversion_rate_pct"] == 15.0
        assert metrics["period_days"] == 30

    @pytest.mark.asyncio
    async def test_returns_zero_rate_when_no_referrals(self) -> None:
        db = AsyncMock()
        total_result = MagicMock()
        total_result.scalar_one.return_value = 0
        referrers_result = MagicMock()
        referrers_result.scalar_one.return_value = 0
        conversions_result = MagicMock()
        conversions_result.all.return_value = []
        db.execute.side_effect = [total_result, referrers_result, conversions_result]
        metrics = await get_referral_metrics(db, days=30)
        assert metrics["total_referrals"] == 0
        assert metrics["conversion_rate_pct"] == 0.0

    @pytest.mark.asyncio
    async def test_custom_days_parameter(self) -> None:
        db = AsyncMock()
        total_result = MagicMock()
        total_result.scalar_one.return_value = 50
        referrers_result = MagicMock()
        referrers_result.scalar_one.return_value = 10
        conversions_result = MagicMock()
        conversions_result.all.return_value = []
        db.execute.side_effect = [total_result, referrers_result, conversions_result]
        metrics = await get_referral_metrics(db, days=7)
        assert metrics["period_days"] == 7


class TestGetReferrerLeaderboard:
    """Tests for get_referrer_leaderboard."""

    @pytest.mark.asyncio
    async def test_returns_leaderboard_entries(self) -> None:
        user1 = uuid4()
        user2 = uuid4()
        db = AsyncMock()
        main_result = MagicMock()
        main_result.all.return_value = [(user1, 10, 5), (user2, 8, 3)]
        breakdown1 = MagicMock()
        breakdown1.all.return_value = [("donation", 3), ("registration", 2)]
        breakdown2 = MagicMock()
        breakdown2.all.return_value = [("adoption_application", 3)]
        db.execute.side_effect = [main_result, breakdown1, breakdown2]
        leaderboard = await get_referrer_leaderboard(db, days=30, limit=10)
        assert len(leaderboard) == 2
        assert leaderboard[0]["referrer_user_id"] == str(user1)
        assert leaderboard[0]["total_referrals"] == 10
        assert leaderboard[0]["total_conversions"] == 5
        assert leaderboard[0]["conversions_by_type"] == {"donation": 3, "registration": 2}
        assert leaderboard[1]["referrer_user_id"] == str(user2)

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_referrers(self) -> None:
        db = AsyncMock()
        main_result = MagicMock()
        main_result.all.return_value = []
        db.execute.return_value = main_result
        leaderboard = await get_referrer_leaderboard(db, days=30, limit=10)
        assert leaderboard == []


class TestGetReferralAnalytics:
    """Tests for get_referral_analytics."""

    @pytest.mark.asyncio
    async def test_returns_daily_data(self) -> None:
        db = AsyncMock()
        day1 = datetime(2026, 3, 1, tzinfo=UTC)
        day2 = datetime(2026, 3, 2, tzinfo=UTC)
        result = MagicMock()
        result.all.return_value = [(day1, 5, 2), (day2, 8, 3)]
        db.execute.return_value = result
        analytics = await get_referral_analytics(db, days=30)
        assert len(analytics["daily_data"]) == 2
        assert analytics["daily_data"][0]["date"] == "2026-03-01"
        assert analytics["daily_data"][0]["referrals"] == 5
        assert analytics["daily_data"][0]["conversions"] == 2
        assert analytics["period_days"] == 30

    @pytest.mark.asyncio
    async def test_returns_empty_data_for_no_activity(self) -> None:
        db = AsyncMock()
        result = MagicMock()
        result.all.return_value = []
        db.execute.return_value = result
        analytics = await get_referral_analytics(db, days=7)
        assert analytics["daily_data"] == []
        assert analytics["period_days"] == 7
