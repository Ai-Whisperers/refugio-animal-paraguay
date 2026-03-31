"""Pydantic schemas for Two-Factor Authentication (TOTP) endpoints."""

from pydantic import BaseModel, Field


class TotpSetupResponse(BaseModel):
    """Returned by POST /auth/2fa/setup — contains the provisioning URI and raw secret."""

    provisioning_uri: str = Field(
        ...,
        description="otpauth:// URI to be encoded as a QR code by the frontend.",
    )
    secret: str = Field(
        ...,
        description="Raw base32 secret — displayed as a fallback manual entry key.",
    )


class TotpVerifyRequest(BaseModel):
    """Request body for POST /auth/2fa/verify (activates 2FA) and POST /auth/2fa/validate."""

    code: str = Field(
        ...,
        min_length=6,
        max_length=8,
        description="6-digit TOTP code from the authenticator app.",
        examples=["123456"],
    )


class TotpDisableRequest(BaseModel):
    """Request body for POST /auth/2fa/disable — requires a live TOTP code to deactivate."""

    code: str = Field(
        ...,
        min_length=6,
        max_length=8,
        description="Current TOTP code to confirm the user controls the device.",
        examples=["654321"],
    )


class TotpStatusResponse(BaseModel):
    """Response for GET /auth/2fa/status."""

    enabled: bool = Field(..., description="Whether 2FA is active for this user.")


class BackupCodesResponse(BaseModel):
    """Returned by POST /auth/2fa/backup-codes — one-time display of plain-text codes."""

    codes: list[str] = Field(
        ...,
        description="Plain-text backup codes. Store these securely — they cannot be retrieved again.",
    )


class BackupCodesCountResponse(BaseModel):
    """Returned by GET /auth/2fa/backup-codes/count — remaining unused backup codes."""

    remaining: int = Field(
        ...,
        ge=0,
        description="Number of unused backup codes remaining for this user.",
    )
