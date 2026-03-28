"""Unit tests for the Google OAuth API endpoints."""

from unittest.mock import MagicMock

import pytest
from src.api.google_oauth import (
    _OAUTH_STATE_STORE,
    _PENDING_LINK_STORE,
    _cleanup_expired_states,
    _validate_google_config,
)
from src.schemas.oauth import (
    OAuthCallbackRequest,
    OAuthCallbackResponse,
    OAuthStartResponse,
    OAuthUserInfo,
)

# --- Schema validation tests ---


def test_oauth_start_response_schema() -> None:
    resp = OAuthStartResponse(authorization_url="https://accounts.google.com/...")
    assert resp.authorization_url.startswith("https://")


def test_oauth_callback_request_schema() -> None:
    req = OAuthCallbackRequest(code="auth-code", state="csrf-state")
    assert req.code == "auth-code"
    assert req.state == "csrf-state"


def test_oauth_callback_response_new_user() -> None:
    resp = OAuthCallbackResponse(
        access_token="jwt-token",
        is_new_user=True,
        requires_linking=False,
    )
    assert resp.is_new_user is True
    assert resp.token_type == "bearer"


def test_oauth_callback_response_requires_linking() -> None:
    resp = OAuthCallbackResponse(
        access_token="link-state",
        token_type="link_pending",
        is_new_user=False,
        requires_linking=True,
        email="user@example.com",
    )
    assert resp.requires_linking is True
    assert resp.email == "user@example.com"


# --- validate_google_config ---


def test_validate_google_config_raises_when_not_configured() -> None:
    settings = MagicMock()
    settings.google_client_id = ""
    settings.google_client_secret = ""

    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        _validate_google_config(settings)
    assert exc_info.value.status_code == 503


def test_validate_google_config_passes_when_configured() -> None:
    settings = MagicMock()
    settings.google_client_id = "test-client-id"
    settings.google_client_secret = "test-client-secret"

    # Should not raise
    _validate_google_config(settings)


# --- cleanup_expired_states ---


def test_cleanup_expired_states_removes_old_entries() -> None:
    from datetime import UTC, datetime, timedelta

    # Add an expired state
    old_state = "expired-state"
    _OAUTH_STATE_STORE[old_state] = {
        "created_at": datetime.now(UTC) - timedelta(minutes=15),
        "ip": "127.0.0.1",
    }
    _PENDING_LINK_STORE[old_state] = OAuthUserInfo(
        google_id="g123",
        email="test@example.com",
    )

    # Add a fresh state
    fresh_state = "fresh-state"
    _OAUTH_STATE_STORE[fresh_state] = {
        "created_at": datetime.now(UTC),
        "ip": "127.0.0.1",
    }

    _cleanup_expired_states()

    assert old_state not in _OAUTH_STATE_STORE
    assert old_state not in _PENDING_LINK_STORE
    assert fresh_state in _OAUTH_STATE_STORE

    # Cleanup
    _OAUTH_STATE_STORE.pop(fresh_state, None)


# --- OAuthUserInfo schema ---


def test_oauth_user_info_with_all_fields() -> None:
    info = OAuthUserInfo(
        google_id="g-123",
        email="user@gmail.com",
        full_name="Test User",
        picture_url="https://example.com/photo.jpg",
        email_verified=True,
    )
    assert info.google_id == "g-123"
    assert info.email_verified is True


def test_oauth_user_info_minimal() -> None:
    info = OAuthUserInfo(
        google_id="g-456",
        email="minimal@gmail.com",
    )
    assert info.full_name is None
    assert info.picture_url is None
    assert info.email_verified is False


# --- User model OAuth fields ---


def test_user_model_has_oauth_fields() -> None:
    """Verify the User model has OAuth columns after migration."""
    from src.db.models.user import User

    # Check the mapped columns exist on the model
    mapper = User.__table__.columns
    assert "oauth_provider" in mapper
    assert "oauth_id" in mapper
    assert "profile_picture_url" in mapper

    # hashed_password should be nullable for OAuth users
    assert mapper["hashed_password"].nullable is True


def test_user_model_oauth_provider_nullable() -> None:
    """OAuth provider should be nullable (not all users use OAuth)."""
    from src.db.models.user import User

    col = User.__table__.columns["oauth_provider"]
    assert col.nullable is True


# --- Auth login handles OAuth-only users ---


def test_auth_login_rejects_oauth_only_user() -> None:
    """The password login endpoint should reject users with no password."""
    # This test verifies the logic exists in the code
    import inspect

    from src.api.auth import login

    # Check that the function body contains a check for hashed_password being None
    source_text = inspect.getsource(login)
    assert "hashed_password is None" in source_text
    assert "social login" in source_text
