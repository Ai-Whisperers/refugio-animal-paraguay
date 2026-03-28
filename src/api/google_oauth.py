"""Google OAuth2 router: social login with Google accounts.

Endpoints:
  GET  /auth/google/start     — generate authorization URL + state
  POST /auth/google/callback   — exchange code for tokens, create/link user
  POST /auth/google/link       — link Google to existing authenticated account
"""

import logging
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import _get_current_user
from src.auth.utils import create_access_token
from src.config import Settings, get_settings
from src.db.models.user import User, UserRole
from src.db.session import get_db
from src.schemas.error import COMMON_RESPONSES
from src.schemas.oauth import (
    OAuthCallbackRequest,
    OAuthCallbackResponse,
    OAuthLinkRequest,
    OAuthLinkResponse,
    OAuthStartResponse,
    OAuthUserInfo,
)
from src.services.google_oauth_service import (
    GoogleOAuthError,
    build_authorization_url,
    exchange_code_for_tokens,
    fetch_google_user_info,
    generate_oauth_state,
)
from src.services.session_service import create_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth/google", tags=["auth-google"], responses=COMMON_RESPONSES)

# In-memory state store (production should use Redis or DB-backed sessions)
# Maps state -> {"created_at": datetime, "ip": str}
_OAUTH_STATE_STORE: dict[str, dict] = {}

# State parameters expire after 10 minutes
STATE_EXPIRY_MINUTES = 10

# Pending link store: maps state -> OAuthUserInfo for the linking flow
_PENDING_LINK_STORE: dict[str, OAuthUserInfo] = {}


def _cleanup_expired_states() -> None:
    """Remove expired state entries to prevent memory leaks."""
    cutoff = datetime.now(UTC) - timedelta(minutes=STATE_EXPIRY_MINUTES)
    expired = [k for k, v in _OAUTH_STATE_STORE.items() if v["created_at"] < cutoff]
    for key in expired:
        _OAUTH_STATE_STORE.pop(key, None)
        _PENDING_LINK_STORE.pop(key, None)


def _validate_google_config(settings: Settings) -> None:
    """Raise 503 if Google OAuth is not configured."""
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth is not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET.",
        )


@router.get("/start", response_model=OAuthStartResponse)
async def google_oauth_start(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> OAuthStartResponse:
    """Generate the Google OAuth2 authorization URL.

    The frontend should redirect the user's browser to the returned URL.
    The state parameter is stored server-side for CSRF validation on callback.
    """
    _validate_google_config(settings)
    _cleanup_expired_states()

    state = generate_oauth_state()
    _OAUTH_STATE_STORE[state] = {
        "created_at": datetime.now(UTC),
        "ip": request.client.host if request.client else "unknown",
    }

    authorization_url = build_authorization_url(
        client_id=settings.google_client_id,
        redirect_uri=settings.google_redirect_uri,
        state=state,
    )

    return OAuthStartResponse(authorization_url=authorization_url)


@router.post("/callback", response_model=OAuthCallbackResponse)
async def google_oauth_callback(
    body: OAuthCallbackRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> OAuthCallbackResponse:
    """Exchange authorization code for tokens, then create or authenticate user.

    Flow:
    1. Validate state parameter (CSRF protection)
    2. Exchange code for Google access token
    3. Fetch user info from Google
    4. If user with this oauth_id exists: log them in
    5. If email matches existing user without OAuth: return requires_linking=True
    6. Otherwise: create new user account
    """
    _validate_google_config(settings)

    # Validate state parameter
    state_data = _OAUTH_STATE_STORE.pop(body.state, None)
    if state_data is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired state parameter. Please restart the login flow.",
        )

    # Exchange code for tokens
    try:
        token_data = await exchange_code_for_tokens(
            code=body.code,
            client_id=settings.google_client_id,
            client_secret=settings.google_client_secret,
            redirect_uri=settings.google_redirect_uri,
        )
    except GoogleOAuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=exc.message,
        ) from exc

    access_token_google = token_data.get("access_token")
    if not access_token_google:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Google did not return an access token.",
        )

    # Fetch user info from Google
    try:
        google_user = await fetch_google_user_info(access_token_google)
    except GoogleOAuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=exc.message,
        ) from exc

    if not google_user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google account email is not verified.",
        )

    # Check if a user with this Google OAuth ID already exists
    result = await db.execute(
        select(User).where(
            User.oauth_provider == "google",
            User.oauth_id == google_user.google_id,
        )
    )
    existing_oauth_user = result.scalar_one_or_none()

    if existing_oauth_user is not None:
        # Existing OAuth user — log them in
        return await _create_jwt_response(
            db=db,
            user=existing_oauth_user,
            settings=settings,
            request=request,
            is_new_user=False,
        )

    # Check if a user with this email already exists (but no OAuth link)
    result = await db.execute(select(User).where(User.email == google_user.email))
    existing_email_user = result.scalar_one_or_none()

    if existing_email_user is not None:
        # Account exists with this email but not linked to Google
        # Store pending link info and return requires_linking
        link_state = generate_oauth_state()
        _PENDING_LINK_STORE[link_state] = google_user
        _OAUTH_STATE_STORE[link_state] = {
            "created_at": datetime.now(UTC),
            "ip": request.client.host if request.client else "unknown",
            "user_id": str(existing_email_user.id),
        }

        return OAuthCallbackResponse(
            access_token=link_state,  # Temporary token for the linking flow
            token_type="link_pending",
            is_new_user=False,
            requires_linking=True,
            email=google_user.email,
        )

    # New user — create account
    new_user = User(
        email=google_user.email,
        full_name=google_user.full_name,
        hashed_password=None,
        role=UserRole.ADOPTER.value,
        oauth_provider="google",
        oauth_id=google_user.google_id,
        profile_picture_url=google_user.picture_url,
        is_active=True,
        email_verified=True,  # Google already verified the email
    )
    db.add(new_user)
    await db.flush()
    await db.refresh(new_user)

    logger.info("New user created via Google OAuth", extra={"user_id": str(new_user.id)})

    return await _create_jwt_response(
        db=db,
        user=new_user,
        settings=settings,
        request=request,
        is_new_user=True,
    )


@router.post("/link", response_model=OAuthLinkResponse)
async def google_oauth_link(
    body: OAuthLinkRequest,
    request: Request,
    current_user: User = Depends(_get_current_user),
    settings: Settings = Depends(get_settings),
) -> OAuthLinkResponse:
    """Link Google OAuth to the current authenticated user's account.

    Called from the profile settings page to add Google login to an
    existing password-based account.
    """
    _validate_google_config(settings)

    if current_user.oauth_provider == "google":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Account is already linked to Google.",
        )

    if not body.confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Linking cancelled.",
        )

    # Start OAuth flow for linking — generate state tied to the current user
    state = generate_oauth_state()
    _OAUTH_STATE_STORE[state] = {
        "created_at": datetime.now(UTC),
        "ip": request.client.host if request.client else "unknown",
        "user_id": str(current_user.id),
        "linking": True,
    }

    authorization_url = build_authorization_url(
        client_id=settings.google_client_id,
        redirect_uri=settings.google_redirect_uri,
        state=state,
    )

    return OAuthLinkResponse(
        access_token=state,
        token_type="link_start",
        message=authorization_url,
    )


@router.post("/link/confirm", response_model=OAuthCallbackResponse)
async def google_oauth_link_confirm(
    body: OAuthCallbackRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> OAuthCallbackResponse:
    """Complete the account linking flow after Google consent.

    Validates the pending link state, updates the user record with
    Google OAuth credentials, and returns a JWT.
    """
    state_data = _OAUTH_STATE_STORE.pop(body.state, None)
    google_user = _PENDING_LINK_STORE.pop(body.state, None)

    if state_data is None or "user_id" not in state_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired linking state. Please restart the login flow.",
        )

    user_id = state_data["user_id"]
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User account not found.",
        )

    # If google_user info is stored from the callback flow, use it
    if google_user is not None:
        user.oauth_provider = "google"
        user.oauth_id = google_user.google_id
        if google_user.picture_url and not user.profile_picture_url:
            user.profile_picture_url = google_user.picture_url
    else:
        # Need to exchange the code for user info
        try:
            token_data = await exchange_code_for_tokens(
                code=body.code,
                client_id=settings.google_client_id,
                client_secret=settings.google_client_secret,
                redirect_uri=settings.google_redirect_uri,
            )
            google_access_token = token_data.get("access_token", "")
            fetched_user = await fetch_google_user_info(google_access_token)
            user.oauth_provider = "google"
            user.oauth_id = fetched_user.google_id
            if fetched_user.picture_url and not user.profile_picture_url:
                user.profile_picture_url = fetched_user.picture_url
        except GoogleOAuthError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=exc.message,
            ) from exc

    await db.flush()

    logger.info("Google OAuth linked to existing account", extra={"user_id": str(user.id)})

    return await _create_jwt_response(
        db=db,
        user=user,
        settings=settings,
        request=request,
        is_new_user=False,
    )


async def _create_jwt_response(
    db: AsyncSession,
    user: User,
    settings: Settings,
    request: Request,
    is_new_user: bool,
) -> OAuthCallbackResponse:
    """Create a JWT session and return an OAuthCallbackResponse."""
    expires_delta = timedelta(minutes=settings.access_token_expire_minutes)
    token_expires_at = datetime.now(UTC) + expires_delta

    jti = await create_session(
        db,
        user_id=str(user.id),
        token_expires_at=token_expires_at,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await db.commit()

    token = create_access_token(
        data={"sub": str(user.id)},
        secret_key=settings.secret_key,
        algorithm=settings.algorithm,
        expires_delta=expires_delta,
        jti=jti,
    )

    return OAuthCallbackResponse(
        access_token=token,
        is_new_user=is_new_user,
        requires_linking=False,
    )
