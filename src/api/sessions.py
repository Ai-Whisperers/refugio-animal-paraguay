"""Session management API endpoints (admin only).

Endpoints:
  GET    /auth/sessions          - List active sessions
  DELETE /auth/sessions/{id}     - Force-logout a specific session
  DELETE /auth/sessions/user/{id} - Force-logout all sessions for a user
"""

import logging
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_admin
from src.db.models.user import User
from src.db.session import get_db
from src.middleware.rate_limiter import AUTH_RATE_LIMIT, limiter
from src.services.session_service import (
    list_active_sessions,
    revoke_all_user_sessions,
    revoke_session,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth/sessions", tags=["auth"])


class SessionResponse(BaseModel):
    """Response schema for an active session."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    jti: str
    created_at: datetime
    last_activity: datetime
    expires_at: datetime
    ip_address: str | None
    user_agent: str | None


class SessionListResponse(BaseModel):
    """Response schema for session list."""

    sessions: list[SessionResponse]
    count: int


class SessionRevokeResponse(BaseModel):
    """Response for session revocation."""

    revoked: bool
    message: str


@router.get("", response_model=SessionListResponse)
@limiter.limit(AUTH_RATE_LIMIT)
async def get_active_sessions(
    request: Request,
    user_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> SessionListResponse:
    """List active sessions. Optionally filter by user_id. Admin only."""
    sessions = await list_active_sessions(
        db, user_id=str(user_id) if user_id else None
    )
    return SessionListResponse(
        sessions=[SessionResponse.model_validate(s) for s in sessions],
        count=len(sessions),
    )


@router.delete("/{session_id}", response_model=SessionRevokeResponse)
@limiter.limit(AUTH_RATE_LIMIT)
async def force_logout_session(
    request: Request,
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> SessionRevokeResponse:
    """Force-logout a specific session. Admin only."""
    revoked = await revoke_session(db, str(session_id))
    await db.commit()

    if not revoked:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or already revoked.",
        )

    return SessionRevokeResponse(
        revoked=True,
        message="Sesion cerrada exitosamente.",
    )


@router.delete("/user/{user_id}", response_model=SessionRevokeResponse)
@limiter.limit(AUTH_RATE_LIMIT)
async def force_logout_all_user_sessions(
    request: Request,
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> SessionRevokeResponse:
    """Force-logout all sessions for a specific user. Admin only."""
    count = await revoke_all_user_sessions(db, str(user_id))
    await db.commit()

    return SessionRevokeResponse(
        revoked=count > 0,
        message=f"{count} sesiones cerradas para el usuario.",
    )
