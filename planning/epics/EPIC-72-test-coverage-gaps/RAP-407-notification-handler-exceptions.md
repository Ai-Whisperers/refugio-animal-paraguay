---
story: RAP-407
epic: EPIC-72
title: "Add notification handler exception tests"
status: ready
priority: 1
points: 3
created: 2026-03-27
---

# RAP-407: Add Notification Handler Exception Tests

## Story

As a **developer**, I want **specific exception tests for notification handlers** so that **notification failures are caught, logged, and don't crash the event bus**.

## Description

Notification handlers in `src/notifications/handlers.py`, `in_app_handlers.py`, and `whatsapp_handlers.py` currently have 14 bare `except Exception` clauses with minimal testing. These handlers are called from the event bus and must:

1. Catch specific exceptions (not bare Exception)
2. Log errors with full context
3. Not crash the bus when an individual handler fails
4. Be testable for each failure scenario

This story adds specific exception tests and validates error handling.

## Acceptance Criteria

### Email Handler Exception Tests (tests/unit/test_email_handlers_exceptions.py)

**Given** an email handler receiving an event when SMTP is unreachable
**When** `send_email_notification(event)` is called
**Then**
- [ ] `SMTPException` is caught (not bare Exception)
- [ ] Error is logged with: handler name, event type, email address, error details
- [ ] Handler returns `NotificationResult(status=FAILED, error_message=str(exception))`
- [ ] Event bus continues processing other handlers

**Given** an email handler with invalid recipient email in event
**When** handler processes event
**Then**
- [ ] `ValueError` is caught and converted to `NotificationResult(status=FAILED)`
- [ ] Error message specifies "invalid email format"
- [ ] No email is sent

**Given** an email handler timeout (SMTP takes >30s)
**When** handler is configured with 30s timeout
**Then**
- [ ] `asyncio.TimeoutError` is caught
- [ ] Handler returns FAILED status
- [ ] Error message specifies "timeout"
- [ ] Caller can implement retry logic

**Given** an email handler with missing email template
**When** handler tries to render template
**Then**
- [ ] `jinja2.TemplateNotFound` is caught
- [ ] Error is logged with: template name, handler name
- [ ] Handler returns FAILED status
- [ ] Alert is sent to ops (optional: log with error level)

**Given** an email handler with database unavailable
**When** handler queries for user email preferences
**Then**
- [ ] `SQLAlchemyError` is caught (connection errors, query errors)
- [ ] Error is logged with context (user_id, operation)
- [ ] Handler returns FAILED status with retry=True (transient error)
- [ ] Caller can implement exponential backoff

### In-App Notification Handler Exception Tests (tests/unit/test_inapp_handlers_exceptions.py)

**Given** an in-app handler when database write fails
**When** `create_in_app_notification(event)` is called
**Then**
- [ ] `IntegrityError` is caught (duplicate key, FK violation)
- [ ] Error is logged with: user_id, notification type, constraint details
- [ ] Handler returns FAILED status
- [ ] Transaction is rolled back (no partial writes)

**Given** an in-app handler with invalid user_id in event
**When** handler attempts to create notification for nonexistent user
**Then**
- [ ] `ForeignKeyError` is caught
- [ ] Error is logged with: user_id, event type
- [ ] Handler returns FAILED status with `retry=False` (permanent error)

**Given** an in-app handler creating notification when database is locked
**When** concurrent writes occur
**Then**
- [ ] `OperationalError` is caught (database is locked)
- [ ] Handler returns FAILED status with `retry=True`
- [ ] Error is logged with retry guidance
- [ ] Caller implements exponential backoff

**Given** an in-app handler with payload larger than max allowed
**When** serialization is attempted
**Then**
- [ ] `SerializationError` or `ValueError` is caught
- [ ] Error is logged specifying payload size limit
- [ ] Handler returns FAILED status

### WhatsApp Handler Exception Tests (tests/unit/test_whatsapp_handlers_exceptions.py)

**Given** a WhatsApp handler when Twilio API fails
**When** `send_whatsapp_notification(event)` is called and API returns 401
**Then**
- [ ] `TwilioRestException` is caught (not bare Exception)
- [ ] Error is logged with: Twilio error code, recipient phone, message content
- [ ] Handler returns FAILED status with appropriate HTTP status code

**Given** a WhatsApp handler with invalid phone number
**When** handler processes event with malformed phone (non-numeric, wrong country code)
**Then**
- [ ] `ValueError` is caught during phone validation
- [ ] Error is logged specifying: expected format, received value
- [ ] Handler returns FAILED status with `retry=False`

**Given** a WhatsApp handler with rate limit (Twilio returns 429)
**When** too many messages sent too quickly
**Then**
- [ ] `TwilioRestException` with status_code=429 is caught
- [ ] Error is logged with: retry-after header (if present), current rate
- [ ] Handler returns FAILED status with `retry=True` and `retry_after_seconds`
- [ ] Caller implements backoff using retry_after

**Given** a WhatsApp handler with network timeout
**When** request to Twilio API times out
**Then**
- [ ] `ConnectionError` or `asyncio.TimeoutError` is caught
- [ ] Error is logged with: timeout duration, endpoint
- [ ] Handler returns FAILED status with `retry=True`

**Given** a WhatsApp handler when authentication token is missing/invalid
**When** handler tries to call Twilio without valid credentials
**Then**
- [ ] `TwilioRestException` with status_code=401 is caught
- [ ] Error is logged (no credential values logged)
- [ ] Handler returns FAILED status with `retry=False`
- [ ] Alert sent to ops (credentials need refresh)

### Event Bus Integration Tests (tests/integration/test_event_bus_resilience.py)

**Given** an event bus with 3 handlers (email, in-app, WhatsApp)
**When** email handler fails (SMTP error)
**Then**
- [ ] Bus does NOT crash
- [ ] In-app and WhatsApp handlers still execute
- [ ] Bus returns: `[{email: FAILED}, {inapp: SUCCESS}, {whatsapp: SUCCESS}]`
- [ ] Adopter is notified via in-app (email failed gracefully)

**Given** an event bus where all 3 handlers fail
**When** all handlers encounter exceptions
**Then**
- [ ] Bus completes without crashing
- [ ] Returns: `{overall_status: PARTIAL_FAILURE, failed_handlers: [...]}`
- [ ] Ops alert is triggered (all notification channels failed)
- [ ] Error summary is logged with all failures

**Given** handlers with different error severities (one transient, one permanent)
**When** event is processed
**Then**
- [ ] Transient errors are marked `retry=True` (will be retried by scheduler)
- [ ] Permanent errors are marked `retry=False`
- [ ] Retry queue includes only transient failures

### Error Logging Standard (all handlers)

All handlers must log errors in this structure:
```json
{
  "level": "ERROR",
  "handler": "EmailNotificationHandler",
  "event_type": "adoption_approved",
  "error_code": "SMTP_CONNECTION_FAILED",
  "error_message": "Connection refused to mail.example.com:587",
  "user_id": "user-123",
  "retry_eligible": true,
  "timestamp": "2026-03-27T15:30:45Z"
}
```

**Acceptance**: All 14 bare `except Exception` replaced with specific exceptions, each with this log structure.

## Definition of Done

- [ ] All handler exception test files created
- [ ] All 14 bare `except Exception` clauses replaced with specific exceptions
- [ ] Each exception has structured logging with WHAT/WHY/HOW
- [ ] All tests pass
- [ ] No skipped tests
- [ ] Integration test verifies bus resilience
- [ ] Code review approved
- [ ] CI pipeline passes

## Technical Notes

### Files to Modify
- `src/notifications/handlers.py` — Email notification handlers (7 bare except clauses)
- `src/notifications/in_app_handlers.py` — In-app notification handlers (4 bare except clauses)
- `src/notifications/whatsapp_handlers.py` — WhatsApp handlers (3 bare except clauses)

### Files to Create
- `tests/unit/test_email_handlers_exceptions.py`
- `tests/unit/test_inapp_handlers_exceptions.py`
- `tests/unit/test_whatsapp_handlers_exceptions.py`
- `tests/integration/test_event_bus_resilience.py`

### Exception Hierarchy to Use

```python
# Create in src/exceptions.py (if not exists)
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

class TemplateError(NotificationError):
    """Template rendering errors."""
    pass
```

### Structured Logging Pattern

```python
import logging
import structlog

logger = structlog.get_logger()

try:
    send_email(...)
except SMTPException as e:
    logger.error(
        "email_send_failed",
        handler="EmailNotificationHandler",
        event_type=event.type,
        recipient=event.recipient_email,
        error_code="SMTP_CONNECTION_FAILED",
        error_message=str(e),
        user_id=event.user_id,
        retry_eligible=True,
    )
    return NotificationResult(
        status="FAILED",
        error_message=str(e),
        retry=True,
        retry_after_seconds=300
    )
```

### Testing with pytest-mock and responses

```python
import responses  # for mocking HTTP calls
from unittest.mock import patch, MagicMock

@pytest.mark.asyncio
async def test_whatsapp_handler_rate_limit(mock_twilio):
    # Mock Twilio to return 429
    mock_twilio.messages.create.side_effect = TwilioRestException(
        status_code=429,
        msg="Rate limit exceeded"
    )

    result = await send_whatsapp_notification(event)

    assert result.status == "FAILED"
    assert result.retry == True
    assert result.retry_after_seconds > 0
```

---

*Last updated: 2026-03-27*
