"""Unit tests for the EmailService.

Tests cover:
  - Disabled mode (logs but does not connect)
  - MIME message construction
  - HTML stripping for plain-text fallback
  - Error handling for SMTP failures
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from src.notifications.service import EmailMessage, EmailService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _make_settings(**overrides: object) -> MagicMock:
    """Build a mock Settings object with email defaults."""
    defaults = {
        "smtp_enabled": True,
        "smtp_host": "smtp.example.com",
        "smtp_port": 587,
        "smtp_username": "user",
        "smtp_password": "pass",
        "smtp_use_tls": True,
        "email_from_address": "noreply@refugio.test",
        "email_from_name": "Refugio Test",
    }
    defaults.update(overrides)
    mock = MagicMock()
    for key, value in defaults.items():
        setattr(mock, key, value)
    return mock


def _make_message(**overrides: object) -> EmailMessage:
    """Build an EmailMessage with sensible defaults."""
    defaults = {
        "to": "adopter@example.com",
        "subject": "Test Subject",
        "html_body": "<h1>Hello</h1><p>World</p>",
    }
    defaults.update(overrides)
    return EmailMessage(**defaults)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
class TestEmailServiceDisabledMode:
    """When smtp_enabled is False, emails should be logged but not sent."""

    def test_is_enabled_returns_false(self) -> None:
        settings = _make_settings(smtp_enabled=False)
        service = EmailService(settings)
        assert service.is_enabled is False

    @pytest.mark.asyncio
    async def test_send_email_returns_true_without_smtp(self) -> None:
        settings = _make_settings(smtp_enabled=False)
        service = EmailService(settings)
        result = await service.send_email(_make_message())
        assert result is True

    @pytest.mark.asyncio
    async def test_send_email_does_not_call_smtp(self) -> None:
        settings = _make_settings(smtp_enabled=False)
        service = EmailService(settings)
        with patch("src.notifications.service.aiosmtplib.send", new_callable=AsyncMock) as mock:
            await service.send_email(_make_message())
            mock.assert_not_called()


class TestEmailServiceEnabledMode:
    """When smtp_enabled is True, emails are sent via SMTP."""

    @pytest.mark.asyncio
    async def test_send_email_calls_smtp_send(self) -> None:
        settings = _make_settings()
        service = EmailService(settings)
        with patch("src.notifications.service.aiosmtplib.send", new_callable=AsyncMock) as mock:
            result = await service.send_email(_make_message())
            assert result is True
            mock.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_email_passes_correct_smtp_params(self) -> None:
        settings = _make_settings(smtp_host="mail.test", smtp_port=465, smtp_use_tls=False)
        service = EmailService(settings)
        with patch("src.notifications.service.aiosmtplib.send", new_callable=AsyncMock) as mock:
            await service.send_email(_make_message())
            call_kwargs = mock.call_args
            assert call_kwargs.kwargs["hostname"] == "mail.test"
            assert call_kwargs.kwargs["port"] == 465
            assert call_kwargs.kwargs["use_tls"] is False

    @pytest.mark.asyncio
    async def test_smtp_exception_returns_false(self) -> None:
        import aiosmtplib

        settings = _make_settings()
        service = EmailService(settings)
        with patch(
            "src.notifications.service.aiosmtplib.send",
            new_callable=AsyncMock,
            side_effect=aiosmtplib.SMTPException("Connection refused"),
        ):
            result = await service.send_email(_make_message())
            assert result is False

    @pytest.mark.asyncio
    async def test_os_error_returns_false(self) -> None:
        settings = _make_settings()
        service = EmailService(settings)
        with patch(
            "src.notifications.service.aiosmtplib.send",
            new_callable=AsyncMock,
            side_effect=OSError("Network unreachable"),
        ):
            result = await service.send_email(_make_message())
            assert result is False


class TestMimeMessageConstruction:
    """Verify the MIME message is built correctly."""

    def test_from_header_includes_name_and_address(self) -> None:
        settings = _make_settings(
            email_from_name="Test Shelter",
            email_from_address="shelter@test.org",
        )
        service = EmailService(settings)
        msg = _make_message()
        mime = service._build_mime_message(msg)
        assert mime["From"] == "Test Shelter <shelter@test.org>"

    def test_to_header_matches_recipient(self) -> None:
        settings = _make_settings()
        service = EmailService(settings)
        msg = _make_message(to="recipient@example.com")
        mime = service._build_mime_message(msg)
        assert mime["To"] == "recipient@example.com"

    def test_subject_header_matches(self) -> None:
        settings = _make_settings()
        service = EmailService(settings)
        msg = _make_message(subject="Important Update")
        mime = service._build_mime_message(msg)
        assert mime["Subject"] == "Important Update"

    def test_reply_to_header_set_when_provided(self) -> None:
        settings = _make_settings()
        service = EmailService(settings)
        msg = _make_message(reply_to="reply@test.org")
        mime = service._build_mime_message(msg)
        assert mime["Reply-To"] == "reply@test.org"

    def test_reply_to_absent_when_not_provided(self) -> None:
        settings = _make_settings()
        service = EmailService(settings)
        msg = _make_message()
        mime = service._build_mime_message(msg)
        assert mime["Reply-To"] is None

    def test_mime_has_two_parts(self) -> None:
        settings = _make_settings()
        service = EmailService(settings)
        msg = _make_message()
        mime = service._build_mime_message(msg)
        payloads = mime.get_payload()
        assert len(payloads) == 2
        assert payloads[0].get_content_type() == "text/plain"
        assert payloads[1].get_content_type() == "text/html"


class TestHtmlStripping:
    """Test the naive HTML → plain text conversion."""

    def test_removes_tags(self) -> None:
        assert EmailService._strip_html("<h1>Title</h1>") == "Title"

    def test_converts_br_to_newline(self) -> None:
        result = EmailService._strip_html("Line 1<br>Line 2<br/>Line 3")
        assert result == "Line 1\nLine 2\nLine 3"

    def test_handles_empty_string(self) -> None:
        assert EmailService._strip_html("") == ""

    def test_preserves_plain_text(self) -> None:
        assert EmailService._strip_html("No HTML here") == "No HTML here"
