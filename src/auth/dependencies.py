"""FastAPI auth dependencies: extract and validate JWT, enforce roles."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.utils import decode_access_token
from src.config import Settings, get_settings
from src.db.models.user import User, UserRole
from src.db.session import get_db

_bearer = HTTPBearer()


async def _get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> User:
    """Decode JWT and return the corresponding User. Raises 401 on any failure."""
    exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(
            credentials.credentials, settings.secret_key, settings.algorithm
        )
        user_id: str | None = payload.get("sub")  # type: ignore[assignment]
        if user_id is None:
            raise exc
    except JWTError:
        raise exc

    user = await db.get(User, user_id)
    if user is None or not user.is_active:
        raise exc
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
