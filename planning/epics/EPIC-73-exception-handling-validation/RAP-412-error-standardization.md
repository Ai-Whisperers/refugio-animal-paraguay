---
story: RAP-412
epic: EPIC-73
title: "Standardize error responses across all routers"
status: ready
priority: 1
points: 3
created: 2026-03-27
---

# RAP-412: Standardize Error Responses Across All Routers

## Story

As an **API client developer**, I want **consistent error response format across all endpoints** so that **I can parse and handle errors uniformly**.

## Description

Different routers return errors in different formats, making client error handling difficult. Some use Pydantic's default 422 format, some return custom JSON, some return generic HTTP errors. All endpoints must return errors in a standard format.

## Standard Error Response Format

All error responses (4xx and 5xx) must follow this format:

```json
{
  "detail": "Human-readable error message",
  "error_code": "MACHINE_READABLE_CODE",
  "timestamp": "2026-03-27T15:30:45Z"
}
```

**For validation errors specifically** (422 Unprocessable Entity):

```json
{
  "detail": "Validation failed",
  "error_code": "VALIDATION_ERROR",
  "timestamp": "2026-03-27T15:30:45Z",
  "fields": {
    "email": ["Invalid email format"],
    "amount_cents": ["Amount must be greater than 0"]
  }
}
```

## Acceptance Criteria

### HTTP Status Code Standards

**Given** any error in any endpoint
**When** error response is returned
**Then**
- [ ] 400 Bad Request — Malformed request (e.g., invalid JSON)
- [ ] 401 Unauthorized — Missing or invalid authentication
- [ ] 403 Forbidden — Authenticated but insufficient permissions
- [ ] 404 Not Found — Resource does not exist
- [ ] 409 Conflict — Duplicate resource, state conflict (e.g., duplicate adoption request)
- [ ] 422 Unprocessable Entity — Input validation failed
- [ ] 500 Internal Server Error — Server error (not a client error)
- [ ] 503 Service Unavailable — External service unavailable (e.g., payment gateway down)

### Error Code Standards

All error_codes follow pattern: `NOUN_VERB` in UPPERCASE_WITH_UNDERSCORES

Examples:
- `INVALID_EMAIL` — Email format invalid
- `ANIMAL_NOT_AVAILABLE` — Animal cannot be adopted (unavailable)
- `DUPLICATE_ADOPTION_REQUEST` — Adopter already has pending request for this animal
- `INSUFFICIENT_PERMISSIONS` — User lacks required role
- `TOKEN_EXPIRED` — Password reset token expired
- `PAYMENT_FAILED` — Payment gateway error
- `DATABASE_ERROR` — Unexpected database error
- `VALIDATION_ERROR` — Input validation failed (422 responses)

### Audit All Routers

**Given** 27 routers in `src/api/`
**When** each router is audited
**Then**
- [ ] All error paths identified
- [ ] All inconsistent error formats documented in progress.md
- [ ] Each error is converted to standard format

**Routers to audit** (27 total):
1. animals.py
2. adoption_requests.py
3. donors.py
4. donations.py
5. adopters.py
6. campaigns.py
7. sponsorships.py
8. volunteer_sessions.py
9. notifications.py
10. email_notifications.py
11. follow_ups.py
12. contact.py
13. webhooks.py
14. auth.py
15. users.py
16. admin.py
17. reports.py
18. password_reset.py
19. public.py
20. health.py
21. (and 7 others — full count 27)

### Common Error Patterns

**401 Unauthorized** — User not authenticated:
```json
{
  "detail": "Not authenticated",
  "error_code": "NOT_AUTHENTICATED",
  "timestamp": "2026-03-27T15:30:45Z"
}
```

**403 Forbidden** — User authenticated but lacks permission:
```json
{
  "detail": "You lack permission to perform this action",
  "error_code": "INSUFFICIENT_PERMISSIONS",
  "timestamp": "2026-03-27T15:30:45Z"
}
```

**404 Not Found** — Resource doesn't exist:
```json
{
  "detail": "Animal not found",
  "error_code": "ANIMAL_NOT_FOUND",
  "timestamp": "2026-03-27T15:30:45Z"
}
```

**409 Conflict** — State conflict or duplicate:
```json
{
  "detail": "You already have a pending adoption request for this animal",
  "error_code": "DUPLICATE_ADOPTION_REQUEST",
  "timestamp": "2026-03-27T15:30:45Z"
}
```

**422 Unprocessable Entity** — Validation failed:
```json
{
  "detail": "Validation failed",
  "error_code": "VALIDATION_ERROR",
  "timestamp": "2026-03-27T15:30:45Z",
  "fields": {
    "email": ["Invalid email format"],
    "amount_cents": ["Must be positive"]
  }
}
```

**500 Internal Server Error** — Unexpected server error:
```json
{
  "detail": "An internal error occurred",
  "error_code": "INTERNAL_SERVER_ERROR",
  "timestamp": "2026-03-27T15:30:45Z"
}
```

**503 Service Unavailable** — External service down:
```json
{
  "detail": "Payment service is temporarily unavailable",
  "error_code": "PAYMENT_SERVICE_UNAVAILABLE",
  "timestamp": "2026-03-27T15:30:45Z"
}
```

### Create Global Exception Handler

**Create file: `src/api/error_handlers.py`**

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class APIException(Exception):
    """Base class for API errors."""
    def __init__(
        self,
        detail: str,
        error_code: str,
        status_code: int = 400,
        fields: dict = None,
    ):
        self.detail = detail
        self.error_code = error_code
        self.status_code = status_code
        self.fields = fields or {}

async def api_exception_handler(request: Request, exc: APIException):
    """Handle APIException and return standard error response."""
    response_data = {
        "detail": exc.detail,
        "error_code": exc.error_code,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    if exc.fields:
        response_data["fields"] = exc.fields

    logger.error(
        f"API error: {exc.error_code}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "error_code": exc.error_code,
            "status_code": exc.status_code,
        },
    )

    return JSONResponse(status_code=exc.status_code, content=response_data)

def register_error_handlers(app: FastAPI):
    """Register all error handlers."""
    app.add_exception_handler(APIException, api_exception_handler)
```

**Register in `src/app.py`**:
```python
from src.api.error_handlers import register_error_handlers

register_error_handlers(app)
```

### Validation Error Handling

Pydantic validation errors (422) need custom handler to add error_code:

```python
from fastapi.exceptions import RequestValidationError

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors."""
    fields = {}
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"][1:])  # Skip "body"
        if field not in fields:
            fields[field] = []
        fields[field].append(error["msg"])

    response_data = {
        "detail": "Validation failed",
        "error_code": "VALIDATION_ERROR",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "fields": fields,
    }

    return JSONResponse(status_code=422, content=response_data)

# Register in app.py
app.add_exception_handler(RequestValidationError, validation_exception_handler)
```

### Update All Endpoints

For each error-raising endpoint, replace custom error handling with APIException:

**Before**:
```python
@router.get("/animals/{animal_id}")
async def get_animal(animal_id: str, db: Session):
    animal = db.query(Animal).filter_by(id=animal_id).first()
    if not animal:
        return JSONResponse(
            status_code=404,
            content={"error": "Not found"}  # Inconsistent format
        )
    return animal
```

**After**:
```python
from src.api.error_handlers import APIException

@router.get("/animals/{animal_id}")
async def get_animal(animal_id: str, db: Session):
    animal = db.query(Animal).filter_by(id=animal_id).first()
    if not animal:
        raise APIException(
            detail="Animal not found",
            error_code="ANIMAL_NOT_FOUND",
            status_code=404,
        )
    return animal
```

### Database Error Handling

Map database errors to appropriate HTTP responses:

```python
from sqlalchemy.exc import IntegrityError

try:
    db.add(new_donor)
    await db.commit()
except IntegrityError as e:
    if "email" in str(e):
        raise APIException(
            detail="Donor with this email already exists",
            error_code="DUPLICATE_EMAIL",
            status_code=409,
        )
    else:
        raise APIException(
            detail="Duplicate record",
            error_code="DUPLICATE_RECORD",
            status_code=409,
        )
```

## Definition of Done

- [ ] Global error handler created in `src/api/error_handlers.py`
- [ ] All 27 routers audited and documented in progress.md
- [ ] All error responses follow standard format (detail, error_code, timestamp)
- [ ] All 4xx status codes correct per HTTP standard
- [ ] All error_codes use NOUN_VERB uppercase pattern
- [ ] All validation errors (422) include fields list
- [ ] All database errors handled and mapped to 4xx/5xx
- [ ] No raw HTTPException or JSONResponse without error_code
- [ ] Timestamps always present in all error responses
- [ ] Code review approved
- [ ] CI pipeline passes (linting, type checking)

## Technical Notes

### Files to Create
- `src/api/error_handlers.py` — Error handler functions and APIException class

### Files to Modify
- `src/app.py` — Register error handlers
- All 27 files in `src/api/` — Update error handling

### Error Code Examples (build inventory)

Create a reference document: `docs/API_ERROR_CODES.md`

```markdown
# API Error Codes

## Authentication (4xx)
- NOT_AUTHENTICATED (401) — User not authenticated
- INVALID_CREDENTIALS (401) — Wrong email or password
- TOKEN_EXPIRED (401) — JWT token expired
- INSUFFICIENT_PERMISSIONS (403) — User lacks required role

## Validation (422)
- VALIDATION_ERROR — Input validation failed (fields included)
- INVALID_EMAIL — Email format invalid
- INVALID_PHONE — Phone format invalid
- INVALID_AMOUNT — Amount invalid (negative, zero, too large)

## Resources (4xx)
- ANIMAL_NOT_FOUND (404)
- ADOPTER_NOT_FOUND (404)
- DONOR_NOT_FOUND (404)
- ADOPTION_REQUEST_NOT_FOUND (404)

## Conflicts (409)
- DUPLICATE_ADOPTION_REQUEST — Adopter already has pending request
- DUPLICATE_EMAIL — Email already in system
- ANIMAL_NOT_AVAILABLE — Animal cannot be adopted
- INVALID_STATUS_TRANSITION — State change not allowed

## Server Errors (5xx)
- INTERNAL_SERVER_ERROR (500) — Unexpected server error
- PAYMENT_SERVICE_UNAVAILABLE (503) — Stripe/Tigo down
- EMAIL_SERVICE_UNAVAILABLE (503) — SMTP server down
- DATABASE_ERROR (500) — Database operation failed
```

---

*Last updated: 2026-03-27*
