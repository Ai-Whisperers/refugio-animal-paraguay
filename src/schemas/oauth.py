"""Pydantic schemas for Google OAuth endpoints."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class OAuthStartResponse(BaseModel):
    """Response from GET /auth/google/start — redirect URL for Google consent."""

    authorization_url: str = Field(
        ..., description="Google OAuth2 authorization URL to redirect the user to."
    )


class OAuthCallbackRequest(BaseModel):
    """Request body for POST /auth/google/callback."""

    code: str = Field(..., description="Authorization code from Google.")
    state: str = Field(..., description="Anti-CSRF state parameter.")


class OAuthCallbackResponse(BaseModel):
    """Response from POST /auth/google/callback."""

    access_token: str
    token_type: str = "bearer"
    is_new_user: bool = Field(
        default=False,
        description="True if a new account was created during this OAuth flow.",
    )
    requires_linking: bool = Field(
        default=False,
        description="True if an existing account with this email was found and needs linking.",
    )
    email: str | None = Field(
        default=None,
        description="User email (included when requires_linking is True).",
    )


class OAuthLinkRequest(BaseModel):
    """Request to link an existing account with Google OAuth."""

    confirm: bool = Field(..., description="True to confirm linking, False to cancel.")


class OAuthLinkResponse(BaseModel):
    """Response after linking an existing account with Google."""

    access_token: str
    token_type: str = "bearer"
    message: str


class OAuthUserInfo(BaseModel):
    """Google user info extracted from the ID token or userinfo endpoint."""

    google_id: str
    email: str
    full_name: str | None = None
    picture_url: str | None = None
    email_verified: bool = False


class OAuthUserResponse(BaseModel):
    """User response including OAuth fields."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    full_name: str | None = None
    role: str
    is_active: bool
    email_verified: bool
    oauth_provider: str | None = None
    profile_picture_url: str | None = None
