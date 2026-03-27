"""Unit tests for the phone verification OTP service."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from src.services.phone_verification_service import (
    MAX_SEND_PER_HOUR,
    MAX_VERIFY_ATTEMPTS,
    OTP_LENGTH,
    OTPExpiredError,
    OTPInvalidError,
    OTPMaxAttemptsError,
    OTPRateLimitError,
    check_send_rate_limit,
    generate_otp,
    hash_otp,
    invalidate_previous_otps,
    send_otp,
    verify_otp,
    verify_otp_hash,
)


class TestGenerateOTP:
    """Tests for OTP generation."""

    def test_generates_six_digit_string(self) -> None:
        otp = generate_otp()
        assert len(otp) == OTP_LENGTH
        assert otp.isdigit()

    def test_generates_unique_values(self) -> None:
        otps = {generate_otp() for _ in range(50)}
        # With 6 digits, 50 samples should almost certainly be unique
        assert len(otps) > 40

    def test_otp_is_zero_padded(self) -> None:
        """OTP can start with zeros (e.g. '000123')."""
        # Generate many OTPs — at least one should demonstrate leading zeros are preserved
        otps = [generate_otp() for _ in range(1000)]
        assert all(len(otp) == OTP_LENGTH for otp in otps)


class TestHashAndVerifyOTP:
    """Tests for OTP hashing and verification."""

    def test_hash_returns_bcrypt_string(self) -> None:
        otp_hash = hash_otp("123456")
        assert otp_hash.startswith("$2")
        assert len(otp_hash) == 60

    def test_verify_correct_otp(self) -> None:
        otp = "654321"
        otp_hash = hash_otp(otp)
        assert verify_otp_hash(otp, otp_hash) is True

    def test_verify_incorrect_otp(self) -> None:
        otp_hash = hash_otp("123456")
        assert verify_otp_hash("654321", otp_hash) is False

    def test_verify_with_invalid_hash(self) -> None:
        assert verify_otp_hash("123456", "not-a-hash") is False

    def test_verify_with_empty_inputs(self) -> None:
        assert verify_otp_hash("", "") is False

    def test_otp_never_stored_in_plaintext(self) -> None:
        """The hash must not contain the original OTP."""
        otp = "987654"
        otp_hash = hash_otp(otp)
        assert otp not in otp_hash


class TestCheckSendRateLimit:
    """Tests for the OTP send rate limiter."""

    @pytest.mark.asyncio()
    async def test_allows_under_limit(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = MAX_SEND_PER_HOUR - 1
        db.execute.return_value = mock_result

        # Should not raise
        await check_send_rate_limit(db, "+595981234567")

    @pytest.mark.asyncio()
    async def test_raises_when_limit_exceeded(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = MAX_SEND_PER_HOUR
        db.execute.return_value = mock_result

        with pytest.raises(OTPRateLimitError):
            await check_send_rate_limit(db, "+595981234567")

    @pytest.mark.asyncio()
    async def test_rate_limit_error_has_retry_after(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = MAX_SEND_PER_HOUR
        db.execute.return_value = mock_result

        with pytest.raises(OTPRateLimitError) as exc_info:
            await check_send_rate_limit(db, "+595981234567")
        assert exc_info.value.retry_after_seconds == 3600


class TestInvalidatePreviousOTPs:
    """Tests for invalidating previous OTPs."""

    @pytest.mark.asyncio()
    async def test_sets_expires_at_to_now_for_active_otps(self) -> None:
        db = AsyncMock()
        active_otp = MagicMock()
        active_otp.verified_at = None
        active_otp.expires_at = datetime.now(UTC) + timedelta(minutes=5)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [active_otp]
        db.execute.return_value = mock_result

        await invalidate_previous_otps(db, "+595981234567")
        # expires_at should now be in the past
        assert active_otp.expires_at <= datetime.now(UTC)


class TestSendOTP:
    """Tests for the send_otp function."""

    @pytest.mark.asyncio()
    @patch("src.services.phone_verification_service.WhatsAppService")
    @patch("src.services.phone_verification_service.invalidate_previous_otps")
    @patch("src.services.phone_verification_service.check_send_rate_limit")
    async def test_creates_otp_record_and_sends_whatsapp(
        self, mock_rate_limit, mock_invalidate, mock_whatsapp_cls
    ) -> None:
        db = AsyncMock()
        db.add = MagicMock()
        db.flush = AsyncMock()
        db.refresh = AsyncMock()

        mock_whatsapp = MagicMock()
        mock_whatsapp.send_message = AsyncMock(return_value=True)
        mock_whatsapp_cls.return_value = mock_whatsapp

        settings = MagicMock()
        user_id = str(uuid4())

        await send_otp(db, "+595981234567", user_id, settings)

        assert db.add.called
        otp_record = db.add.call_args[0][0]
        assert otp_record.phone == "+595981234567"
        assert otp_record.user_id == user_id
        assert otp_record.otp_hash  # Must have a hash
        assert otp_record.expires_at > datetime.now(UTC)
        mock_whatsapp.send_message.assert_called_once()

        # Verify WhatsApp message contains OTP format text
        msg = mock_whatsapp.send_message.call_args[0][0]
        assert "verification code" in msg.body.lower()
        assert msg.to == "+595981234567"

    @pytest.mark.asyncio()
    @patch("src.services.phone_verification_service.check_send_rate_limit")
    async def test_raises_rate_limit_error(self, mock_rate_limit) -> None:
        mock_rate_limit.side_effect = OTPRateLimitError()
        db = AsyncMock()
        settings = MagicMock()

        with pytest.raises(OTPRateLimitError):
            await send_otp(db, "+595981234567", None, settings)


class TestVerifyOTP:
    """Tests for the verify_otp function."""

    def _make_otp_record(
        self,
        otp_hash: str = "",
        expires_at: datetime | None = None,
        attempted_count: int = 0,
        verified_at: datetime | None = None,
    ) -> MagicMock:
        record = MagicMock()
        record.otp_hash = otp_hash or hash_otp("123456")
        record.expires_at = expires_at or (datetime.now(UTC) + timedelta(minutes=5))
        record.attempted_count = attempted_count
        record.verified_at = verified_at
        return record

    @pytest.mark.asyncio()
    async def test_verifies_correct_otp(self) -> None:
        otp = "123456"
        otp_hash = hash_otp(otp)
        record = self._make_otp_record(otp_hash=otp_hash)

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = record
        db.execute.return_value = mock_result

        result = await verify_otp(db, "+595981234567", otp)
        assert result.verified_at is not None

    @pytest.mark.asyncio()
    async def test_raises_invalid_for_wrong_otp(self) -> None:
        record = self._make_otp_record(otp_hash=hash_otp("123456"))

        db = AsyncMock()
        db.flush = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = record
        db.execute.return_value = mock_result

        with pytest.raises(OTPInvalidError):
            await verify_otp(db, "+595981234567", "999999")

    @pytest.mark.asyncio()
    async def test_raises_expired_for_old_otp(self) -> None:
        record = self._make_otp_record(
            expires_at=datetime.now(UTC) - timedelta(minutes=1)
        )

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = record
        db.execute.return_value = mock_result

        with pytest.raises(OTPExpiredError):
            await verify_otp(db, "+595981234567", "123456")

    @pytest.mark.asyncio()
    async def test_raises_max_attempts_when_exhausted(self) -> None:
        record = self._make_otp_record(attempted_count=MAX_VERIFY_ATTEMPTS)

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = record
        db.execute.return_value = mock_result

        with pytest.raises(OTPMaxAttemptsError):
            await verify_otp(db, "+595981234567", "123456")

    @pytest.mark.asyncio()
    async def test_increments_attempt_count_on_failure(self) -> None:
        record = self._make_otp_record(otp_hash=hash_otp("123456"))
        record.attempted_count = 0

        db = AsyncMock()
        db.flush = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = record
        db.execute.return_value = mock_result

        with pytest.raises(OTPInvalidError):
            await verify_otp(db, "+595981234567", "999999")
        assert record.attempted_count == 1

    @pytest.mark.asyncio()
    async def test_raises_invalid_when_no_otp_found(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        with pytest.raises(OTPInvalidError):
            await verify_otp(db, "+595981234567", "123456")

    @pytest.mark.asyncio()
    async def test_fifth_failed_attempt_raises_max_attempts(self) -> None:
        """On the 5th wrong attempt, should raise OTPMaxAttemptsError."""
        record = self._make_otp_record(
            otp_hash=hash_otp("123456"),
            attempted_count=MAX_VERIFY_ATTEMPTS - 1,
        )

        db = AsyncMock()
        db.flush = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = record
        db.execute.return_value = mock_result

        with pytest.raises(OTPMaxAttemptsError):
            await verify_otp(db, "+595981234567", "999999")


class TestExceptionCodes:
    """Tests for error code attributes."""

    def test_rate_limit_error_code(self) -> None:
        err = OTPRateLimitError()
        assert err.error_code == "rate_limit_exceeded"

    def test_expired_error_code(self) -> None:
        err = OTPExpiredError()
        assert err.error_code == "otp_expired"

    def test_invalid_error_code(self) -> None:
        err = OTPInvalidError()
        assert err.error_code == "otp_invalid"

    def test_max_attempts_error_code(self) -> None:
        err = OTPMaxAttemptsError()
        assert err.error_code == "max_attempts_exceeded"
