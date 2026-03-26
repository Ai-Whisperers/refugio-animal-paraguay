"""Unit tests for src/auth/utils.py — password hashing and JWT helpers."""

from datetime import timedelta

import pytest
from jose import JWTError

from src.auth.utils import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)

_SECRET = "test-secret-key-for-unit-tests"
_ALGORITHM = "HS256"


# ---------------------------------------------------------------------------
# hash_password / verify_password
# ---------------------------------------------------------------------------


def test_hash_password_returns_non_empty_string() -> None:
    result = hash_password("somepassword")
    assert isinstance(result, str)
    assert len(result) > 0


def test_hash_password_produces_bcrypt_hash() -> None:
    # bcrypt hashes always start with $2b$ (or $2a$)
    result = hash_password("somepassword")
    assert result.startswith("$2")


def test_hash_password_is_not_plaintext() -> None:
    plain = "supersecret"
    assert hash_password(plain) != plain


def test_hash_password_different_calls_produce_different_hashes() -> None:
    # bcrypt uses a random salt — two hashes of the same password differ
    h1 = hash_password("same")
    h2 = hash_password("same")
    assert h1 != h2


def test_verify_password_correct_password_returns_true() -> None:
    hashed = hash_password("correct")
    assert verify_password("correct", hashed) is True


def test_verify_password_wrong_password_returns_false() -> None:
    hashed = hash_password("correct")
    assert verify_password("wrong", hashed) is False


def test_verify_password_empty_string_does_not_match() -> None:
    hashed = hash_password("notempty")
    assert verify_password("", hashed) is False


# ---------------------------------------------------------------------------
# create_access_token / decode_access_token
# ---------------------------------------------------------------------------


def test_create_access_token_returns_string() -> None:
    token = create_access_token(
        data={"sub": "user-id-123"},
        secret_key=_SECRET,
        algorithm=_ALGORITHM,
        expires_delta=timedelta(minutes=30),
    )
    assert isinstance(token, str)
    assert len(token) > 0


def test_decode_access_token_returns_sub_claim() -> None:
    token = create_access_token(
        data={"sub": "00000000-0000-0000-0000-000000000001"},
        secret_key=_SECRET,
        algorithm=_ALGORITHM,
        expires_delta=timedelta(minutes=30),
    )
    payload = decode_access_token(token, _SECRET, _ALGORITHM)
    assert payload["sub"] == "00000000-0000-0000-0000-000000000001"


def test_decode_access_token_preserves_custom_claims() -> None:
    token = create_access_token(
        data={"sub": "user-1", "role": "staff"},
        secret_key=_SECRET,
        algorithm=_ALGORITHM,
        expires_delta=timedelta(minutes=5),
    )
    payload = decode_access_token(token, _SECRET, _ALGORITHM)
    assert payload["role"] == "staff"


def test_decode_access_token_includes_exp_claim() -> None:
    token = create_access_token(
        data={"sub": "user-1"},
        secret_key=_SECRET,
        algorithm=_ALGORITHM,
        expires_delta=timedelta(minutes=30),
    )
    payload = decode_access_token(token, _SECRET, _ALGORITHM)
    assert "exp" in payload


def test_decode_access_token_wrong_secret_raises_jwterror() -> None:
    token = create_access_token(
        data={"sub": "user-1"},
        secret_key=_SECRET,
        algorithm=_ALGORITHM,
        expires_delta=timedelta(minutes=30),
    )
    with pytest.raises(JWTError):
        decode_access_token(token, "wrong-secret", _ALGORITHM)


def test_decode_access_token_expired_token_raises_jwterror() -> None:
    token = create_access_token(
        data={"sub": "user-1"},
        secret_key=_SECRET,
        algorithm=_ALGORITHM,
        expires_delta=timedelta(seconds=-1),  # already expired
    )
    with pytest.raises(JWTError):
        decode_access_token(token, _SECRET, _ALGORITHM)


def test_decode_access_token_tampered_token_raises_jwterror() -> None:
    token = create_access_token(
        data={"sub": "user-1"},
        secret_key=_SECRET,
        algorithm=_ALGORITHM,
        expires_delta=timedelta(minutes=30),
    )
    tampered = token[:-5] + "XXXXX"
    with pytest.raises(JWTError):
        decode_access_token(tampered, _SECRET, _ALGORITHM)
