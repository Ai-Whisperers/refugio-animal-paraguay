"""Unit tests for the Google OAuth service."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from src.schemas.oauth import OAuthUserInfo
from src.services.google_oauth_service import (
    GoogleOAuthError,
    build_authorization_url,
    exchange_code_for_tokens,
    fetch_google_user_info,
    generate_oauth_state,
)

# --- generate_oauth_state ---


def test_generate_oauth_state_returns_string() -> None:
    state = generate_oauth_state()
    assert isinstance(state, str)
    assert len(state) > 20


def test_generate_oauth_state_is_unique() -> None:
    states = {generate_oauth_state() for _ in range(100)}
    assert len(states) == 100


# --- build_authorization_url ---


def test_build_authorization_url_contains_required_params() -> None:
    url = build_authorization_url(
        client_id="test-client-id",
        redirect_uri="http://localhost:3000/auth/google/callback",
        state="test-state-123",
    )

    assert "https://accounts.google.com/o/oauth2/v2/auth" in url
    assert "client_id=test-client-id" in url
    assert "state=test-state-123" in url
    assert "response_type=code" in url
    assert "scope=" in url
    assert "redirect_uri=" in url


def test_build_authorization_url_includes_openid_scope() -> None:
    url = build_authorization_url(
        client_id="test",
        redirect_uri="http://localhost/callback",
        state="s",
    )
    assert "openid" in url
    assert "email" in url
    assert "profile" in url


# --- exchange_code_for_tokens ---


@pytest.mark.asyncio
async def test_exchange_code_success() -> None:
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "access_token": "ya29.test-token",
        "id_token": "eyJ.test.id-token",
        "token_type": "Bearer",
    }

    mock_client_instance = AsyncMock()
    mock_client_instance.post.return_value = mock_response
    mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client_instance.__aexit__ = AsyncMock(return_value=False)

    with patch(
        "src.services.google_oauth_service.httpx.AsyncClient", return_value=mock_client_instance
    ):
        result = await exchange_code_for_tokens(
            code="auth-code-123",
            client_id="client-id",
            client_secret="client-secret",
            redirect_uri="http://localhost/callback",
        )

    assert result["access_token"] == "ya29.test-token"
    mock_client_instance.post.assert_called_once()


@pytest.mark.asyncio
async def test_exchange_code_failure_raises_error() -> None:
    mock_response = AsyncMock()
    mock_response.status_code = 400
    mock_response.text = '{"error": "invalid_grant"}'

    mock_client_instance = AsyncMock()
    mock_client_instance.post.return_value = mock_response
    mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client_instance.__aexit__ = AsyncMock(return_value=False)

    with (
        patch(
            "src.services.google_oauth_service.httpx.AsyncClient", return_value=mock_client_instance
        ),
        pytest.raises(GoogleOAuthError, match="Failed to exchange"),
    ):
        await exchange_code_for_tokens(
            code="bad-code",
            client_id="client-id",
            client_secret="client-secret",
            redirect_uri="http://localhost/callback",
        )


# --- fetch_google_user_info ---


@pytest.mark.asyncio
async def test_fetch_user_info_success() -> None:
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "id": "google-user-123",
        "email": "user@gmail.com",
        "name": "Test User",
        "picture": "https://lh3.googleusercontent.com/photo.jpg",
        "verified_email": True,
    }

    mock_client_instance = AsyncMock()
    mock_client_instance.get.return_value = mock_response
    mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client_instance.__aexit__ = AsyncMock(return_value=False)

    with patch(
        "src.services.google_oauth_service.httpx.AsyncClient", return_value=mock_client_instance
    ):
        result = await fetch_google_user_info("ya29.test-token")

    assert isinstance(result, OAuthUserInfo)
    assert result.google_id == "google-user-123"
    assert result.email == "user@gmail.com"
    assert result.full_name == "Test User"
    assert result.picture_url == "https://lh3.googleusercontent.com/photo.jpg"
    assert result.email_verified is True


@pytest.mark.asyncio
async def test_fetch_user_info_failure_raises_error() -> None:
    mock_response = AsyncMock()
    mock_response.status_code = 401

    mock_client_instance = AsyncMock()
    mock_client_instance.get.return_value = mock_response
    mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client_instance.__aexit__ = AsyncMock(return_value=False)

    with (
        patch(
            "src.services.google_oauth_service.httpx.AsyncClient", return_value=mock_client_instance
        ),
        pytest.raises(GoogleOAuthError, match="Failed to fetch"),
    ):
        await fetch_google_user_info("bad-token")


@pytest.mark.asyncio
async def test_fetch_user_info_without_optional_fields() -> None:
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "id": "google-user-456",
        "email": "minimal@gmail.com",
        "verified_email": False,
    }

    mock_client_instance = AsyncMock()
    mock_client_instance.get.return_value = mock_response
    mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client_instance.__aexit__ = AsyncMock(return_value=False)

    with patch(
        "src.services.google_oauth_service.httpx.AsyncClient", return_value=mock_client_instance
    ):
        result = await fetch_google_user_info("ya29.test-token")

    assert result.google_id == "google-user-456"
    assert result.full_name is None
    assert result.picture_url is None
    assert result.email_verified is False
