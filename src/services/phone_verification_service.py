"""Phone verification service: OTP generation, hashing, rate limiting, verification.

Generates cryptographically random 6-digit OTPs, stores bcrypt hashes in the
database, and sends the plaintext code via WhatsApp. Rate limits OTP sends
(3 per phone per hour) and verification attempts (5 per OTP record).
"""

import logging
import secrets
from datetime import UTC, datetime, timedelta

import bcrypt
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import Settings
from src.db.models.phone_verification_otp import PhoneVerificationOTP
from src.db.models.user import User
from src.notifications.whatsapp_service import WhatsAppMessage, WhatsAppService

logger = logging.getLogger(__name__)

OTP_LENGTH = 6
OTP_EXPIRY_MINUTES = 5
MAX_SEND_PER_HOUR = 3
MAX_VERIFY_ATTEMPTS = 5
BCRYPT_COST_FACTOR = 12

WHATSAPP_OTP_TEMPLATE = (
    "Your Refugio verification code is: {otp}. "
    "Valid for 5 minutes. Do not share this code."
)


class PhoneVerificationError(Exception):
    """Base error for phone verification operations."""

    def __init__(self, message: str, error_code: str = "verification_error") -> None:
        self.message = message
        self.error_code = error_code
        super().__init__(message)


class OTPRateLimitError(PhoneVerificationError):
    """Raised when OTP send rate limit is exceeded."""

    def __init__(self, retry_after_seconds: int = 3600) -> None:
        self.retry_after_seconds = retry_after_seconds
        super().__init__(
            "Too many OTP requests. Please try again later.",
            error_code="rate_limit_exceeded",
        )


class OTPExpiredError(PhoneVerificationError):
    """Raised when OTP has expired."""

    def __init__(self) -> None:
        super().__init__(
            "OTP has expired. Request a new code.",
            error_code="otp_expired",
        )


class OTPInvalidError(PhoneVerificationError):
    """Raised when OTP code is incorrect."""

    def __init__(self) -> None:
        super().__init__("Invalid OTP", error_code="otp_invalid")


class OTPMaxAttemptsError(PhoneVerificationError):
    """Raised when max verification attempts are exhausted."""

    def __init__(self) -> None:
        super().__init__(
            "Too many attempts, please request a new code",
            error_code="max_attempts_exceeded",
        )


def generate_otp() -> str:
    """Generate a cryptographically random 6-digit OTP string."""
    return "".join(secrets.choice("0123456789") for _ in range(OTP_LENGTH))


def hash_otp(otp: str) -> str:
    """Hash an OTP using bcrypt with the configured cost factor."""
    return bcrypt.hashpw(
        otp.encode("utf-8"),
        bcrypt.gensalt(rounds=BCRYPT_COST_FACTOR),
    ).decode("utf-8")


def verify_otp_hash(otp: str, otp_hash: str) -> bool:
    """Verify an OTP against its bcrypt hash using constant-time comparison."""
    try:
        return bcrypt.checkpw(otp.encode("utf-8"), otp_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False


async def check_send_rate_limit(db: AsyncSession, phone: str) -> None:
    """Check if the phone number has exceeded the OTP send rate limit.

    Raises OTPRateLimitError if more than MAX_SEND_PER_HOUR OTPs were sent
    to this phone in the last hour.
    """
    one_hour_ago = datetime.now(UTC) - timedelta(hours=1)
    result = await db.execute(
        select(func.count())
        .select_from(PhoneVerificationOTP)
        .where(
            and_(
                PhoneVerificationOTP.phone == phone,
                PhoneVerificationOTP.created_at >= one_hour_ago,
            )
        )
    )
    count = result.scalar_one()
    if count >= MAX_SEND_PER_HOUR:
        raise OTPRateLimitError()


async def invalidate_previous_otps(db: AsyncSession, phone: str) -> None:
    """Mark all unverified OTPs for this phone as expired (set expires_at to now).

    New OTPs invalidate previous ones per the acceptance criteria.
    """
    now = datetime.now(UTC)
    result = await db.execute(
        select(PhoneVerificationOTP).where(
            and_(
                PhoneVerificationOTP.phone == phone,
                PhoneVerificationOTP.verified_at.is_(None),
                PhoneVerificationOTP.expires_at > now,
            )
        )
    )
    for otp_record in result.scalars().all():
        otp_record.expires_at = now


async def send_otp(
    db: AsyncSession,
    phone: str,
    user_id: str | None,
    settings: Settings,
) -> PhoneVerificationOTP:
    """Generate, store, and send a new OTP via WhatsApp.

    Returns the created PhoneVerificationOTP record (without the plaintext OTP).
    Raises OTPRateLimitError if rate limit is exceeded.
    """
    await check_send_rate_limit(db, phone)
    await invalidate_previous_otps(db, phone)

    otp_code = generate_otp()
    otp_hashed = hash_otp(otp_code)
    now = datetime.now(UTC)
    expires_at = now + timedelta(minutes=OTP_EXPIRY_MINUTES)

    otp_record = PhoneVerificationOTP(
        phone=phone,
        user_id=user_id,
        otp_hash=otp_hashed,
        expires_at=expires_at,
    )
    db.add(otp_record)
    await db.flush()
    await db.refresh(otp_record)

    # Send OTP via WhatsApp
    whatsapp = WhatsAppService(settings)
    message = WhatsAppMessage(
        to=phone,
        body=WHATSAPP_OTP_TEMPLATE.format(otp=otp_code),
    )
    sent = await whatsapp.send_message(message)
    if not sent:
        logger.error("Failed to send OTP WhatsApp message to %s", phone)

    return otp_record


async def verify_otp(
    db: AsyncSession,
    phone: str,
    otp_code: str,
) -> PhoneVerificationOTP:
    """Verify an OTP code for a phone number.

    Returns the verified OTP record on success.
    Raises OTPExpiredError, OTPInvalidError, or OTPMaxAttemptsError on failure.
    """
    now = datetime.now(UTC)

    # Find the most recent unverified OTP for this phone
    result = await db.execute(
        select(PhoneVerificationOTP)
        .where(
            and_(
                PhoneVerificationOTP.phone == phone,
                PhoneVerificationOTP.verified_at.is_(None),
            )
        )
        .order_by(PhoneVerificationOTP.created_at.desc())
        .limit(1)
    )
    otp_record = result.scalar_one_or_none()

    if otp_record is None:
        raise OTPInvalidError()

    # Check if expired
    if otp_record.expires_at < now:
        raise OTPExpiredError()

    # Check attempt count
    if otp_record.attempted_count >= MAX_VERIFY_ATTEMPTS:
        raise OTPMaxAttemptsError()

    # Increment attempt count before verifying
    otp_record.attempted_count += 1

    # Verify the OTP hash
    if not verify_otp_hash(otp_code, otp_record.otp_hash):
        await db.flush()
        # Check if this was the 5th attempt
        if otp_record.attempted_count >= MAX_VERIFY_ATTEMPTS:
            raise OTPMaxAttemptsError()
        raise OTPInvalidError()

    # OTP is valid — mark as verified
    otp_record.verified_at = now
    await db.flush()
    return otp_record


async def mark_phone_verified(db: AsyncSession, user_id: str, phone: str) -> None:
    """Update the user record to mark the phone as verified."""
    now = datetime.now(UTC)
    user = await db.get(User, user_id)
    if user is not None:
        user.phone_verified = True
        user.phone_verified_at = now
        await db.flush()


async def get_verification_status(db: AsyncSession, phone: str) -> dict:
    """Check if a phone number has been verified.

    Returns {"verified": bool, "verified_at": datetime | None}.
    """
    result = await db.execute(
        select(PhoneVerificationOTP)
        .where(
            and_(
                PhoneVerificationOTP.phone == phone,
                PhoneVerificationOTP.verified_at.is_not(None),
            )
        )
        .order_by(PhoneVerificationOTP.verified_at.desc())
        .limit(1)
    )
    otp_record = result.scalar_one_or_none()
    if otp_record is not None:
        return {"verified": True, "verified_at": otp_record.verified_at}
    return {"verified": False, "verified_at": None}
