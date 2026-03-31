"""FastAPI auth dependencies: extract and validate JWT, enforce roles."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.utils import decode_access_token
from src.config import Settings, get_settings
from src.db.models.user import User, UserRole
from src.db.session import get_db
from src.services.session_service import refresh_session_activity, validate_session

_bearer = HTTPBearer()


async def _get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> User:
    """Decode JWT and return the corresponding User. Raises 401 on any failure.

    Also validates the session (not revoked, not timed out) and refreshes
    the last_activity timestamp.
    """
    exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(
            credentials.credentials,
            settings.secret_key,
            settings.algorithm,
            secret_key_previous=settings.secret_key_previous,
        )
        user_id: str | None = payload.get("sub")  # type: ignore[assignment]
        if user_id is None:
            raise exc
    except JWTError as jwt_exc:
        raise exc from jwt_exc

    user = await db.get(User, user_id)
    if user is None or not user.is_active:
        raise exc

    # Validate session if JTI is present (tokens issued before session tracking
    # won't have a JTI — allow them through for backwards compatibility)
    jti: str | None = payload.get("jti")  # type: ignore[assignment]
    if jti:
        session = await validate_session(db, jti)
        if session is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired or revoked. Please log in again.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        await refresh_session_activity(db, jti)

    return user


async def require_staff(user: User = Depends(_get_current_user)) -> User:
    """Require a valid JWT with role staff or admin. Raises 403 otherwise."""
    if user.role not in (UserRole.STAFF.value, UserRole.ADMIN.value):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Staff access required",
        )
    return user


async def require_admin(user: User = Depends(_get_current_user)) -> User:
    """Require a valid JWT with role admin. Raises 403 otherwise."""
    if user.role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user


async def require_vet(user: User = Depends(_get_current_user)) -> User:
    """Require a valid JWT with role vet. Raises 403 otherwise."""
    if user.role != UserRole.VET.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Veterinarian access required",
        )
    return user


async def require_medical_staff(user: User = Depends(_get_current_user)) -> User:
    """Require vet, staff, or admin role — anyone who can access medical records."""
    allowed = (UserRole.VET.value, UserRole.STAFF.value, UserRole.ADMIN.value)
    if user.role not in allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Medical staff access required",
        )
    return user


async def require_verified_rescuer(
    user: User = Depends(_get_current_user), db: AsyncSession = Depends(get_db)
) -> User:
    """Require a verified rescuer profile. Raises 403 otherwise.

    Any authenticated user with a verified rescuer_profiles row may create
    emergencies. Staff and admin are also allowed (they can act on behalf of
    rescuers).
    """
    # Staff/admin bypass
    if user.role in (UserRole.STAFF.value, UserRole.ADMIN.value):
        return user

    from sqlalchemy import select

    from src.db.models.rescuer_profile import RescuerProfile

    stmt = select(RescuerProfile).where(
        RescuerProfile.user_id == user.id,
        RescuerProfile.is_verified.is_(True),
    )
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Verified rescuer profile required",
        )
    return user
