"""Email backend for authentication flows.

This module provides a pluggable email sending interface. The current
implementation logs emails to the console/logger — actual SMTP delivery
is deferred to V2 (Email Notification System, EPIC-6 S01).

The console backend is suitable for development and testing: token URLs
are printed to stdout so developers can complete verification/reset flows.
"""

import logging

logger = logging.getLogger(__name__)

# Base URL for verification/reset links — overridden in production
FRONTEND_BASE_URL = "http://localhost:3000"


def send_verification_email(email: str, token: str) -> None:
    """Send an email verification link to the user.

    In development, logs the verification URL to the console.
    """
    url = f"{FRONTEND_BASE_URL}/verify-email?token={token}"
    logger.info(
        "EMAIL VERIFICATION for %s — click: %s",
        email,
        url,
    )
    # Print to stdout for easy access during development
    print(  # noqa: T201
        f"\n{'=' * 60}\n"
        f"  EMAIL VERIFICATION\n"
        f"  To: {email}\n"
        f"  Link: {url}\n"
        f"{'=' * 60}\n"
    )


def send_password_reset_email(email: str, token: str) -> None:
    """Send a password reset link to the user.

    In development, logs the reset URL to the console.
    """
    url = f"{FRONTEND_BASE_URL}/reset-password?token={token}"
    logger.info(
        "PASSWORD RESET for %s — click: %s",
        email,
        url,
    )
    print(  # noqa: T201
        f"\n{'=' * 60}\n"
        f"  PASSWORD RESET\n"
        f"  To: {email}\n"
        f"  Link: {url}\n"
        f"{'=' * 60}\n"
    )
