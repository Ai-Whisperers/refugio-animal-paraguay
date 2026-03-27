---
story: RAP-418
epic: EPIC-74
title: "Add request/response logging middleware"
status: ready
priority: 1
points: 3
created: 2026-03-27
---

# RAP-418: Add Request/Response Logging Middleware

## Story

As a **developer**, I want **all HTTP requests logged with context and performance metrics** so that **request flows are traceable and performance issues are visible**.

## Description

Every HTTP request should be logged with: method, path, status code, duration, user_id, and request_id. This enables request tracing, performance monitoring, and debugging.

## Acceptance Criteria

### Log Every Request

**Given** any HTTP request
**When** request is processed
**Then**
- [ ] Request is logged in middleware (after response is sent)
- [ ] Log includes: method, path, status_code, duration_ms, user_id, request_id
- [ ] All logs are structured JSON (from RAP-415)

**Log structure**:
```json
{
  "timestamp": "2026-03-27T15:30:45.123Z",
  "level": "INFO",
  "message": "http_request",
  "method": "POST",
  "path": "/donations",
  "status_code": 201,
  "duration_ms": 145,
  "user_id": "user-uuid",
  "request_id": "req-abc123",
  "response_size_bytes": 512
}
```

### Measure Request Duration

**Given** request processing
**When** middleware wraps request
**Then**
- [ ] Duration is measured from request start to response end
- [ ] Duration is included in log in milliseconds
- [ ] Slow requests (> 1000ms) are logged at WARNING level

**Code**:
```python
import time

@app.middleware("http")
async def log_request_middleware(request: Request, call_next):
    start_time = time.time()

    # Process request
    response = await call_next(request)

    # Calculate duration
    duration_ms = int((time.time() - start_time) * 1000)

    # Log
    level = "warning" if duration_ms > 1000 else "info"
    logger.log(
        level,
        "http_request",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=duration_ms,
    )

    return response
```

### Extract User Context

**Given** authenticated request
**When** middleware processes request
**Then**
- [ ] User ID is extracted from JWT token (if present)
- [ ] User ID is included in log
- [ ] Unauthenticated requests have user_id=None

**Code**:
```python
from src.auth import get_current_user

@app.middleware("http")
async def add_user_context(request: Request, call_next):
    user = None
    try:
        user = await get_current_user(request)
    except:
        pass  # Not authenticated

    # Add to context
    request.state.user_id = user.id if user else None

    response = await call_next(request)
    return response
```

### Request ID Propagation

**Given** incoming request
**When** request enters middleware
**Then**
- [ ] X-Request-ID header is read (if present)
- [ ] If not present, UUID is generated
- [ ] Request ID is added to response headers
- [ ] Request ID is included in all logs from this request

**Code**:
```python
import uuid

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    request.state.request_id = request_id

    # Bind to logging context
    structlog.get_logger().context.bind(request_id=request_id)

    response = await call_next(request)

    # Add to response headers
    response.headers["x-request-id"] = request_id
    return response
```

### Request Body Logging (optional)

**Given** POST/PATCH requests with body
**When** middleware logs request
**Then**
- [ ] Request body is logged (or request size)
- [ ] Sensitive fields are masked (password, token, card_number)
- [ ] Body is truncated if > 10KB (avoid log spam)

**Code**:
```python
@app.middleware("http")
async def log_request_body(request: Request, call_next):
    if request.method in ["POST", "PATCH"]:
        body = await request.body()
        body_size = len(body)

        if body_size > 0 and body_size < 10000:
            try:
                data = json.loads(body)
                # Mask sensitive fields
                data = mask_sensitive_fields(data)
                logger.debug("request_body", data=data)
            except:
                pass  # Not JSON

    response = await call_next(request)
    return response
```

### Response Size Tracking

**Given** response is sent
**When** middleware logs request
**Then**
- [ ] Response size in bytes is included
- [ ] Large responses (> 1MB) are logged at WARNING level

**Code**:
```python
response_size = sum(len(chunk) for chunk in response.body_iterator)
if response_size > 1000000:
    logger.warning(
        "large_response",
        response_size_bytes=response_size,
    )
```

### Exclude Health Checks

**Given** request to `/health`
**When** middleware processes request
**Then**
- [ ] Health check is NOT logged (would clutter logs)
- [ ] Other requests are logged normally

**Code**:
```python
@app.middleware("http")
async def log_request_middleware(request: Request, call_next):
    if request.url.path == "/health":
        return await call_next(request)

    # ... logging logic ...
```

### Exclude Static Assets

**Given** request to static files (JS, CSS, images)
**When** middleware processes request
**Then**
- [ ] Static requests are NOT logged
- [ ] API requests are logged

**Code**:
```python
EXCLUDED_PATHS = {"/health", "/static", "/docs", "/openapi.json"}

if request.url.path in EXCLUDED_PATHS or request.url.path.startswith("/static/"):
    return await call_next(request)
```

### Error Logging

**Given** request results in error
**When** response status is 5xx
**Then**
- [ ] Error is logged at ERROR level (not INFO)
- [ ] Error includes: user_id, request_id, endpoint, error_type
- [ ] Error is sent to Sentry (from RAP-416)

**Code**:
```python
response = await call_next(request)

if response.status_code >= 500:
    logger.error(
        "http_request_error",
        status_code=response.status_code,
        user_id=request.state.user_id,
    )
else:
    logger.info("http_request", status_code=response.status_code)
```

### Middleware Order

All middleware must be registered in correct order:

1. Request ID (first, for all downstream to use)
2. User context (authenticate user early)
3. Audit logging (for security/compliance)
4. Request/response logging (main logging)
5. Error handling (catch errors)

## Definition of Done

- [ ] Request/response logging middleware created
- [ ] All requests logged (except /health, /static, /docs)
- [ ] Log includes: method, path, status_code, duration_ms, user_id, request_id
- [ ] Request ID is propagated to response headers
- [ ] Sensitive fields are masked in request body logging
- [ ] Slow requests (>1s) logged at WARNING level
- [ ] Error responses (5xx) logged at ERROR level
- [ ] Health check requests excluded from logging
- [ ] Code review approved
- [ ] CI pipeline passes

## Technical Notes

### Middleware Location
`src/middleware/logging_middleware.py`

### Register in app.py
```python
from src.middleware.logging_middleware import (
    add_request_id,
    add_user_context,
    log_request_middleware,
)

app.middleware("http")(add_request_id)
app.middleware("http")(add_user_context)
app.middleware("http")(log_request_middleware)
```

### Mask Sensitive Fields
Use utility from RAP-408 (audit middleware):
```python
def mask_sensitive_fields(data):
    if isinstance(data, dict):
        return {
            k: "***" if k in ["password", "token", "card_number"] else v
            for k, v in data.items()
        }
    return data
```

---

*Last updated: 2026-03-27*
