---
story: RAP-410
epic: EPIC-73
title: "Replace bare except clauses in notification handlers"
status: ready
priority: 0
points: 3
created: 2026-03-27
---

# RAP-410: Replace Bare Except Clauses in Notification Handlers

## Story

As a **developer**, I want **specific exception handlers in notification code** so that **errors are properly logged and notification failures don't mask other issues**.

## Description

Notification handlers have 14 bare `except Exception` clauses that hide bugs and make debugging difficult. These must be replaced with specific exceptions (SMTPException, TwilioRestException, etc.) and proper logging.

## Acceptance Criteria

### Audit & Identify (all handlers)

**Given** the codebase with notification handlers
**When** `grep -r "except Exception" src/notifications/` is run
**Then**
- [ ] Exactly 14 matches are found (audit inventory)
- [ ] All matches are documented in progress.md with file:line_number

**Match inventory expected**:
- File: `src/notifications/handlers.py` (email, 7 matches)
- File: `src/notifications/in_app_handlers.py` (in-app, 4 matches)
- File: `src/notifications/whatsapp_handlers.py` (WhatsApp, 3 matches)

### Replace in handlers.py

**Given** email notification handler with bare Exception
**When** exception is replaced with specific SMTPException
**Then**
- [ ] Handler catches `aiosmtplib.SMTPException` (not bare Exception)
- [ ] Handler logs with structure: handler_name, error_code, recipient_email, error_message
- [ ] Handler returns `NotificationResult(status="FAILED", error_message=str(e))`
- [ ] Handler does not re-raise (SMTP errors are non-fatal)

**Pattern to follow**:
```python
# Before
try:
    await send_email(...)
except Exception as e:
    logger.error(f"Failed to send email: {e}")

# After
try:
    await send_email(...)
except aiosmtplib.SMTPException as e:
    logger.error(
        "email_handler_failed",
        handler="EmailNotificationHandler",
        error_code="SMTP_ERROR",
        recipient=event.recipient_email,
        error_message=str(e),
    )
    return NotificationResult(status="FAILED", error_message=str(e))
except Exception as e:
    # Catch unexpected errors (not SMTP-related)
    logger.error(
        "email_handler_unexpected_error",
        handler="EmailNotificationHandler",
        error_message=str(e),
    )
    return NotificationResult(status="FAILED", error_message="Unexpected error")
```

**Given** template rendering error in email handler
**When** Jinja2 template is not found
**Then**
- [ ] Handler catches `jinja2.TemplateNotFound` or `jinja2.TemplateError` specifically
- [ ] Error is logged with template name: `{"template": "adoption_approved.html", ...}`
- [ ] Handler returns FAILED status
- [ ] Handler does not re-raise

### Replace in in_app_handlers.py

**Given** in-app notification handler with bare Exception
**When** database write fails
**Then**
- [ ] Handler catches specific `SQLAlchemyError` subclasses:
  - `IntegrityError` (duplicate, foreign key constraint)
  - `OperationalError` (database locked, connection lost)
  - `DataError` (invalid data type)
- [ ] Each has distinct error logging and retry strategy
- [ ] `IntegrityError`: log with constraint details, no retry
- [ ] `OperationalError`: log with retry=True, suggest exponential backoff
- [ ] Handler returns appropriate NotificationResult

**Pattern**:
```python
try:
    await create_in_app_notification(...)
except IntegrityError as e:
    logger.error(
        "inapp_constraint_violation",
        handler="InAppNotificationHandler",
        user_id=event.user_id,
        constraint=str(e.orig),
        retry=False,
    )
    return NotificationResult(status="FAILED", retry=False)
except OperationalError as e:
    logger.error(
        "inapp_database_operational_error",
        handler="InAppNotificationHandler",
        error_message=str(e),
        retry=True,
    )
    return NotificationResult(status="FAILED", retry=True, retry_after_seconds=300)
```

### Replace in whatsapp_handlers.py

**Given** WhatsApp handler with bare Exception
**When** Twilio API call fails
**Then**
- [ ] Handler catches `TwilioRestException` (not bare Exception)
- [ ] Different Twilio error codes are handled:
  - 401: Authentication error (no retry)
  - 429: Rate limit error (retry with backoff)
  - 5xx: Server error (retry with backoff)
- [ ] Error is logged with: status_code, Twilio error message, phone number
- [ ] Handler returns NotificationResult with retry flag and retry_after_seconds

**Pattern**:
```python
try:
    await send_whatsapp_message(...)
except TwilioRestException as e:
    if e.status_code == 401:
        logger.error(
            "whatsapp_auth_failed",
            error_code="TWILIO_AUTH_ERROR",
            retry=False,
        )
        return NotificationResult(status="FAILED", retry=False)
    elif e.status_code == 429:
        retry_after = int(e.response.headers.get("Retry-After", 3600))
        logger.warning(
            "whatsapp_rate_limited",
            error_code="TWILIO_RATE_LIMIT",
            retry_after_seconds=retry_after,
        )
        return NotificationResult(
            status="FAILED",
            retry=True,
            retry_after_seconds=retry_after,
        )
    else:
        logger.error(
            "whatsapp_error",
            status_code=e.status_code,
            error_message=str(e),
            retry=True,
        )
        return NotificationResult(status="FAILED", retry=True)
```

### Exception Hierarchy

**Create file: src/exceptions.py**

```python
"""Application-wide exception hierarchy."""

class NotificationError(Exception):
    """Base class for notification errors."""
    pass

class SMTPException(NotificationError):
    """Email service errors."""
    pass

class TwilioRestException(NotificationError):
    """WhatsApp service errors."""
    pass

class DatabaseError(NotificationError):
    """Database operation errors."""
    pass

class TemplateRenderError(NotificationError):
    """Template rendering errors."""
    pass

class ValidationError(Exception):
    """Input validation errors."""
    pass

class PaymentError(Exception):
    """Payment processing errors."""
    pass
```

Note: Re-export third-party exceptions (aiosmtplib.SMTPException, twilio.rest.TwilioRestException) in this module for consistency.

### Logging Standard

All handlers must log errors with this structure:

```json
{
  "level": "ERROR",
  "handler": "EmailNotificationHandler",
  "event_type": "adoption_approved",
  "error_code": "SMTP_CONNECTION_REFUSED",
  "error_message": "Connection refused to smtp.example.com:587",
  "user_id": "user-uuid",
  "recipient": "adopter@example.com",
  "retry": true,
  "retry_after_seconds": 300,
  "timestamp": "2026-03-27T15:30:45Z"
}
```

All 14 handlers must use structlog (not print or basic logging) with this format.

## Definition of Done

- [ ] All 14 bare `except Exception` clauses replaced with specific exceptions
- [ ] All handlers use structlog with WHAT/WHY/HOW format
- [ ] Each handler has retry flag (True/False) in result
- [ ] Each handler logs full context (user_id, event_type, error_details)
- [ ] No secrets logged (mask tokens, passwords, PII)
- [ ] Code passes linting (Ruff, mypy)
- [ ] Tests from RAP-407 pass
- [ ] Code review approved

## Technical Notes

### Files to Modify
- `src/notifications/handlers.py` — 7 bare except clauses
- `src/notifications/in_app_handlers.py` — 4 bare except clauses
- `src/notifications/whatsapp_handlers.py` — 3 bare except clauses

### Files to Create
- `src/exceptions.py` — Exception hierarchy

### Import Changes

All handlers must import specific exceptions:
```python
import aiosmtplib  # For SMTPException
from twilio.rest import TwilioException  # For TwilioRestException
from sqlalchemy.exc import IntegrityError, OperationalError  # For database errors
import jinja2  # For TemplateNotFound

import structlog  # For structured logging
logger = structlog.get_logger()
```

### Linting & Type Checking

After changes:
```bash
ruff check src/notifications/  # Must be zero warnings
mypy src/notifications/         # Must be zero type errors
```

### Testing Strategy

All 14 exception replacements will be tested in RAP-407 (notification handler exception tests). This story focuses on code changes; tests verify correctness.

---

*Last updated: 2026-03-27*
