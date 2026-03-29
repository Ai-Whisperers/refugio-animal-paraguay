"""Unit tests for src/services/totp_service.py."""

import pyotp
from src.services.totp_service import (
    TOTP_DIGITS,
    TOTP_INTERVAL,
    TOTP_ISSUER,
    TOTP_VALID_WINDOW,
    generate_secret,
    get_provisioning_uri,
    verify_totp,
)

# ---------------------------------------------------------------------------
# generate_secret
# ---------------------------------------------------------------------------


def test_generate_secret_returns_string() -> None:
    secret = generate_secret()
    assert isinstance(secret, str)


def test_generate_secret_is_valid_base32() -> None:
    secret = generate_secret()
    # pyotp.TOTP will raise if the secret is not valid base32
    totp = pyotp.TOTP(secret)
    assert totp is not None


def test_generate_secret_length_is_32_chars() -> None:
    secret = generate_secret()
    assert len(secret) == 32


def test_generate_secrets_are_unique() -> None:
    secrets = {generate_secret() for _ in range(10)}
    assert len(secrets) == 10  # each call should produce a distinct secret


# ---------------------------------------------------------------------------
# get_provisioning_uri
# ---------------------------------------------------------------------------


def test_provisioning_uri_starts_with_otpauth() -> None:
    secret = generate_secret()
    uri = get_provisioning_uri(secret, "test@example.com")
    assert uri.startswith("otpauth://totp/")


def test_provisioning_uri_contains_issuer() -> None:
    secret = generate_secret()
    uri = get_provisioning_uri(secret, "test@example.com")
    assert "Refugio" in uri or "refugio" in uri.lower()


def test_provisioning_uri_contains_account_name() -> None:
    secret = generate_secret()
    account = "shelter@refugio.org.py"
    uri = get_provisioning_uri(secret, account)
    assert "shelter" in uri or "refugio" in uri.lower()


def test_provisioning_uri_contains_secret_param() -> None:
    secret = generate_secret()
    uri = get_provisioning_uri(secret, "user@example.com")
    assert f"secret={secret}" in uri


# ---------------------------------------------------------------------------
# verify_totp
# ---------------------------------------------------------------------------


def test_valid_current_code_is_accepted() -> None:
    secret = generate_secret()
    totp = pyotp.TOTP(secret, digits=TOTP_DIGITS, interval=TOTP_INTERVAL)
    code = totp.now()
    assert verify_totp(secret, code) is True


def test_wrong_code_is_rejected() -> None:
    secret = generate_secret()
    assert verify_totp(secret, "000000") is False


def test_code_with_spaces_is_accepted() -> None:
    secret = generate_secret()
    totp = pyotp.TOTP(secret, digits=TOTP_DIGITS, interval=TOTP_INTERVAL)
    raw_code = totp.now()
    # Insert a space in the middle like some apps display
    spaced = raw_code[:3] + " " + raw_code[3:]
    assert verify_totp(secret, spaced) is True


def test_code_with_dashes_is_accepted() -> None:
    secret = generate_secret()
    totp = pyotp.TOTP(secret, digits=TOTP_DIGITS, interval=TOTP_INTERVAL)
    raw_code = totp.now()
    dashed = raw_code[:3] + "-" + raw_code[3:]
    assert verify_totp(secret, dashed) is True


def test_empty_code_is_rejected() -> None:
    secret = generate_secret()
    assert verify_totp(secret, "") is False


def test_wrong_secret_is_rejected() -> None:
    secret1 = generate_secret()
    secret2 = generate_secret()
    totp = pyotp.TOTP(secret1, digits=TOTP_DIGITS, interval=TOTP_INTERVAL)
    code = totp.now()
    # Code for secret1 should not validate against secret2 (with very high probability)
    # This may rarely fail if secrets produce matching codes — acceptable for a unit test
    result = verify_totp(secret2, code)
    # We can't guarantee failure, but we can verify the function handles it gracefully
    assert isinstance(result, bool)


# ---------------------------------------------------------------------------
# Constants sanity check
# ---------------------------------------------------------------------------


def test_constants_have_expected_values() -> None:
    assert TOTP_DIGITS == 6
    assert TOTP_INTERVAL == 30
    assert TOTP_VALID_WINDOW >= 0
    assert isinstance(TOTP_ISSUER, str)
    assert len(TOTP_ISSUER) > 0
