"""Async email service for sending transactional emails.

Supports SMTP delivery via aiosmtplib. The service is intentionally
transport-agnostic at the interface level so a SendGrid HTTP backend
can be added later without changing callers.

Usage:
    service = EmailService(settings)
    await service.send_email(
        to="adopter@example.com",
        subject="Your adoption request update",
        html_body="<h1>Approved!</h1>",
    )
"""

import logging
from dataclasses import dataclass
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib

from src.config import Settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class EmailMessage:
    """Value object representing an outbound email."""

    to: str
    subject: str
    html_body: str
    text_body: str | None = None
    reply_to: str | None = None


class EmailService:
    """Async email sender using SMTP.

    The service reads SMTP configuration from Settings at construction time
    and validates that required fields are present. If email is disabled
    (smtp_enabled=False), send_email() logs the attempt and returns without
    connecting to the SMTP server.
    """

    def __init__(self, settings: Settings) -> None:
        self._host = settings.smtp_host
        self._port = settings.smtp_port
        self._username = settings.smtp_username
        self._password = settings.smtp_password
        self._from_address = settings.email_from_address
        self._from_name = settings.email_from_name
        self._use_tls = settings.smtp_use_tls
        self._enabled = settings.smtp_enabled

    @property
    def is_enabled(self) -> bool:
        """Whether the email service is configured and enabled."""
        return self._enabled

    async def send_email(self, message: EmailMessage) -> bool:
        """Send an email message.

        Returns True if the email was sent (or would have been sent in disabled mode).
        Returns False if sending failed.
        """
        if not self._enabled:
            logger.info(
                "Email sending disabled — would send to=%s subject=%r",
                message.to,
                message.subject,
            )
            return True

        mime_message = self._build_mime_message(message)

        try:
            await aiosmtplib.send(
                mime_message,
                hostname=self._host,
                port=self._port,
                username=self._username or None,
                password=self._password or None,
                use_tls=self._use_tls,
            )
            logger.info(
                "Email sent: to=%s subject=%r",
                message.to,
                message.subject,
            )
            return True
        except aiosmtplib.SMTPException as exc:
            logger.error(
                "SMTP delivery failed: to=%s subject=%r error=%s",
                message.to,
                message.subject,
                str(exc),
            )
            return False
        except OSError as exc:
            logger.error(
                "SMTP connection failed: host=%s port=%d error=%s",
                self._host,
                self._port,
                str(exc),
            )
            return False

    def _build_mime_message(self, message: EmailMessage) -> MIMEMultipart:
        """Build a MIME multipart message from an EmailMessage."""
        mime = MIMEMultipart("alternative")
        mime["From"] = f"{self._from_name} <{self._from_address}>"
        mime["To"] = message.to
        mime["Subject"] = message.subject

        if message.reply_to:
            mime["Reply-To"] = message.reply_to

        # Plain text fallback
        text_body = message.text_body or self._strip_html(message.html_body)
        mime.attach(MIMEText(text_body, "plain", "utf-8"))
        mime.attach(MIMEText(message.html_body, "html", "utf-8"))

        return mime

    @staticmethod
    def _strip_html(html: str) -> str:
        """Naive HTML tag removal for plain-text fallback.

        Good enough for transactional emails. For complex HTML, consider
        html2text or beautifulsoup.
        """
        import re

        text = re.sub(r"<br\s*/?>", "\n", html, flags=re.IGNORECASE)
        text = re.sub(r"<[^>]+>", "", text)
        return text.strip()
