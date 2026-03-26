"""Authentication utilities: password hashing and JWT token creation/decoding."""

from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt
from passlib.context import CryptContext

_PWD_CONTEXT = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    """Return a bcrypt hash of *plain*."""
    return _PWD_CONTEXT.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if *plain* matches *hashed*."""
    return _PWD_CONTEXT.verify(plain, hashed)


def create_access_token(
    data: dict[str, object],
    secret_key: str,
    algorithm: str,
    expires_delta: timedelta,
) -> str:
    """Encode *data* as a signed JWT with an expiry claim."""
    payload = data.copy()
    payload["exp"] = datetime.now(UTC) + expires_delta
    return jwt.encode(payload, secret_key, algorithm=algorithm)


def decode_access_token(
    token: str,
    secret_key: str,
    algorithm: str,
) -> dict[str, object]:
    """Decode and verify *token*. Raises JWTError on any failure."""
    return jwt.decode(token, secret_key, algorithms=[algorithm])


__all__ = [
    "JWTError",
    "create_access_token",
    "decode_access_token",
    "hash_password",
    "verify_password",
]
