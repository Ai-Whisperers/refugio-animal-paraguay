"""Unit tests for password reset schemas and token utilities.

Covers:
  - PasswordResetRequest schema validation
  - PasswordResetComplete schema validation (password strength)
  - PasswordResetResponse / PasswordResetCompleteResponse defaults
  - Token generation (entropy, uniqueness)
  - Token hashing (SHA-256, deterministic)
  - Constant-time comparison
"""

import pytest
from pydantic import ValidationError
from src.auth.password_reset import (
    constant_time_token_compare,
    generate_reset_token,
    hash_token,
)
from src.schemas.password_reset import (
    PasswordResetComplete,
    PasswordResetCompleteResponse,
    PasswordResetRequest,
    PasswordResetResponse,
)

# ---------------------------------------------------------------------------
# Token utilities
# ---------------------------------------------------------------------------


class TestGenerateResetToken:
    """Tests for generate_reset_token()."""

    def test_returns_nonempty_string(self) -> None:
        token = generate_reset_token()
        assert isinstance(token, str)
        assert len(token) > 0

    def test_sufficient_length(self) -> None:
        """Token must be long enough for >= 128 bits entropy."""
        token = generate_reset_token()
        # 32 bytes = 256 bits; base64url encoding ~ 43 chars
        assert len(token) >= 40

    def test_tokens_are_unique(self) -> None:
        tokens = {generate_reset_token() for _ in range(100)}
        assert len(tokens) == 100


class TestHashToken:
    """Tests for hash_token()."""

    def test_returns_64_char_hex(self) -> None:
        """SHA-256 hex digest is always 64 characters."""
        result = hash_token("test-token")
        assert len(result) == 64
        assert all(c in "0123456789abcdef" for c in result)

    def test_deterministic(self) -> None:
        assert hash_token("same-input") == hash_token("same-input")

    def test_different_inputs_different_hashes(self) -> None:
        assert hash_token("token-a") != hash_token("token-b")


class TestConstantTimeCompare:
    """Tests for constant_time_token_compare()."""

    def test_equal_strings_return_true(self) -> None:
        h = hash_token("my-token")
        assert constant_time_token_compare(h, h) is True

    def test_different_strings_return_false(self) -> None:
        a = hash_token("token-a")
        b = hash_token("token-b")
        assert constant_time_token_compare(a, b) is False


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class TestPasswordResetRequest:
    """Tests for PasswordResetRequest schema."""

    def test_valid_email(self) -> None:
        req = PasswordResetRequest(email="user@example.com")
        assert str(req.email) == "user@example.com"

    def test_invalid_email_raises(self) -> None:
        with pytest.raises(ValidationError):
            PasswordResetRequest(email="not-an-email")

    def test_email_domain_normalized_lowercase(self) -> None:
        """Pydantic EmailStr normalizes domain to lowercase."""
        req = PasswordResetRequest(email="User@Example.COM")
        # Domain is lowered; local part preserved per RFC 5321
        assert str(req.email).endswith("@example.com")


class TestPasswordResetComplete:
    """Tests for PasswordResetComplete schema."""

    def test_valid_password(self) -> None:
        obj = PasswordResetComplete(new_password="SecurePass1!")
        assert obj.new_password == "SecurePass1!"

    def test_minimum_length_8(self) -> None:
        obj = PasswordResetComplete(new_password="12345678")
        assert obj.new_password == "12345678"

    def test_too_short_raises(self) -> None:
        with pytest.raises(ValidationError):
            PasswordResetComplete(new_password="short")

    def test_empty_password_raises(self) -> None:
        with pytest.raises(ValidationError):
            PasswordResetComplete(new_password="")


class TestPasswordResetResponse:
    """Tests for PasswordResetResponse schema."""

    def test_default_message(self) -> None:
        resp = PasswordResetResponse()
        assert "password reset link" in resp.message.lower()

    def test_custom_message(self) -> None:
        resp = PasswordResetResponse(message="Custom")
        assert resp.message == "Custom"


class TestPasswordResetCompleteResponse:
    """Tests for PasswordResetCompleteResponse schema."""

    def test_default_message(self) -> None:
        resp = PasswordResetCompleteResponse()
        assert "successfully" in resp.message.lower()
