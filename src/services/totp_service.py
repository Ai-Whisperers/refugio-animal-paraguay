"""TOTP 2FA service: secret generation, provisioning URI, and code verification.

Implements RFC 6238 TOTP (Time-based One-Time Password) via pyotp.
All functions are pure (no database access) so they compose cleanly with
the router and are trivially unit-testable.

Constants:
  TOTP_ISSUER        — Label shown in authenticator apps (e.g. Google Authenticator)
  TOTP_DIGITS        — Code length (6, standard)
  TOTP_INTERVAL      — Time window in seconds (30, standard)
  TOTP_VALID_WINDOW  — Number of adjacent windows to accept (helps with clock skew)
"""

import pyotp

TOTP_ISSUER = "Refugio Animal Paraguay"
TOTP_DIGITS = 6
TOTP_INTERVAL = 30
TOTP_VALID_WINDOW = 1  # accept ±1 window to tolerate moderate clock skew


def generate_secret() -> str:
    """Return a new random base32-encoded TOTP secret (32 chars = 160 bits).

    The secret is safe to store directly in the database.
    """
    return pyotp.random_base32()


def get_provisioning_uri(secret: str, account_name: str) -> str:
    """Return an otpauth:// URI for the given secret and account.

    This URI can be encoded into a QR code by the frontend and scanned
    by any TOTP-compatible authenticator app (Google Authenticator, Authy, etc.).

    Args:
        secret:       Base32-encoded TOTP secret.
        account_name: Usually the user's email address — shown in the app.
    """
    totp = pyotp.TOTP(secret, digits=TOTP_DIGITS, interval=TOTP_INTERVAL)
    return totp.provisioning_uri(name=account_name, issuer_name=TOTP_ISSUER)


def verify_totp(secret: str, code: str) -> bool:
    """Return True if *code* is a valid TOTP token for *secret*.

    Accepts codes from the current window and TOTP_VALID_WINDOW adjacent
    windows on either side to tolerate minor clock drift between the server
    and the user's device.

    Args:
        secret: Base32-encoded TOTP secret stored for the user.
        code:   6-digit code submitted by the user (may contain spaces/dashes
                — those are stripped before verification).
    """
    # Strip formatting characters that some authenticator apps include
    clean_code = code.replace(" ", "").replace("-", "")
    totp = pyotp.TOTP(secret, digits=TOTP_DIGITS, interval=TOTP_INTERVAL)
    return totp.verify(clean_code, valid_window=TOTP_VALID_WINDOW)


__all__ = [
    "TOTP_DIGITS",
    "TOTP_INTERVAL",
    "TOTP_ISSUER",
    "TOTP_VALID_WINDOW",
    "generate_secret",
    "get_provisioning_uri",
    "verify_totp",
]
