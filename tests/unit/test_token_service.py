"""Unit tests for the token service (generation, hashing, expiry logic)."""

import hashlib
from datetime import UTC, datetime, timedelta

from src.auth.token_service import (
    EMAIL_VERIFY_EXPIRY_HOURS,
    PASSWORD_RESET_EXPIRY_HOURS,
    TOKEN_BYTES,
    _expiry_for,
    generate_token,
    hash_token,
)
from src.db.models.verification_token import TokenType


class TestGenerateToken:
    """Tests for generate_token()."""

    def test_returns_non_empty_string(self) -> None:
        token = generate_token()
        assert isinstance(token, str)
        assert len(token) > 0

    def test_returns_url_safe_characters(self) -> None:
        token = generate_token()
        # URL-safe base64 uses only these characters
        allowed = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_=")
        assert all(c in allowed for c in token)

    def test_generates_unique_tokens(self) -> None:
        tokens = {generate_token() for _ in range(100)}
        assert len(tokens) == 100

    def test_token_has_sufficient_entropy(self) -> None:
        """Token must be at least TOKEN_BYTES * 4/3 characters (base64 encoding)."""
        token = generate_token()
        # URL-safe base64 of 32 bytes = 43 characters
        min_length = int(TOKEN_BYTES * 4 / 3) - 1
        assert len(token) >= min_length


class TestHashToken:
    """Tests for hash_token()."""

    def test_returns_sha256_hex_digest(self) -> None:
        token = "test-token-value"
        result = hash_token(token)
        expected = hashlib.sha256(token.encode("utf-8")).hexdigest()
        assert result == expected

    def test_hash_is_64_characters(self) -> None:
        result = hash_token("any-value")
        assert len(result) == 64

    def test_same_input_produces_same_hash(self) -> None:
        token = generate_token()
        assert hash_token(token) == hash_token(token)

    def test_different_inputs_produce_different_hashes(self) -> None:
        token_a = generate_token()
        token_b = generate_token()
        assert hash_token(token_a) != hash_token(token_b)


class TestExpiryFor:
    """Tests for _expiry_for()."""

    def test_email_verify_expiry_is_24_hours(self) -> None:
        before = datetime.now(UTC)
        expiry = _expiry_for(TokenType.EMAIL_VERIFY)
        after = datetime.now(UTC)

        expected_min = before + timedelta(hours=EMAIL_VERIFY_EXPIRY_HOURS)
        expected_max = after + timedelta(hours=EMAIL_VERIFY_EXPIRY_HOURS)
        assert expected_min <= expiry <= expected_max

    def test_password_reset_expiry_is_1_hour(self) -> None:
        before = datetime.now(UTC)
        expiry = _expiry_for(TokenType.PASSWORD_RESET)
        after = datetime.now(UTC)

        expected_min = before + timedelta(hours=PASSWORD_RESET_EXPIRY_HOURS)
        expected_max = after + timedelta(hours=PASSWORD_RESET_EXPIRY_HOURS)
        assert expected_min <= expiry <= expected_max

    def test_expiry_has_utc_timezone(self) -> None:
        expiry = _expiry_for(TokenType.EMAIL_VERIFY)
        assert expiry.tzinfo is not None
