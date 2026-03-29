"""Unit tests for JWT key rotation support.

Tests that:
  - decode_access_token verifies against the active key
  - decode_access_token falls back to the previous key during rotation
  - Tokens signed with neither key raise JWTError
  - Settings validates secret_key_previous length when set
  - Admin endpoint returns correct rotation status
"""

from datetime import timedelta
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from jose import JWTError
from src.auth.utils import create_access_token, decode_access_token

ACTIVE_KEY = "active-key-for-tests-must-be-at-least-32-chars-long"
PREVIOUS_KEY = "previous-key-for-tests-must-be-at-least-32-chars"
UNRELATED_KEY = "unrelated-key-that-never-signed-any-token-in-tests"
ALGORITHM = "HS256"
DELTA = timedelta(minutes=5)
PAYLOAD = {"sub": "user-123"}


# --- decode_access_token ---


class TestDecodeAccessTokenRotation:
    def test_decodes_token_signed_with_active_key(self) -> None:
        token = create_access_token(PAYLOAD, ACTIVE_KEY, ALGORITHM, DELTA)
        result = decode_access_token(token, ACTIVE_KEY, ALGORITHM)
        assert result["sub"] == "user-123"

    def test_decodes_token_signed_with_previous_key_during_rotation(self) -> None:
        # Token was issued before rotation (signed with the old key).
        old_token = create_access_token(PAYLOAD, PREVIOUS_KEY, ALGORITHM, DELTA)

        # After rotation, active key is new; previous key is the old one.
        result = decode_access_token(
            old_token, ACTIVE_KEY, ALGORITHM, secret_key_previous=PREVIOUS_KEY
        )
        assert result["sub"] == "user-123"

    def test_raises_jwt_error_when_no_previous_key_and_active_key_wrong(self) -> None:
        token = create_access_token(PAYLOAD, PREVIOUS_KEY, ALGORITHM, DELTA)
        with pytest.raises(JWTError):
            # No previous key configured — only active key tried.
            decode_access_token(token, ACTIVE_KEY, ALGORITHM)

    def test_raises_jwt_error_when_both_keys_wrong(self) -> None:
        token = create_access_token(PAYLOAD, UNRELATED_KEY, ALGORITHM, DELTA)
        with pytest.raises(JWTError):
            decode_access_token(token, ACTIVE_KEY, ALGORITHM, secret_key_previous=PREVIOUS_KEY)

    def test_raises_jwt_error_for_malformed_token(self) -> None:
        with pytest.raises(JWTError):
            decode_access_token("not.a.valid.token", ACTIVE_KEY, ALGORITHM)

    def test_raises_jwt_error_for_malformed_token_with_previous_key(self) -> None:
        with pytest.raises(JWTError):
            decode_access_token(
                "not.a.valid.token",
                ACTIVE_KEY,
                ALGORITHM,
                secret_key_previous=PREVIOUS_KEY,
            )

    def test_empty_previous_key_does_not_attempt_fallback(self) -> None:
        token = create_access_token(PAYLOAD, PREVIOUS_KEY, ALGORITHM, DELTA)
        with pytest.raises(JWTError):
            decode_access_token(token, ACTIVE_KEY, ALGORITHM, secret_key_previous="")

    def test_new_tokens_still_verify_with_active_key_during_rotation(self) -> None:
        # After rotation, new tokens are signed with active key.
        new_token = create_access_token(PAYLOAD, ACTIVE_KEY, ALGORITHM, DELTA)
        result = decode_access_token(
            new_token, ACTIVE_KEY, ALGORITHM, secret_key_previous=PREVIOUS_KEY
        )
        assert result["sub"] == "user-123"


# --- Settings validation ---


class TestSecretKeyPreviousValidation:
    def test_accepts_empty_previous_key(self) -> None:
        from src.config import Settings

        s = Settings(
            secret_key="a" * 32,
            secret_key_previous="",
            database_url="postgresql+asyncpg://u:p@localhost:5432/db",
        )
        assert s.secret_key_previous == ""

    def test_accepts_valid_previous_key(self) -> None:
        from src.config import Settings

        s = Settings(
            secret_key="a" * 32,
            secret_key_previous="b" * 32,
            database_url="postgresql+asyncpg://u:p@localhost:5432/db",
        )
        assert s.secret_key_previous == "b" * 32

    def test_rejects_short_previous_key(self) -> None:
        from pydantic import ValidationError
        from src.config import Settings

        with pytest.raises(ValidationError):
            Settings(
                secret_key="a" * 32,
                secret_key_previous="too-short",
                database_url="postgresql+asyncpg://u:p@localhost:5432/db",
            )


# --- Admin endpoint ---


def _make_admin_app(secret_key: str, secret_key_previous: str) -> FastAPI:
    """Build a minimal FastAPI app with the admin_security router."""
    from src.api.admin_security import router as sec_router
    from src.auth.dependencies import require_admin
    from src.config import Settings

    test_settings = Settings(
        secret_key=secret_key,
        secret_key_previous=secret_key_previous,
        database_url="postgresql+asyncpg://u:p@localhost:5432/db",
        app_env="development",
    )

    fake_admin = MagicMock()

    app = FastAPI()
    app.include_router(sec_router)
    app.dependency_overrides[require_admin] = lambda: fake_admin
    app.dependency_overrides[Settings] = lambda: test_settings

    from src.config import get_settings

    app.dependency_overrides[get_settings] = lambda: test_settings

    return app


class TestAdminJwtRotationStatusEndpoint:
    def test_rotation_inactive_when_no_previous_key(self) -> None:
        client = TestClient(_make_admin_app(ACTIVE_KEY, ""))
        response = client.get("/admin/security/jwt-rotation-status")
        assert response.status_code == 200
        data = response.json()
        assert data["rotation_active"] is False
        assert data["previous_key_configured"] is False
        assert data["previous_key_prefix"] == ""

    def test_rotation_active_when_previous_key_set(self) -> None:
        client = TestClient(_make_admin_app(ACTIVE_KEY, PREVIOUS_KEY))
        response = client.get("/admin/security/jwt-rotation-status")
        assert response.status_code == 200
        data = response.json()
        assert data["rotation_active"] is True
        assert data["previous_key_configured"] is True
        assert data["previous_key_prefix"] != ""

    def test_active_key_prefix_is_masked(self) -> None:
        client = TestClient(_make_admin_app(ACTIVE_KEY, ""))
        response = client.get("/admin/security/jwt-rotation-status")
        data = response.json()
        # Should show first 8 chars + "..."
        assert data["active_key_prefix"] == ACTIVE_KEY[:8] + "..."
        # Full key must not appear in response
        assert ACTIVE_KEY not in response.text

    def test_previous_key_prefix_is_masked(self) -> None:
        client = TestClient(_make_admin_app(ACTIVE_KEY, PREVIOUS_KEY))
        response = client.get("/admin/security/jwt-rotation-status")
        data = response.json()
        assert data["previous_key_prefix"] == PREVIOUS_KEY[:8] + "..."
        assert PREVIOUS_KEY not in response.text

    def test_recommendation_guides_rotation_when_active(self) -> None:
        client = TestClient(_make_admin_app(ACTIVE_KEY, PREVIOUS_KEY))
        response = client.get("/admin/security/jwt-rotation-status")
        data = response.json()
        assert "rotation is in progress" in data["recommendation"].lower()

    def test_recommendation_guides_how_to_start_rotation_when_inactive(self) -> None:
        client = TestClient(_make_admin_app(ACTIVE_KEY, ""))
        response = client.get("/admin/security/jwt-rotation-status")
        data = response.json()
        assert "SECRET_KEY_PREVIOUS" in data["recommendation"]

    def test_checked_at_is_present(self) -> None:
        client = TestClient(_make_admin_app(ACTIVE_KEY, ""))
        response = client.get("/admin/security/jwt-rotation-status")
        data = response.json()
        assert "checked_at" in data
        assert data["checked_at"]
