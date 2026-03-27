"""Audit trail middleware — automatic logging of authenticated write requests.

Intercepts POST, PUT, PATCH, DELETE requests that return a successful response
(2xx) and records an audit log entry. The user is identified from the JWT
in the Authorization header.

Non-authenticated requests and failed requests are silently skipped.
"""

import logging
from uuid import UUID

from jose import JWTError
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from src.auth.utils import decode_access_token
from src.config import get_settings
from src.db.models.audit_log import AuditLog
from src.db.session import get_async_session

logger = logging.getLogger(__name__)

# HTTP methods that constitute "write" operations for audit purposes
AUDITABLE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

# Paths excluded from audit logging (health checks, static, etc.)
EXCLUDED_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}

# Map HTTP methods to audit action types
METHOD_TO_ACTION = {
    "POST": "create",
    "PUT": "update",
    "PATCH": "update",
    "DELETE": "delete",
}


def _extract_resource_info(path: str) -> tuple[str, str | None]:
    """Extract resource type and ID from a URL path.

    Examples:
        /animals/123       -> ("animals", "123")
        /animals           -> ("animals", None)
        /auth/token        -> ("auth", None)
        /admin/audit-logs  -> ("admin.audit-logs", None)
    """
    parts = [p for p in path.strip("/").split("/") if p]
    if not parts:
        return ("unknown", None)

    # If the path has an ID-like segment (UUID or numeric), extract it
    resource_type = parts[0]
    resource_id: str | None = None

    if len(parts) >= 2:
        candidate = parts[1]
        # Check if it looks like a UUID or numeric ID
        try:
            UUID(candidate)
            resource_id = candidate
        except ValueError:
            # Not a UUID — might be a sub-resource or action
            resource_type = f"{parts[0]}.{parts[1]}"
            if len(parts) >= 3:
                try:
                    UUID(parts[2])
                    resource_id = parts[2]
                except ValueError:
                    pass

    return (resource_type, resource_id)


def _extract_user_id_from_token(request: Request) -> UUID | None:
    """Try to extract user_id from the Authorization Bearer token.

    Returns None if no valid token is found (non-authenticated request).
    """
    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        return None

    token = auth_header[7:]
    settings = get_settings()
    try:
        payload = decode_access_token(token, settings.secret_key, settings.algorithm)
        sub = payload.get("sub")
        if sub:
            return UUID(str(sub))
    except (JWTError, ValueError):
        pass
    return None


class AuditMiddleware(BaseHTTPMiddleware):
    """Middleware that records audit log entries for authenticated write requests."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        # Only audit write methods
        if request.method not in AUDITABLE_METHODS:
            return response

        # Skip excluded paths
        if request.url.path in EXCLUDED_PATHS:
            return response

        # Only audit successful responses
        if not (200 <= response.status_code < 300):
            return response

        # Extract user from JWT — skip if not authenticated
        user_id = _extract_user_id_from_token(request)
        if user_id is None:
            return response

        # Extract resource info from path
        resource_type, resource_id = _extract_resource_info(request.url.path)
        action = METHOD_TO_ACTION.get(request.method, "unknown")

        # Record audit entry asynchronously
        try:
            async with get_async_session() as session:
                entry = AuditLog(
                    user_id=user_id,
                    action=action,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    ip_address=request.client.host if request.client else None,
                    user_agent=request.headers.get("user-agent", "")[:500],
                    request_id=getattr(request.state, "request_id", None),
                )
                session.add(entry)
                await session.commit()
        except Exception as exc:
            logger.exception(
                "Failed to record audit entry: user=%s action=%s resource=%s error=%s",
                user_id,
                action,
                resource_type,
                exc,
            )

        return response
