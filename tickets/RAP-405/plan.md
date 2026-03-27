# RAP-405 Plan

## Objective
Write comprehensive tests for the password_reset module to bring coverage from 0% to 80%+.

## Description
The password reset module (service + API + schemas) currently has 0% unit test coverage. Integration tests exist but are minimal. This ticket adds unit tests for the service layer and schema validation, and enhances integration tests to cover the full reset flow, token reuse, expired tokens, and edge cases.

## Acceptance Criteria
- [ ] Unit tests for password_reset_service.py (create token, validate token, reset password)
- [ ] Unit tests for password_reset schemas (email validation, password confirm matching)
- [ ] Integration tests enhanced (full flow, token reuse, expired token, concurrent requests)
- [ ] Coverage for password_reset module >= 80%
- [ ] All tests follow AAA pattern
- [ ] No mocking of internal functions (mock at I/O boundaries only)
- [ ] All tests pass with zero warnings

## Complexity Assessment
**Track**: Simple Fix

### Simple Fix Criteria
- [x] Single, clear root cause identified (missing tests)
- [x] Solution affects ≤3 files (3 test files)
- [ ] Change impact ≤10 lines of actual code (will be more, but all test code)
- [x] Low risk of side effects
- [x] Solution pattern is well-understood

**Assessment result**: Complex (due to volume of test code) but low-risk — phased approach: unit tests first, then integration.

## Approach
1. Create `tests/unit/test_password_reset_service.py` — service logic tests with mocked DB
2. Create `tests/unit/test_password_reset_schemas.py` — Pydantic schema validation tests
3. Enhance `tests/integration/test_password_reset.py` — token reuse, expired tokens, old password invalidation

## Dependencies
- Depends on: RAP-101 (PR #62 — now merged)
- Blocked by: None

## Risks
- Risk: Rate limiter interference in tests → Mitigation: Already disabled globally via conftest
