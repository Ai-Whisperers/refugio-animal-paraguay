---
story: RAP-416
epic: EPIC-74
title: "Integrate Sentry error tracking"
status: ready
priority: 0
points: 3
created: 2026-03-27
---

# RAP-416: Integrate Sentry Error Tracking

## Story

As a **developer**, I want **automatic error tracking with Sentry** so that **production exceptions are captured, grouped, and alerted**.

## Description

Production errors need centralized tracking. Sentry captures exceptions, groups similar errors, tracks occurrence trends, and enables alerting. Configuration placeholder exists in `.env.example` (SENTRY_DSN).

## Acceptance Criteria

### Install & Configure Sentry

**Given** the application starts
**When** SENTRY_DSN env var is set
**Then**
- [ ] `sentry-sdk[fastapi]` is installed
- [ ] Sentry is initialized in `src/app.py`
- [ ] Sentry middleware is added to FastAPI app
- [ ] SENTRY_DSN is read from environment
- [ ] Errors are sent to Sentry project

**Code example**:
```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

sentry_sdk.init(
    dsn=settings.SENTRY_DSN,
    integrations=[
        FastApiIntegration(),
        SqlalchemyIntegration(),
    ],
    environment=settings.ENVIRONMENT,  # "development", "staging", "production"
    traces_sample_rate=0.1,  # Sample 10% of transactions for performance monitoring
)
```

### Capture Errors Automatically

**Given** any unhandled exception in request handler
**When** exception occurs
**Then**
- [ ] Exception is automatically captured by Sentry middleware
- [ ] Error includes: stack trace, request context, environment
- [ ] Duplicate errors are grouped by fingerprint
- [ ] First occurrence creates an issue; subsequent are grouped

### Add User Context

**Given** authenticated user making request
**When** error occurs
**Then**
- [ ] Sentry capture includes user_id, email, or username
- [ ] Sentry groups errors by user (to identify affected users)

**Code example**:
```python
from sentry_sdk import set_user

@router.get("/animals")
async def list_animals(current_user: User):
    set_user({"id": current_user.id, "email": current_user.email})
    # Handler code
```

### Performance Monitoring

**Given** request is processed
**When** request completes
**Then**
- [ ] Request is traced in Sentry (method, path, duration, status_code)
- [ ] Slow requests are flagged (> 1 second)
- [ ] Database queries are tracked
- [ ] Performance data is viewable in Sentry dashboard

**Configuration**:
```python
sentry_sdk.init(
    traces_sample_rate=0.1,  # 10% of requests (not 100% to control quota)
)
```

### Exception Filtering

**Given** non-critical exceptions (e.g., 404 Not Found)
**When** exception occurs
**Then**
- [ ] 404 errors are NOT sent to Sentry (too noisy)
- [ ] 401/403 errors are NOT sent (expected)
- [ ] Validation errors (422) are logged but NOT sent
- [ ] Only 5xx and unexpected 4xx are captured

**Configuration**:
```python
def before_send(event, hint):
    """Filter which errors to send to Sentry."""
    if event.get("transaction") and "health" in event["transaction"]:
        return None  # Don't send health check errors
    status = event.get("response", {}).get("status_code")
    if status in [401, 403, 404, 422]:
        return None  # Expected errors, don't send
    return event

sentry_sdk.init(
    ...,
    before_send=before_send,
)
```

### Release Tracking

**Given** new version deployed
**When** version is released
**Then**
- [ ] Sentry knows about new release
- [ ] Errors are tracked per release (to identify regressions)
- [ ] Release version comes from git tag or `src/__version__.py`

**Code example**:
```python
sentry_sdk.init(
    ...,
    release=f"refugio-animal-paraguay@{VERSION}",
)
```

### Verify Sentry Connection

**Given** application is running
**When** Sentry is configured
**Then**
- [ ] A test error can be manually sent: `sentry_sdk.capture_exception(...)`
- [ ] Error appears in Sentry dashboard within 5 minutes
- [ ] No errors in logs about Sentry connectivity

**Test**:
```python
# In a management command or test
import sentry_sdk
sentry_sdk.capture_exception(Exception("Test error from Refugio Animal Paraguay"))
```

## Definition of Done

- [ ] sentry-sdk installed
- [ ] Sentry initialized in `src/app.py` with FastAPI integration
- [ ] SENTRY_DSN read from environment
- [ ] Non-critical errors filtered (404, 401, 403, 422)
- [ ] User context set on errors
- [ ] Performance monitoring configured (10% trace sample rate)
- [ ] Release version tracked
- [ ] Test error sent and verified in Sentry dashboard
- [ ] Code review approved
- [ ] CI pipeline passes

## Technical Notes

### Installation
```bash
pip install sentry-sdk[fastapi]
```

### Environment Variable
Add to `.env` and `.env.example`:
```
SENTRY_DSN=https://[key]@o[org].ingest.sentry.io/[project]
```

### Settings Configuration
```python
# src/config.py
from pydantic import Field

class Settings:
    SENTRY_DSN: str = Field(default="", env="SENTRY_DSN")
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
```

### Sentry Dashboard
- Organization: Set up on sentry.io
- Project: Create Refugio Animal Paraguay project
- Share SENTRY_DSN with team

---

*Last updated: 2026-03-27*
