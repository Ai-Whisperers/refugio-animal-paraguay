---
story: RAP-405
epic: EPIC-72
title: "Write tests for password_reset module (0% → 80%+)"
status: ready
priority: 0
points: 5
created: 2026-03-27
---

# RAP-405: Write Tests for Password Reset Module

## Story

As a **developer**, I want **comprehensive tests for the password_reset module** so that **password recovery flows are protected from regressions**.

## Description

The `password_reset` module currently has 0% test coverage. This module handles:
- Token generation and storage (`VerificationToken` model)
- Token expiry validation
- Password update with token verification
- Email dispatch on reset request
- Rate limiting to prevent abuse

All of these need unit and integration tests.

## Acceptance Criteria

### Unit Tests (tests/unit/test_password_reset_service.py)

**Given** a password reset service and valid email
**When** `request_password_reset(email)` is called
**Then**
- [ ] A `VerificationToken` is created in the database
- [ ] Token expires in exactly 24 hours
- [ ] Token is not returned in plain text in any response
- [ ] Email is queued for sending (mocked)
- [ ] Calling twice within 1 hour raises `RateLimitError`

**Given** a valid reset token
**When** `reset_password(token, new_password)` is called
**Then**
- [ ] User password is updated (hash verified)
- [ ] Token is marked as `used=True`
- [ ] Token can no longer be reused (second call raises error)
- [ ] User's old sessions are invalidated (optional: `last_password_changed` updated)

**Given** an expired token
**When** `reset_password(token, new_password)` is called
**Then**
- [ ] `TokenExpiredError` is raised (not generic Exception)
- [ ] No password change occurs
- [ ] Error message is user-friendly (no internal details)

**Given** an invalid token (malformed, nonexistent, wrong user)
**When** `reset_password(token, new_password)` is called
**Then**
- [ ] `InvalidTokenError` is raised
- [ ] No password change occurs
- [ ] No timing leak (same response time for all invalid cases)

**Given** a password reset request with weak password (< 8 chars, no uppercase)
**When** validation is run
**Then**
- [ ] `ValidationError` lists all violations (length, uppercase, number, special)
- [ ] No partial updates occur

### Integration Tests (tests/integration/test_password_reset.py)

**Given** a fresh user account
**When** full password reset flow is executed (request → email dispatch → token verification → password update)
**Then**
- [ ] Email is sent to correct address (mock SMTP)
- [ ] Email contains reset link with correct token
- [ ] Visiting reset link with valid token shows form
- [ ] Submitting new password succeeds
- [ ] Old password no longer works on login
- [ ] New password works on login

**Given** a concurrent request scenario (two reset requests within 1 minute)
**When** both are submitted
**Then**
- [ ] First succeeds
- [ ] Second raises `RateLimitError` with retry_after_seconds

**Given** a reset token that was used
**When** attempting to reset again with the same token
**Then**
- [ ] Request fails with `TokenAlreadyUsedError`
- [ ] No second password change occurs

### Schema & Model Tests (tests/unit/test_password_reset_schemas.py)

**Given** a PasswordResetRequestSchema input
**When** validated with valid email
**Then**
- [ ] Schema accepts it
- [ ] Email is normalized (lowercase, whitespace trimmed)

**Given** invalid email formats
**When** validated
**Then**
- [ ] Schema rejects: "notanemail", "user@", "@domain.com", "user @domain.com"
- [ ] Error messages specify "invalid email format"

**Given** PasswordResetConfirmSchema with mismatched passwords
**When** validated
**Then**
- [ ] Schema rejects it
- [ ] Error message specifies "passwords must match"

## Definition of Done

- [ ] All test files created and passing
- [ ] Coverage report shows password_reset module at ≥ 80%
- [ ] All tests follow AAA pattern (Arrange/Act/Assert)
- [ ] No mocking of internal functions (mock at I/O boundaries only)
- [ ] Tests use pytest fixtures from conftest.py (create new fixtures if needed)
- [ ] Docstrings explain non-obvious test setup
- [ ] No hardcoded timestamps (use freezegun for time-based tests)
- [ ] No skipped tests without documented reason
- [ ] Code review approved
- [ ] CI pipeline passes

## Technical Notes

### Files to Create
- `tests/unit/test_password_reset_service.py` — Service logic tests
- `tests/unit/test_password_reset_schemas.py` — Pydantic schema validation tests

### Files to Create / Enhance
- `tests/integration/test_password_reset.py` — Full flow tests

### Files to Reference
- `src/api/password_reset.py` — Route handlers
- `src/services/password_reset_service.py` — Service logic
- `src/db/models/verification_token.py` — Token model
- `src/db/models/user.py` — User model
- `tests/conftest.py` — Shared fixtures (add new ones here)

### Key Test Utilities

**Fixtures to use/create**:
- `user_factory` — Create test users
- `async_client` — FastAPI test client
- `db_session` — Fresh database session per test
- `mock_smtp` — Mock email sending
- `monkeypatch` (pytest built-in) — Patch rate limiter, time

**Libraries to use**:
- `pytest`, `pytest-asyncio` — Already in dependencies
- `freezegun` — Time-based testing (already in dependencies)
- `unittest.mock.patch` — Mock email service at `src.email_service` boundary

### Example Test Structure

```python
@pytest.mark.asyncio
async def test_request_password_reset_creates_token(user_factory, db_session, mock_smtp):
    # Arrange
    user = user_factory(email="test@example.com")
    db_session.add(user)
    await db_session.commit()

    # Act
    result = await request_password_reset(user.email, db_session)

    # Assert
    token = await db_session.execute(
        select(VerificationToken).where(VerificationToken.user_id == user.id)
    )
    token = token.scalar_one()
    assert token is not None
    assert token.expires_at > datetime.utcnow()
    mock_smtp.send.assert_called_once()
```

### Rate Limiter Mocking

Tests should verify rate limiting works, but mock the Redis/rate limiter for isolation:

```python
def test_rate_limit_on_second_request(user_factory, monkeypatch):
    # Mock rate limiter to return "limit exceeded" on second call
    call_count = 0

    def mock_check_limit(key):
        nonlocal call_count
        call_count += 1
        if call_count > 1:
            raise RateLimitError(retry_after_seconds=3600)

    monkeypatch.setattr("src.services.password_reset.check_rate_limit", mock_check_limit)
    # Test here
```

---

*Last updated: 2026-03-27*
