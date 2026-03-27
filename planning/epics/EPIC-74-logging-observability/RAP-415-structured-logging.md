---
story: RAP-415
epic: EPIC-74
title: "Add structured JSON logging (structlog)"
status: ready
priority: 0
points: 5
created: 2026-03-27
---

# RAP-415: Add Structured JSON Logging (Structlog)

## Story

As a **developer**, I want **structured JSON logging throughout the app** so that **logs are machine-parseable, queryable, and include full context**.

## Description

Current logging uses print() and basic Python logging with text messages. This is hard to parse, search, and aggregate. All logging must use structlog with JSON output, including context (request_id, user_id, endpoint).

## Acceptance Criteria

### Setup Structlog

**Given** the application is starting
**When** logging is initialized
**Then**
- [ ] structlog is configured in `src/config.py` or `src/logging_config.py`
- [ ] Output format is JSON (not text)
- [ ] Each log entry includes: timestamp, level, message, context fields
- [ ] Async logging is configured (doesn't block requests)

**Configuration example**:
```python
import structlog

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.dev.ConsoleRenderer()  # Change to JSONRenderer for prod
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)
```

### Replace All print() and logging.* Calls

**Given** any print() statement in codebase
**When** codebase is scanned
**Then**
- [ ] Zero print() statements remain (use logger instead)
- [ ] All logger.debug/info/warning/error use structlog
- [ ] All logging.getLogger() becomes structlog.get_logger()

**Search targets**:
- `grep -r "print(" src/` — Replace with logger.info()
- `grep -r "logging.getLogger" src/` — Replace with structlog.get_logger()
- `grep -r "logging.debug\|logging.info" src/` — Already structlog

**Pattern**:
```python
# Before
import logging
logger = logging.getLogger(__name__)
logger.info(f"Processing donation from {donor_id}")
print("Donation processed")

# After
import structlog
logger = structlog.get_logger()
logger.info("donation_processed", donor_id=donor_id)
```

### Application-Level Logging

**Given** any significant application action (create, update, delete, error)
**When** action occurs
**Then**
- [ ] Action is logged with: action name, resource_id, user_id, status
- [ ] Log includes context-specific fields (e.g., adoption_request status change)

**Pattern for create**:
```python
@router.post("/donations")
async def create_donation(donation: CreateDonationSchema, current_user: User, db: Session):
    logger = structlog.get_logger()
    logger.info(
        "donation_created",
        donor_id=current_user.id,
        amount_cents=donation.amount_cents,
        currency=donation.currency,
    )
    # Create donation...
```

**Pattern for error**:
```python
try:
    process_payment(donation)
except PaymentError as e:
    logger.error(
        "payment_failed",
        donor_id=donor_id,
        amount_cents=amount_cents,
        error_code=str(e),
        retry=True,
    )
    raise
```

### API Request/Response Logging

**Given** middleware that logs all requests
**When** request is processed
**Then**
- [ ] Every request is logged (in middleware, before routing)
- [ ] Log includes: method, path, status_code, duration_ms, user_id
- [ ] GET requests are logged (volume is acceptable)
- [ ] Response body size is logged (track large responses)

**Log structure**:
```json
{
  "timestamp": "2026-03-27T15:30:45.123Z",
  "level": "INFO",
  "message": "http_request",
  "method": "POST",
  "path": "/donations",
  "status_code": 201,
  "duration_ms": 234,
  "user_id": "user-uuid",
  "request_id": "req-abc123",
  "response_size_bytes": 512
}
```

### Database Operation Logging

**Given** database operations (query, insert, update, delete)
**When** operation completes
**Then**
- [ ] Slow queries are logged (> 100ms)
- [ ] Errors are logged with full context
- [ ] Transaction rollbacks are logged

**Pattern**:
```python
import time

start = time.time()
try:
    result = await db.execute(query)
    duration = (time.time() - start) * 1000
    if duration > 100:
        logger.warning(
            "slow_query",
            duration_ms=duration,
            table="donations",
            operation="select",
        )
except Exception as e:
    logger.error(
        "database_error",
        operation="select",
        error=str(e),
    )
    raise
```

### Notification Logging

**Given** notifications are sent (email, WhatsApp, in-app)
**When** notification is sent or fails
**Then**
- [ ] Successful sends are logged: `{"message": "email_sent", "recipient": "...", "template": "..."}`
- [ ] Failures are logged: `{"message": "email_send_failed", "error": "...", "retry": true}`

### Context Propagation

**Given** async request handling
**When** context (user_id, request_id) is set in middleware
**Then**
- [ ] All downstream loggers have access to context
- [ ] user_id and request_id are included in all logs (not hardcoded)
- [ ] Context is isolated per request (no leakage between concurrent requests)

**Pattern using structlog context**:
```python
# In middleware
structlog.get_logger().context.bind(
    request_id=request_id,
    user_id=current_user.id if current_user else None,
)

# Downstream, context is automatically included
logger.info("donation_created")  # Automatically includes request_id, user_id
```

### Log Levels

All logs use appropriate level:
- **DEBUG** — Detailed diagnostic info (not in production)
- **INFO** — Significant events (user actions, important state changes)
- **WARNING** — Potentially harmful (slow queries, rate limits, retries)
- **ERROR** — Error but app continues (failed email, invalid input)
- **CRITICAL** — Error and app may fail (database down, payment failed)

### No Sensitive Data in Logs

**Given** any log entry
**When** log is generated
**Then**
- [ ] Passwords, tokens, API keys are NOT logged
- [ ] Credit card numbers are NOT logged
- [ ] Email addresses ARE logged (not sensitive in this context)
- [ ] Masking happens at logging point or earlier

**Pattern**:
```python
# Bad — exposes password
logger.info("user_login_failed", email=email, password=password)

# Good — no sensitive data
logger.info("user_login_failed", email=email)
```

### Structured Logging in All Modules

All modules must use structlog:
- `src/api/*.py` — Route handlers
- `src/services/*.py` — Business logic
- `src/db/*.py` — Database operations
- `src/notifications/*.py` — Notification handlers
- `src/auth/*.py` — Authentication
- `src/payments/*.py` — Payment processing

## Definition of Done

- [ ] structlog installed and configured
- [ ] Zero print() statements in source code
- [ ] All logging uses structlog.get_logger()
- [ ] Request/response logging middleware logs all requests
- [ ] All log entries include: timestamp, level, message, context fields
- [ ] user_id and request_id propagated to all logs
- [ ] No sensitive data (passwords, tokens, card numbers) in logs
- [ ] Database operation logging for slow queries (>100ms)
- [ ] Notification logging (success and failures)
- [ ] Code review approved
- [ ] CI pipeline passes

## Technical Notes

### Files to Create
- `src/logging_config.py` — structlog configuration

### Files to Modify
- All files in `src/` with print() or logging calls
- `src/app.py` — Initialize logging_config
- Middleware file — Add request/response logging

### structlog Installation
```bash
pip install structlog
```

### Log Output Format

For development (console):
```
[timestamp] [level] [logger_name] — message — key1=value1 key2=value2
```

For production (JSON):
```json
{"timestamp": "...", "level": "INFO", "message": "...", "key1": "value1", "key2": "value2"}
```

### Testing Structured Logging

Tests should verify logs are emitted (use pytest-structlog or caplog):

```python
def test_donation_created_is_logged(caplog, db_session):
    with caplog.at_level(logging.INFO):
        create_donation(donation_schema, db_session)

    assert "donation_created" in caplog.text
    assert "donor_id" in caplog.text
```

---

*Last updated: 2026-03-27*
