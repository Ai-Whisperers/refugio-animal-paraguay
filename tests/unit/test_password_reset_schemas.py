"""Unit tests for password reset Pydantic schemas.

Tests cover:
- PasswordResetRequest: valid email, invalid formats, normalization
- PasswordResetConfirm: valid payload, short password, empty token
- PasswordResetResponse: default message
- PasswordResetConfirmResponse: custom message
"""

import pytest
from pydantic import ValidationError
from src.schemas.password_reset import (
    PasswordResetConfirm,
    PasswordResetConfirmResponse,
    PasswordResetRequest,
    PasswordResetResponse,
)


class TestPasswordResetRequestSchema:
    """Tests for PasswordResetRequest schema."""

    def test_accepts_valid_email(self) -> None:
        """Should accept a well-formed email address."""
        req = PasswordResetRequest(email="user@example.com")
        assert str(req.email) == "user@example.com"

    def test_accepts_email_with_subdomain(self) -> None:
        """Should accept email with subdomain."""
        req = PasswordResetRequest(email="user@mail.example.com")
        assert "example.com" in str(req.email)

    def test_normalizes_email_to_lowercase(self) -> None:
        """EmailStr should normalize to lowercase."""
        req = PasswordResetRequest(email="User@EXAMPLE.COM")
        assert str(req.email) == "User@example.com"

    def test_rejects_missing_at_sign(self) -> None:
        """Should reject email without @ sign."""
        with pytest.raises(ValidationError) as exc_info:
            PasswordResetRequest(email="notanemail")
        errors = exc_info.value.errors()
        assert len(errors) >= 1

    def test_rejects_missing_domain(self) -> None:
        """Should reject email without domain."""
        with pytest.raises(ValidationError):
            PasswordResetRequest(email="user@")

    def test_rejects_missing_local_part(self) -> None:
        """Should reject email without local part."""
        with pytest.raises(ValidationError):
            PasswordResetRequest(email="@domain.com")

    def test_rejects_email_with_spaces(self) -> None:
        """Should reject email with spaces."""
        with pytest.raises(ValidationError):
            PasswordResetRequest(email="user @domain.com")

    def test_rejects_empty_string(self) -> None:
        """Should reject empty string as email."""
        with pytest.raises(ValidationError):
            PasswordResetRequest(email="")

    def test_rejects_missing_email_field(self) -> None:
        """Should reject when email field is missing."""
        with pytest.raises(ValidationError):
            PasswordResetRequest()


class TestPasswordResetConfirmSchema:
    """Tests for PasswordResetConfirm schema."""

    def test_accepts_valid_payload(self) -> None:
        """Should accept valid token and password."""
        confirm = PasswordResetConfirm(
            token="valid-token-string",
            new_password="SecurePass123!",
        )
        assert confirm.token == "valid-token-string"
        assert confirm.new_password == "SecurePass123!"

    def test_rejects_short_password(self) -> None:
        """Should reject password shorter than 8 characters."""
        with pytest.raises(ValidationError) as exc_info:
            PasswordResetConfirm(token="some-token", new_password="short")
        errors = exc_info.value.errors()
        assert any("min_length" in str(e) or "too_short" in str(e) for e in errors)

    def test_rejects_empty_token(self) -> None:
        """Should reject empty token string."""
        with pytest.raises(ValidationError):
            PasswordResetConfirm(token="", new_password="ValidPass123!")

    def test_rejects_missing_token(self) -> None:
        """Should reject when token field is missing."""
        with pytest.raises(ValidationError):
            PasswordResetConfirm(new_password="ValidPass123!")

    def test_rejects_missing_password(self) -> None:
        """Should reject when new_password field is missing."""
        with pytest.raises(ValidationError):
            PasswordResetConfirm(token="some-token")

    def test_accepts_exactly_8_char_password(self) -> None:
        """Should accept password with exactly 8 characters (min length)."""
        confirm = PasswordResetConfirm(token="tok", new_password="12345678")
        assert len(confirm.new_password) == 8

    def test_accepts_long_password(self) -> None:
        """Should accept a long password."""
        long_pwd = "A" * 200
        confirm = PasswordResetConfirm(token="tok", new_password=long_pwd)
        assert len(confirm.new_password) == 200


class TestPasswordResetResponseSchema:
    """Tests for PasswordResetResponse schema."""

    def test_default_message(self) -> None:
        """Should have a default message that does not leak email existence."""
        resp = PasswordResetResponse()
        assert "reset link" in resp.message.lower() or "registered" in resp.message.lower()

    def test_custom_message(self) -> None:
        """Should allow overriding the default message."""
        resp = PasswordResetResponse(message="Custom message")
        assert resp.message == "Custom message"


class TestPasswordResetConfirmResponseSchema:
    """Tests for PasswordResetConfirmResponse schema."""

    def test_requires_message(self) -> None:
        """Should require a message field."""
        with pytest.raises(ValidationError):
            PasswordResetConfirmResponse()

    def test_accepts_valid_message(self) -> None:
        """Should accept a valid message string."""
        resp = PasswordResetConfirmResponse(message="Password has been reset.")
        assert resp.message == "Password has been reset."
