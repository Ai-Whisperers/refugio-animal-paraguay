"""Authentication utilities: password hashing and JWT token creation/decoding.

Key rotation support
--------------------
To rotate the JWT signing secret without invalidating in-flight tokens:

1. Generate a new strong secret (≥64 random chars recommended):
       python3 -c "import secrets; print(secrets.token_hex(32))"

2. Update environment variables on the server:
       SECRET_KEY_PREVIOUS=<old SECRET_KEY value>
       SECRET_KEY=<new value>

3. Restart the application.  New tokens are signed with the new key.
   Existing tokens signed with the previous key are still accepted.

4. Wait for access_token_expire_minutes (default: 30 min) to ensure
   all in-flight tokens expire.

5. Clear SECRET_KEY_PREVIOUS (set to empty string or unset the variable).
   Restart the application.  Rotation complete.
"""

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
    jti: str | None = None,
) -> str:
    """Encode *data* as a signed JWT with an expiry claim.

    If *jti* is provided, it is included as the JWT ID claim
    for session tracking and revocation support.

    Always uses the current active *secret_key* — never the previous key.
    """
    payload = data.copy()
    payload["exp"] = datetime.now(UTC) + expires_delta
    if jti:
        payload["jti"] = jti
    return jwt.encode(payload, secret_key, algorithm=algorithm)


def decode_access_token(
    token: str,
    secret_key: str,
    algorithm: str,
    secret_key_previous: str = "",
) -> dict[str, object]:
    """Decode and verify *token*.  Raises JWTError on any failure.

    Key rotation support: if *secret_key_previous* is provided, the token
    is first verified against *secret_key*.  On failure, it is retried with
    *secret_key_previous* to allow zero-downtime key rotation.

    Args:
        token: Encoded JWT string.
        secret_key: Active signing secret.
        algorithm: JWT algorithm (e.g. ``"HS256"``).
        secret_key_previous: Previous signing secret, set during rotation.
            Leave empty when no rotation is in progress.

    Returns:
        Decoded JWT payload as a dict.

    Raises:
        JWTError: If the token is invalid, expired, or signed by neither key.
    """
    try:
        return jwt.decode(token, secret_key, algorithms=[algorithm])
    except JWTError:
        # Current key failed.  Attempt previous key if one is configured.
        if secret_key_previous:
            # Raises JWTError if the previous key also fails — caller handles it.
            return jwt.decode(token, secret_key_previous, algorithms=[algorithm])
        raise


__all__ = [
    "JWTError",
    "create_access_token",
    "decode_access_token",
    "hash_password",
    "verify_password",
]
