"""Session management service.

Handles creation, validation, refresh, and revocation of active sessions.
Sessions are tracked in the active_sessions table alongside JWT tokens
to support timeout-based expiration and admin forced logout.
"""

import logging
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.active_session import ActiveSession

logger = logging.getLogger(__name__)

SESSION_INACTIVITY_TIMEOUT_MINUTES = 30


async def create_session(
    db: AsyncSession,
    user_id: str,
    token_expires_at: datetime,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> str:
    """Create a new active session and return its JTI (JWT ID).

    The JTI is embedded in the JWT token and used to look up
    the session record for timeout/revocation checks.
    """
    jti = uuid.uuid4().hex
    session = ActiveSession(
        user_id=user_id,
        jti=jti,
        expires_at=token_expires_at,
        ip_address=ip_address,
        user_agent=user_agent[:512] if user_agent else None,
    )
    db.add(session)
    await db.flush()
    logger.info("Session created: jti=%s user_id=%s", jti, user_id)
    return jti


async def validate_session(db: AsyncSession, jti: str) -> ActiveSession | None:
    """Validate that a session is active (not revoked, not expired, not timed out).

    Returns the session record if valid, None otherwise.
    """
    result = await db.execute(
        select(ActiveSession).where(
            ActiveSession.jti == jti,
            ActiveSession.revoked_at.is_(None),
        )
    )
    session = result.scalar_one_or_none()

    if session is None:
        return None

    now = datetime.now(UTC)

    # Check JWT expiration
    if session.expires_at < now:
        logger.debug("Session expired: jti=%s", jti)
        return None

    # Check inactivity timeout
    inactivity_deadline = session.last_activity + timedelta(
        minutes=SESSION_INACTIVITY_TIMEOUT_MINUTES
    )
    if inactivity_deadline < now:
        logger.info("Session timed out due to inactivity: jti=%s", jti)
        return None

    return session


async def refresh_session_activity(db: AsyncSession, jti: str) -> None:
    """Update the last_activity timestamp for a session (called on each request)."""
    await db.execute(
        update(ActiveSession)
        .where(ActiveSession.jti == jti)
        .values(last_activity=datetime.now(UTC))
    )


async def revoke_session(db: AsyncSession, session_id: str) -> bool:
    """Revoke (force-logout) a specific session by its ID.

    Returns True if the session was found and revoked, False otherwise.
    """
    session = await db.get(ActiveSession, session_id)
    if session is None or session.revoked_at is not None:
        return False

    session.revoked_at = datetime.now(UTC)
    logger.info("Session revoked: id=%s jti=%s", session_id, session.jti)
    return True


async def revoke_all_user_sessions(db: AsyncSession, user_id: str) -> int:
    """Revoke all active sessions for a user. Returns count of revoked sessions."""
    result = await db.execute(
        select(ActiveSession).where(
            ActiveSession.user_id == user_id,
            ActiveSession.revoked_at.is_(None),
        )
    )
    sessions = result.scalars().all()
    count = 0
    now = datetime.now(UTC)
    for session in sessions:
        session.revoked_at = now
        count += 1
    logger.info("Revoked %d sessions for user_id=%s", count, user_id)
    return count


async def list_active_sessions(db: AsyncSession, user_id: str | None = None) -> list[ActiveSession]:
    """List active (non-revoked, non-expired) sessions.

    If user_id is provided, filter to that user's sessions only.
    """
    now = datetime.now(UTC)
    query = select(ActiveSession).where(
        ActiveSession.revoked_at.is_(None),
        ActiveSession.expires_at > now,
    )
    if user_id:
        query = query.where(ActiveSession.user_id == user_id)
    query = query.order_by(ActiveSession.last_activity.desc())

    result = await db.execute(query)
    return list(result.scalars().all())
