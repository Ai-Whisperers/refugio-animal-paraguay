"""Google OAuth2 service — handles authorization URL generation, token exchange, and user info.

Uses httpx for async HTTP calls to Google's OAuth2 endpoints.
"""

import logging
import secrets
from urllib.parse import urlencode

import httpx

from src.schemas.oauth import OAuthUserInfo

logger = logging.getLogger(__name__)

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

# Scopes: email (address + verified status), profile (name + picture), openid (ID token)
GOOGLE_SCOPES = "openid email profile"


class GoogleOAuthError(Exception):
    """Raised when a Google OAuth operation fails."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


def generate_oauth_state() -> str:
    """Generate a cryptographically secure random state parameter for CSRF protection."""
    return secrets.token_urlsafe(32)


def build_authorization_url(
    client_id: str,
    redirect_uri: str,
    state: str,
) -> str:
    """Build the Google OAuth2 authorization URL.

    The user's browser is redirected here to start the consent flow.
    """
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": GOOGLE_SCOPES,
        "state": state,
        "access_type": "offline",
        "prompt": "consent",
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


async def exchange_code_for_tokens(
    code: str,
    client_id: str,
    client_secret: str,
    redirect_uri: str,
) -> dict:
    """Exchange the authorization code for access and ID tokens.

    Returns the raw token response dict from Google.
    Raises GoogleOAuthError on failure.
    """
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
        )

    if response.status_code != 200:
        logger.warning(
            "Google token exchange failed",
            extra={"status": response.status_code, "body": response.text[:200]},
        )
        raise GoogleOAuthError("Failed to exchange authorization code with Google")

    return response.json()


async def fetch_google_user_info(access_token: str) -> OAuthUserInfo:
    """Fetch user profile info from Google using the access token.

    Returns an OAuthUserInfo with the user's Google ID, email, name, and picture.
    Raises GoogleOAuthError on failure.
    """
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )

    if response.status_code != 200:
        logger.warning(
            "Google userinfo fetch failed",
            extra={"status": response.status_code},
        )
        raise GoogleOAuthError("Failed to fetch user info from Google")

    data = response.json()

    return OAuthUserInfo(
        google_id=data["id"],
        email=data["email"],
        full_name=data.get("name"),
        picture_url=data.get("picture"),
        email_verified=data.get("verified_email", False),
    )
