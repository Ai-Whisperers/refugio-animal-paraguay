"""FastAPI middleware for automatic audit trail recording.

Intercepts all authenticated mutating requests (POST, PUT, PATCH, DELETE)
and records an audit log entry after the response is sent. Uses the event
bus for async, non-blocking audit recording.

Design decisions:
- Only mutating methods are audited (GET/HEAD/OPTIONS excluded by default)
- Audit recording is fire-and-forget via event bus to avoid adding latency
- Sensitive paths (login, password reset) are excluded from detailed logging
- User ID is extracted from the JWT in the Authorization header
"""

import logging
import re
from uuid import UUID

from fastapi import Request, Response
from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from src.config import Settings, get_settings
from src.db.models.audit_log import (
    HTTP_METHOD_TO_ACTION,
    PATH_TO_RESOURCE_TYPE,
    AuditAction,
    AuditLog,
    ResourceType,
)
from src.db.session import get_session_factory

logger = logging.getLogger(__name__)

# HTTP methods that trigger audit recording
AUDITED_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})

# Paths excluded from audit logging (contain sensitive data)
EXCLUDED_PATHS = frozenset(
    {
        "/auth/token",
        "/auth/password-reset",
        "/auth/password-reset/confirm",
        "/auth/verify-email",
        "/health",
        "/docs",
        "/openapi.json",
        "/redoc",
    }
)

# Regex to extract resource ID from URL paths like /animals/{uuid}
_RESOURCE_ID_PATTERN = re.compile(
    r"^(/[a-z-]+)/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})"
)

# Event type for audit events published to the event bus
AUDIT_EVENT_TYPE = "audit.action_recorded"


def extract_user_id_from_token(authorization: str | None, settings: Settings) -> str | None:
    """Extract user_id (sub claim) from a Bearer JWT token.

    Returns None if the header is missing, malformed, or the token is invalid.
    Never raises — audit middleware must not break request processing.
    """
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization[7:]
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload.get("sub")
    except JWTError:
        return None


def parse_resource_from_path(path: str) -> tuple[ResourceType, str | None]:
    """Extract resource type and optional resource ID from a URL path.

    Returns (ResourceType, resource_id) where resource_id may be None
    for collection-level operations (e.g., POST /animals).
    """
    # Try to match /resource-type/{uuid} pattern
    match = _RESOURCE_ID_PATTERN.match(path)
    if match:
        prefix = match.group(1)
        resource_id = match.group(2)
    else:
        # Strip trailing slashes and query parameters
        prefix = "/" + path.strip("/").split("/")[0] if path != "/" else "/"
        prefix = "/" + prefix.strip("/")
        resource_id = None

    resource_type = PATH_TO_RESOURCE_TYPE.get(prefix, ResourceType.SYSTEM)
    return resource_type, resource_id


def determine_action(method: str, path: str) -> AuditAction:
    """Determine the audit action from the HTTP method and path.

    Special cases:
    - POST /auth/users -> CREATE (user creation)
    - POST /auth/token -> LOGIN
    """
    if path == "/auth/users" and method == "POST":
        return AuditAction.CREATE
    return HTTP_METHOD_TO_ACTION.get(method, AuditAction.READ)


class AuditMiddleware(BaseHTTPMiddleware):
    """Middleware that records audit log entries for authenticated requests.

    Publishes audit events to the event bus after response is sent.
    Non-blocking: failures in audit recording do not affect the response.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """Process the request and record an audit entry if applicable."""
        path = request.url.path
        method = request.method

        # Skip non-audited methods and excluded paths
        if method not in AUDITED_METHODS or path in EXCLUDED_PATHS:
            return await call_next(request)

        # Process the request first
        response = await call_next(request)

        # Only audit successful or client-error responses from authenticated users
        settings = get_settings()
        user_id = extract_user_id_from_token(request.headers.get("authorization"), settings)

        if user_id is None:
            return response

        # Extract audit metadata
        resource_type, resource_id = parse_resource_from_path(path)
        action = determine_action(method, path)

        # Get client info
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent", "")[:500]

        # Write audit log entry directly to the database
        try:
            session_factory = get_session_factory()
            if session_factory is not None:
                async with session_factory() as session:
                    entry = AuditLog(
                        user_id=UUID(user_id),
                        action=action.value,
                        resource_type=resource_type.value,
                        resource_id=resource_id,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        http_method=method,
                        path=path,
                        status_code=response.status_code,
                    )
                    session.add(entry)
                    await session.commit()
        except Exception:
            # Audit recording must never break the response
            logger.exception("Failed to record audit entry for %s %s", method, path)

        return response
