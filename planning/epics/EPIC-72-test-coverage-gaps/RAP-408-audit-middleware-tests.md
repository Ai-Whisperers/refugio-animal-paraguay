---
story: RAP-408
epic: EPIC-72
title: "Add audit middleware tests"
status: ready
priority: 1
points: 3
created: 2026-03-27
---

# RAP-408: Add Audit Middleware Tests

## Story

As a **developer**, I want **comprehensive tests for the audit middleware** so that **audit logging is reliable and sensitive data is properly masked**.

## Description

The audit middleware (`src/audit/middleware.py`) logs all requests for compliance and debugging. Current coverage is ~30%. Tests must verify:

1. All POST/PATCH/DELETE requests are logged
2. GET requests are NOT logged (to reduce log volume)
3. User context (user_id, email) is captured
4. Sensitive fields are masked (passwords, tokens, card numbers)
5. Request IDs are propagated correctly
6. Audit logs include method, path, status_code, duration_ms

## Acceptance Criteria

### Request Logging Tests (tests/unit/test_audit_middleware_logging.py)

**Given** a POST request to `/adoptions`
**When** middleware processes the request
**Then**
- [ ] Audit log is created with: method=POST, path=/adoptions, status_code
- [ ] Log includes duration_ms (request time)
- [ ] Log includes request_id (X-Request-ID header or generated UUID)
- [ ] Log includes authenticated user_id (if user is logged in)
- [ ] Log is written to audit log file or service

**Given** a GET request to `/animals`
**When** middleware processes the request
**Then**
- [ ] No audit log is created (GET requests not logged)
- [ ] Request is still processed normally

**Given** a PATCH request to `/donors/{id}`
**When** middleware processes the request
**Then**
- [ ] Audit log is created with method=PATCH
- [ ] Request body is logged (or logged selectively)
- [ ] Payload size is reasonable (large bodies not bloated)

**Given** a DELETE request to `/adoption_requests/{id}`
**When** middleware processes the request
**Then**
- [ ] Audit log is created with method=DELETE
- [ ] Log includes: user_id (who deleted), resource_id (what was deleted)
- [ ] Log is marked as CRITICAL or HIGH severity (destructive operation)

**Given** a request without authentication
**When** middleware processes the request
**Then**
- [ ] Audit log is created
- [ ] user_id field is null or "anonymous"
- [ ] No error is raised (authentication checked elsewhere)

**Given** a request with X-Request-ID header set
**When** middleware processes the request
**Then**
- [ ] Audit log includes the same request_id
- [ ] request_id is propagated to logs and downstream services

**Given** a request without X-Request-ID header
**When** middleware processes the request
**Then**
- [ ] Middleware generates a unique UUID as request_id
- [ ] request_id is stored in context for downstream services
- [ ] request_id appears in response headers (X-Request-ID)

### Sensitive Field Masking Tests (tests/unit/test_audit_middleware_masking.py)

**Given** a POST request with password field in body
**When** body is logged
**Then**
- [ ] password field is masked: `"password": "***"`
- [ ] Original password is never logged
- [ ] Field name is still visible (for debugging)

**Given** a request with card number in body
**When** body is logged
**Then**
- [ ] card_number is masked: `"card_number": "****1234"` (last 4 digits visible)
- [ ] Full card number never appears in logs
- [ ] Cardholder name is NOT masked (not sensitive)

**Given** a request with token field (auth, verification)
**When** body is logged
**Then**
- [ ] token field is masked: `"token": "***"`
- [ ] Token prefix may be visible for debugging (first 3 chars): `"token": "abc***"`

**Given** a request with email field
**When** body is logged
**Then**
- [ ] email field IS logged (email is not considered sensitive for audit)
- [ ] Full email appears in logs

**Given** a request with nested objects containing sensitive fields
**When** body is logged
**Then**
- [ ] Masking applies recursively: `{"donor": {"password": "***"}}`
- [ ] All nesting levels are processed

**Given** a request with array of objects containing sensitive fields
**When** body is logged
**Then**
- [ ] Masking applies to all array elements
- [ ] Example: `[{"password": "***"}, {"password": "***"}]`

### Performance Tests (tests/unit/test_audit_middleware_performance.py)

**Given** a large request body (10KB)
**When** middleware processes it
**Then**
- [ ] Processing overhead is minimal (<10ms added)
- [ ] Large bodies are truncated in logs if needed
- [ ] Middleware does not block request processing

**Given** middleware with database writes for audit logs
**When** database is slow or unavailable
**Then**
- [ ] Request is NOT blocked waiting for audit log write
- [ ] Audit log write happens asynchronously (fire-and-forget)
- [ ] Request still completes normally

**Given** concurrent requests (10 simultaneous)
**When** all are processed
**Then**
- [ ] request_ids are unique for each
- [ ] Audit logs don't interfere with each other
- [ ] All requests complete

### Integration Tests (tests/integration/test_audit_middleware_flow.py)

**Given** a workflow: create donor → update donation → delete donation
**When** all requests pass through middleware
**Then**
- [ ] All 3 operations are logged (POST, PATCH, DELETE)
- [ ] user_id is consistent across all logs
- [ ] request_ids are unique
- [ ] Sensitive fields (if any) are masked in all logs

**Given** authentication failure (invalid token)
**When** request reaches middleware
**Then**
- [ ] Audit log is still created (attempt is logged)
- [ ] Log includes: attempted user_id (if extractable), failure reason
- [ ] Request proceeds to auth handler (which returns 401)

**Given** request to endpoint that doesn't exist (404)
**When** middleware processes it
**Then**
- [ ] Audit log is created with status_code=404
- [ ] Log shows attempted path
- [ ] No error in audit logging

### Context Propagation Tests (tests/unit/test_audit_middleware_context.py)

**Given** middleware sets user_id in request context
**When** downstream handler accesses context.user_id
**Then**
- [ ] user_id is available and correct
- [ ] Context persists across async boundaries

**Given** request with X-Request-ID header
**When** middleware propagates it via context
**Then**
- [ ] Downstream code can access it: `context.request_id`
- [ ] Same request_id appears in audit logs
- [ ] Same request_id appears in application logs (if using structlog)

**Given** multiple concurrent requests with different request_ids
**When** each is processed
**Then**
- [ ] Context is properly isolated (no cross-contamination)
- [ ] Each request's logs have correct request_id
- [ ] No context leakage between requests

### Error Handling Tests (tests/unit/test_audit_middleware_errors.py)

**Given** middleware with exception in request handler
**When** handler raises an exception
**Then**
- [ ] Middleware still logs the request (before exception)
- [ ] status_code is set correctly (500, etc.)
- [ ] Exception doesn't prevent audit logging
- [ ] Audit log includes error information

**Given** middleware with misconfigured masking rules
**When** invalid mask pattern is provided
**Then**
- [ ] Middleware logs warning but doesn't crash
- [ ] Request is still processed
- [ ] Audit logging falls back to safe default (mask everything by default)

## Definition of Done

- [ ] All test files created and passing
- [ ] Coverage report shows audit middleware at ≥ 80%
- [ ] Masking rules tested for all sensitive field patterns
- [ ] Performance overhead measured and acceptable (<10ms)
- [ ] Context propagation verified across async boundaries
- [ ] Code review approved
- [ ] CI pipeline passes

## Technical Notes

### Files to Reference
- `src/audit/middleware.py` — Main audit middleware
- `src/audit/models.py` — AuditLog model (if exists)
- `src/config.py` — Configuration for audit logging

### Files to Create
- `tests/unit/test_audit_middleware_logging.py`
- `tests/unit/test_audit_middleware_masking.py`
- `tests/unit/test_audit_middleware_performance.py`
- `tests/unit/test_audit_middleware_context.py`
- `tests/unit/test_audit_middleware_errors.py`
- `tests/integration/test_audit_middleware_flow.py`

### Masking Rules Configuration

Create a configuration dict (in `src/audit/config.py`) defining sensitive fields:

```python
SENSITIVE_FIELDS = {
    "password": "***",
    "token": "***",
    "verification_token": "***",
    "card_number": "****{last4}",  # Show last 4 digits
    "cvv": "***",
    "stripe_token": "***",
    "api_key": "***",
}

# Fields that are safe to log (whitelist if needed)
PUBLIC_FIELDS = {
    "email",
    "phone_number",
    "name",
    "status",
    "created_at",
}
```

### Testing Masking with Fixtures

```python
@pytest.fixture
def mask_test_data():
    """Provides test payloads with sensitive fields."""
    return {
        "password_in_root": {
            "email": "user@example.com",
            "password": "SecurePassword123!",
        },
        "nested_password": {
            "user": {
                "name": "John",
                "password": "SecurePassword123!",
            },
        },
        "array_passwords": [
            {"password": "pass1"},
            {"password": "pass2"},
        ],
    }

def test_mask_root_level_password(mask_test_data):
    masked = mask_payload(mask_test_data["password_in_root"])
    assert masked["password"] == "***"
    assert masked["email"] == "user@example.com"  # Not masked
```

### Testing Request ID Propagation

```python
@pytest.mark.asyncio
async def test_request_id_propagation(async_client):
    # Send request with custom request_id
    response = await async_client.post(
        "/adoptions",
        headers={"X-Request-ID": "test-request-123"},
        json={"adopter_id": "...", "animal_id": "..."},
    )

    # Verify request_id is in response headers
    assert response.headers["X-Request-ID"] == "test-request-123"

    # Verify audit log has same request_id
    audit_log = await db.query(AuditLog).filter_by(
        request_id="test-request-123"
    ).first()
    assert audit_log is not None
```

### Testing Context Isolation

```python
@pytest.mark.asyncio
async def test_context_isolation_concurrent_requests(async_client):
    # Fire two concurrent requests with different request_ids
    task1 = async_client.get(
        "/animals",
        headers={"X-Request-ID": "req-1"},
    )
    task2 = async_client.get(
        "/animals",
        headers={"X-Request-ID": "req-2"},
    )

    resp1, resp2 = await asyncio.gather(task1, task2)

    # Verify each got its own request_id
    assert resp1.headers["X-Request-ID"] == "req-1"
    assert resp2.headers["X-Request-ID"] == "req-2"

    # Verify logs have correct request_ids (no cross-contamination)
    log1 = await db.query(AuditLog).filter_by(request_id="req-1").first()
    log2 = await db.query(AuditLog).filter_by(request_id="req-2").first()
    assert log1 is not None
    assert log2 is not None
```

---

*Last updated: 2026-03-27*
