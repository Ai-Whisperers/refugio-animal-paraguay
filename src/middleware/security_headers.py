"""HTTP security headers middleware for the Refugio Animal Paraguay API.

Adds hardened HTTP response headers to every API response:

  - Content-Security-Policy (CSP)
  - Strict-Transport-Security (HSTS)  — production only
  - X-Frame-Options
  - X-Content-Type-Options
  - Referrer-Policy
  - Permissions-Policy

The CSP policy is environment-aware:
  - production: strict, no unsafe-inline / unsafe-eval
  - development/test: relaxed to allow hot-reload, inline scripts, and dev tools

References:
  - https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP
  - https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Permissions-Policy
  - https://owasp.org/www-project-secure-headers/
"""

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

# --- Production CSP directives (strict) ---
# API-only backend: no frontend assets served from this origin.
# Forms, scripts, and objects are denied entirely.
CSP_PRODUCTION = (
    "default-src 'none'; "
    "script-src 'none'; "
    "style-src 'none'; "
    "img-src 'none'; "
    "font-src 'none'; "
    "connect-src 'self'; "
    "frame-src 'none'; "
    "object-src 'none'; "
    "base-uri 'self'; "
    "form-action 'none'; "
    "frame-ancestors 'none';"
)

# --- Development CSP directives (relaxed) ---
# Allow inline scripts and eval for hot-module replacement and dev-tools.
CSP_DEVELOPMENT = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data:; "
    "font-src 'self'; "
    "connect-src 'self' ws: wss:; "
    "frame-src 'none'; "
    "object-src 'none'; "
    "base-uri 'self'; "
    "form-action 'self'; "
    "frame-ancestors 'none';"
)

# HSTS: enforce HTTPS for one year, include subdomains.
HSTS_VALUE = "max-age=31536000; includeSubDomains"

# Deny framing entirely — not a browser that loads pages.
X_FRAME_OPTIONS = "DENY"

# Prevent MIME sniffing of response content-type.
X_CONTENT_TYPE_OPTIONS = "nosniff"

# Limit referrer to origin only on cross-site requests.
REFERRER_POLICY = "strict-origin-when-cross-origin"

# Deny access to all sensitive browser APIs from this origin.
PERMISSIONS_POLICY = (
    "accelerometer=(), "
    "ambient-light-sensor=(), "
    "autoplay=(), "
    "battery=(), "
    "camera=(), "
    "display-capture=(), "
    "geolocation=(), "
    "gyroscope=(), "
    "magnetometer=(), "
    "microphone=(), "
    "payment=(), "
    "usb=()"
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Attach HTTP security headers to every API response.

    Args:
        app: The ASGI application.
        environment: Runtime environment string (``"production"``,
            ``"staging"``, ``"development"``, ``"test"``).
            Defaults to ``"development"``.
    """

    def __init__(self, app: object, *, environment: str = "development") -> None:
        super().__init__(app)  # type: ignore[arg-type]
        self._is_production = environment == "production"
        self._csp = CSP_PRODUCTION if self._is_production else CSP_DEVELOPMENT

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Process the request and inject security headers into the response."""
        response = await call_next(request)

        response.headers["Content-Security-Policy"] = self._csp
        response.headers["X-Frame-Options"] = X_FRAME_OPTIONS
        response.headers["X-Content-Type-Options"] = X_CONTENT_TYPE_OPTIONS
        response.headers["Referrer-Policy"] = REFERRER_POLICY
        response.headers["Permissions-Policy"] = PERMISSIONS_POLICY

        # HSTS must only be sent over HTTPS — restrict to production where TLS is enforced.
        if self._is_production:
            response.headers["Strict-Transport-Security"] = HSTS_VALUE

        return response
