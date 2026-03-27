---
story: RAP-417
epic: EPIC-74
title: "Improve health check endpoint"
status: ready
priority: 1
points: 3
created: 2026-03-27
---

# RAP-417: Improve Health Check Endpoint

## Story

As an **operations engineer**, I want **comprehensive health checks for all dependencies** so that **I can detect and respond to service degradation quickly**.

## Description

Current `/health` endpoint only checks database connectivity. It must check all critical dependencies: database, migrations, external services (Stripe, SMTP, Twilio), and provide response times.

## Acceptance Criteria

### Health Check Response Format

**Given** GET /health request
**When** health check runs
**Then**
- [ ] Response HTTP 200 if all checks pass
- [ ] Response HTTP 503 if any critical check fails
- [ ] Response format: `{"status": "healthy" | "degraded" | "unhealthy", "checks": {...}, "timestamp": "..."}`

**Response structure**:
```json
{
  "status": "healthy",
  "timestamp": "2026-03-27T15:30:45Z",
  "checks": {
    "database": {
      "status": "ok",
      "response_time_ms": 5
    },
    "migrations": {
      "status": "ok",
      "current_version": "20260327_120000"
    },
    "smtp": {
      "status": "ok",
      "response_time_ms": 120
    },
    "stripe": {
      "status": "ok",
      "response_time_ms": 350
    },
    "twilio": {
      "status": "ok",
      "response_time_ms": 280
    }
  }
}
```

### Database Connectivity Check

**Given** health check runs
**When** database connectivity is tested
**Then**
- [ ] Simple query is executed: `SELECT 1`
- [ ] Response time is measured and included
- [ ] Status is "ok" or "error"
- [ ] If error: error message is included (e.g., "Connection refused")

**Code**:
```python
async def check_database(db: Session) -> dict:
    start = time.time()
    try:
        await db.execute(text("SELECT 1"))
        return {
            "status": "ok",
            "response_time_ms": int((time.time() - start) * 1000),
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
        }
```

### Alembic Migration Check

**Given** health check runs
**When** migration state is checked
**Then**
- [ ] Current migration version is queried from `alembic_version` table
- [ ] Version is compared with latest in codebase
- [ ] Status is "ok" if at head, "outdated" if behind, "error" if issue

**Code**:
```python
async def check_migrations(db: Session) -> dict:
    try:
        # Get current version
        result = await db.execute(text("SELECT version_num FROM alembic_version"))
        current = result.scalar()

        # Compare with latest migration file
        from alembic.script import ScriptDirectory
        from alembic.config import Config
        config = Config("alembic.ini")
        script = ScriptDirectory.from_config(config)
        latest = script.get_current_head()

        if current == latest:
            return {"status": "ok", "current_version": current}
        else:
            return {
                "status": "outdated",
                "current": current,
                "latest": latest,
            }
    except Exception as e:
        return {"status": "error", "error": str(e)}
```

### SMTP (Email Service) Check

**Given** health check runs
**When** SMTP connectivity is tested
**Then**
- [ ] SMTP server connection is attempted
- [ ] Response time is measured
- [ ] Status is "ok" or "error"
- [ ] No email is actually sent (just connect/disconnect)

**Code**:
```python
async def check_smtp() -> dict:
    start = time.time()
    try:
        async with aiosmtplib.SMTP(hostname=SMTP_HOST, port=SMTP_PORT) as smtp:
            await smtp.login(SMTP_USER, SMTP_PASSWORD)
        return {
            "status": "ok",
            "response_time_ms": int((time.time() - start) * 1000),
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(type(e).__name__),
        }
```

### Stripe API Check

**Given** health check runs
**When** Stripe API is tested
**Then**
- [ ] Stripe API is called with a safe operation (list charges with limit=1)
- [ ] Response time is measured
- [ ] Status is "ok" or "error"
- [ ] No charges are created (read-only check)

**Code**:
```python
async def check_stripe() -> dict:
    start = time.time()
    try:
        stripe.Charge.list(limit=1)  # Safe read-only operation
        return {
            "status": "ok",
            "response_time_ms": int((time.time() - start) * 1000),
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(type(e).__name__),
        }
```

### Twilio API Check

**Given** health check runs
**When** Twilio API is tested
**Then**
- [ ] Twilio API is called with a safe operation (get account info)
- [ ] Response time is measured
- [ ] Status is "ok" or "error"

**Code**:
```python
async def check_twilio() -> dict:
    start = time.time()
    try:
        client.api.account.fetch()  # Safe read-only operation
        return {
            "status": "ok",
            "response_time_ms": int((time.time() - start) * 1000),
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(type(e).__name__),
        }
```

### Redis Check (if used)

**Given** health check runs and Redis is in use
**When** Redis connectivity is tested
**Then**
- [ ] PING command is sent to Redis
- [ ] Response time is measured
- [ ] Status is "ok" or "error"

### Overall Status Determination

**Given** all checks complete
**When** overall status is determined
**Then**
- [ ] Status is "healthy" if all checks pass
- [ ] Status is "degraded" if some non-critical checks fail
- [ ] Status is "unhealthy" if database or migrations fail
- [ ] HTTP status code is 200 for healthy/degraded, 503 for unhealthy

**Critical checks** (cause unhealthy):
- Database
- Migrations

**Non-critical checks** (cause degraded):
- SMTP
- Stripe
- Twilio

### Performance Requirements

**Given** health check endpoint is called
**When** all checks run
**Then**
- [ ] Total response time is < 5 seconds
- [ ] Individual check timeouts are set (e.g., 2 seconds per service)
- [ ] Timeout doesn't block other checks

**Code**:
```python
async def health_check():
    checks = {}

    # Run checks concurrently with timeouts
    db_result = asyncio.timeout(2)(check_database(db))
    migration_result = asyncio.timeout(2)(check_migrations(db))
    smtp_result = asyncio.timeout(2)(check_smtp())
    stripe_result = asyncio.timeout(2)(check_stripe())
    twilio_result = asyncio.timeout(2)(check_twilio())

    checks["database"] = await db_result
    checks["migrations"] = await migration_result
    checks["smtp"] = await smtp_result
    checks["stripe"] = await stripe_result
    checks["twilio"] = await twilio_result

    # Determine overall status
    if checks["database"]["status"] == "error" or checks["migrations"]["status"] == "error":
        overall_status = "unhealthy"
    elif any(c["status"] == "error" for c in checks.values()):
        overall_status = "degraded"
    else:
        overall_status = "healthy"

    return {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "checks": checks,
    }
```

### Health Check Logging

**Given** health check is executed
**When** any check fails
**Then**
- [ ] Failure is logged with check name and error
- [ ] Logs are structured (JSON) for easy alerting

**Code**:
```python
logger = structlog.get_logger()
logger.info(
    "health_check_completed",
    overall_status=status,
    database_status=checks["database"]["status"],
    migrations_status=checks["migrations"]["status"],
)
```

### Exclude From Metrics/Logs

Health check requests should not be logged in request metrics (too noisy):

**In middleware**:
```python
if request.url.path == "/health":
    # Skip logging for health checks
    return await call_next(request)
```

## Definition of Done

- [ ] Health check endpoint checks: database, migrations, SMTP, Stripe, Twilio
- [ ] Each check includes response time
- [ ] Overall status is "healthy" | "degraded" | "unhealthy"
- [ ] HTTP 200 for healthy/degraded, 503 for unhealthy
- [ ] All checks run concurrently with timeouts
- [ ] Total response time < 5 seconds
- [ ] Failures are logged for alerting
- [ ] Health check requests excluded from metrics
- [ ] Code review approved
- [ ] CI pipeline passes

## Technical Notes

### Endpoint
`GET /health` — Health check (excludes request logging)
`GET /health/detailed` — Detailed health info (optional)

### Test Health Check

```bash
curl http://localhost:8000/health
```

---

*Last updated: 2026-03-27*
