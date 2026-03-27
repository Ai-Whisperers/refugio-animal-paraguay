"""Integration tests for phone verification API endpoints."""

import uuid
from datetime import timedelta
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from src.app import app
from src.auth.utils import create_access_token, hash_password
from src.config import Settings
from src.db.session import init_engine
from src.services.phone_verification_service import hash_otp

_PHONE_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000601")
_PHONE_USER_EMAIL = "phone-test@refugio.test"
_PHONE_USER_PHONE = "+595981111111"


@pytest_asyncio.fixture
async def phone_client():
    """Authenticated client for phone verification tests."""
    settings = Settings()
    engine = init_engine(settings)
    session_factory = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )

    # Upsert test user with a phone number
    async with session_factory() as session:
        await session.execute(
            text("""
                INSERT INTO users (id, email, hashed_password, role, is_active, phone)
                VALUES (:id, :email, :pwd, 'adopter', true, :phone)
                ON CONFLICT (email) DO UPDATE SET
                    phone = :phone,
                    role = 'adopter',
                    phone_verified = false,
                    phone_verified_at = NULL
            """),
            {
                "id": str(_PHONE_USER_ID),
                "email": _PHONE_USER_EMAIL,
                "pwd": hash_password("TestPass123!"),
                "phone": _PHONE_USER_PHONE,
            },
        )
        await session.commit()

    token = create_access_token(
        data={"sub": str(_PHONE_USER_ID)},
        secret_key=settings.secret_key,
        algorithm=settings.algorithm,
        expires_delta=timedelta(minutes=30),
    )

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"Authorization": f"Bearer {token}"},
    ) as ac:
        yield ac

    # Cleanup
    async with session_factory() as session:
        await session.execute(
            text("DELETE FROM phone_verification_otps WHERE phone = :phone"),
            {"phone": _PHONE_USER_PHONE},
        )
        await session.execute(
            text("DELETE FROM users WHERE id = :id"),
            {"id": str(_PHONE_USER_ID)},
        )
        await session.commit()


@pytest.mark.integration()
class TestSendOTP:
    """Tests for POST /auth/verify-phone/send-otp."""

    @pytest.mark.asyncio()
    @patch("src.services.phone_verification_service.WhatsAppService")
    async def test_sends_otp_successfully(self, mock_wa_cls, phone_client) -> None:
        mock_wa = mock_wa_cls.return_value
        mock_wa.send_message = AsyncMock(return_value=True)

        response = await phone_client.post(
            "/auth/verify-phone/send-otp",
            json={"phone": _PHONE_USER_PHONE},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "OTP sent via WhatsApp"
        assert data["expires_in_seconds"] == 300
        mock_wa.send_message.assert_called_once()

    @pytest.mark.asyncio()
    async def test_rejects_invalid_phone_format(self, phone_client) -> None:
        response = await phone_client.post(
            "/auth/verify-phone/send-otp",
            json={"phone": "1234567890"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio()
    @patch("src.services.phone_verification_service.WhatsAppService")
    async def test_rate_limits_after_3_sends(self, mock_wa_cls, phone_client) -> None:
        mock_wa = mock_wa_cls.return_value
        mock_wa.send_message = AsyncMock(return_value=True)

        # Send 3 OTPs (should succeed)
        for _ in range(3):
            response = await phone_client.post(
                "/auth/verify-phone/send-otp",
                json={"phone": _PHONE_USER_PHONE},
            )
            assert response.status_code == 200

        # 4th should fail with 429
        response = await phone_client.post(
            "/auth/verify-phone/send-otp",
            json={"phone": _PHONE_USER_PHONE},
        )
        assert response.status_code == 429


@pytest.mark.integration()
class TestVerifyOTP:
    """Tests for POST /auth/verify-phone/verify-otp."""

    @pytest.mark.asyncio()
    @patch("src.services.phone_verification_service.WhatsAppService")
    async def test_verify_with_correct_otp(self, mock_wa_cls, phone_client) -> None:
        mock_wa = mock_wa_cls.return_value
        mock_wa.send_message = AsyncMock(return_value=True)

        # Capture the OTP that will be sent
        sent_otp = None

        original_send = mock_wa.send_message

        async def capture_otp(message):
            nonlocal sent_otp
            # Extract 6-digit code from message body
            import re
            match = re.search(r"\b(\d{6})\b", message.body)
            if match:
                sent_otp = match.group(1)
            return await original_send(message)

        mock_wa.send_message = capture_otp

        # Send OTP
        response = await phone_client.post(
            "/auth/verify-phone/send-otp",
            json={"phone": _PHONE_USER_PHONE},
        )
        assert response.status_code == 200
        assert sent_otp is not None

        # Verify OTP
        response = await phone_client.post(
            "/auth/verify-phone/verify-otp",
            json={"phone": _PHONE_USER_PHONE, "otp_code": sent_otp},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Phone number verified"
        assert data["phone"] == _PHONE_USER_PHONE
        assert "verified_at" in data

    @pytest.mark.asyncio()
    @patch("src.services.phone_verification_service.WhatsAppService")
    async def test_verify_with_incorrect_otp(self, mock_wa_cls, phone_client) -> None:
        mock_wa = mock_wa_cls.return_value
        mock_wa.send_message = AsyncMock(return_value=True)

        # Send OTP first
        await phone_client.post(
            "/auth/verify-phone/send-otp",
            json={"phone": _PHONE_USER_PHONE},
        )

        # Try with wrong code
        response = await phone_client.post(
            "/auth/verify-phone/verify-otp",
            json={"phone": _PHONE_USER_PHONE, "otp_code": "000000"},
        )
        assert response.status_code == 400

    @pytest.mark.asyncio()
    @patch("src.services.phone_verification_service.WhatsAppService")
    async def test_locks_after_5_failed_attempts(self, mock_wa_cls, phone_client) -> None:
        mock_wa = mock_wa_cls.return_value
        mock_wa.send_message = AsyncMock(return_value=True)

        # Send OTP
        await phone_client.post(
            "/auth/verify-phone/send-otp",
            json={"phone": _PHONE_USER_PHONE},
        )

        # 5 wrong attempts
        for i in range(5):
            response = await phone_client.post(
                "/auth/verify-phone/verify-otp",
                json={"phone": _PHONE_USER_PHONE, "otp_code": f"00000{i}"},
            )
            # Last attempt(s) should return 429
            if i >= 4:
                assert response.status_code == 429

    @pytest.mark.asyncio()
    async def test_expired_otp_returns_400(self, phone_client) -> None:
        """Expired OTPs return 400 with otp_expired error code."""
        settings = Settings()
        engine = init_engine(settings)
        session_factory = async_sessionmaker(
            bind=engine, class_=AsyncSession, expire_on_commit=False
        )

        # Insert an already-expired OTP directly
        async with session_factory() as session:
            await session.execute(
                text("""
                    INSERT INTO phone_verification_otps
                        (id, user_id, phone, otp_hash, expires_at, created_at)
                    VALUES
                        (:id, :user_id, :phone, :otp_hash,
                         NOW() - INTERVAL '10 minutes',
                         NOW() - INTERVAL '15 minutes')
                """),
                {
                    "id": str(uuid.uuid4()),
                    "user_id": str(_PHONE_USER_ID),
                    "phone": _PHONE_USER_PHONE,
                    "otp_hash": hash_otp("123456"),
                },
            )
            await session.commit()

        response = await phone_client.post(
            "/auth/verify-phone/verify-otp",
            json={"phone": _PHONE_USER_PHONE, "otp_code": "123456"},
        )
        assert response.status_code == 400
        data = response.json()
        assert data.get("error_code") == "otp_expired"


@pytest.mark.integration()
class TestPhoneVerificationStatus:
    """Tests for GET /auth/verify-phone/status."""

    @pytest.mark.asyncio()
    async def test_returns_unverified_status(self, phone_client) -> None:
        response = await phone_client.get(
            "/auth/verify-phone/status",
            params={"phone": _PHONE_USER_PHONE},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["verified"] is False
        assert data["verified_at"] is None

    @pytest.mark.asyncio()
    async def test_rejects_invalid_phone_format(self, phone_client) -> None:
        response = await phone_client.get(
            "/auth/verify-phone/status",
            params={"phone": "invalid"},
        )
        assert response.status_code == 422
