---
epic: EPIC-73
title: "Exception Handling & Validation Hardening"
status: ready
priority: 95
sprint: priority
version: V3.1
points: 16
created: 2026-03-27
---

# EPIC-73: Exception Handling & Validation Hardening

## Overview

**Goal**: Replace all bare `except Exception` with specific exceptions, add missing input validation, ensure consistent error responses across all API endpoints.

**Why it matters**: Bare exception handlers hide bugs, make debugging difficult, and don't provide specific error information to clients. Missing validation allows invalid data into the system. Inconsistent error responses confuse clients.

**Target users**: API clients, developers, system operators.

## Scope

### In Scope
- Replace 14+ bare `except Exception` clauses with specific exceptions
- Audit and fix API input validation gaps (email, phone, amounts, enums)
- Standardize error responses across all 27 routers
- Add database constraint error handling (IntegrityError, ForeignKeyError)
- Harden payment error handling (Stripe, Tigo Money)

### Out of Scope
- End-to-end error scenario testing (covered by EPIC-72)
- UI error display/messaging (frontend work)
- Error monitoring/alerting (covered by EPIC-74)

## Features

- [ ] RAP-410: Replace bare except clauses in notification handlers — 3 pts
- [ ] RAP-411: Audit and fix API input validation gaps — 3 pts
- [ ] RAP-412: Standardize error responses across all routers — 3 pts
- [ ] RAP-413: Add database constraint error handling — 3 pts
- [ ] RAP-414: Harden payment error handling (Stripe + Tigo) — 4 pts

## Dependencies

- Depends on: Quality Standards (error handling rules)
- Blocks: V3.1 release; production stability
- Related: EPIC-72 (test coverage for exceptions)

## Key Decisions Made

1. **Exception hierarchy**: Create `src/exceptions.py` with specific exception classes
2. **Error response format**: Standard `{"detail": "message", "error_code": "CODE"}` across all endpoints
3. **Validation approach**: Pydantic schemas for input validation, custom validators for complex rules
4. **Logging**: Structured logging with WHAT/WHY/HOW format (see EPIC-74)
5. **Payment errors**: Map third-party errors to internal types for consistency

## Risks

- **Risk**: Existing code relies on bare Exception catching
  → **Mitigation**: New exceptions inherit from BaseException; backwards compatible

- **Risk**: Many places to update; easy to miss one
  → **Mitigation**: Search codebase for `except Exception` before starting

---

## Acceptance Criteria (Epic Level)

The epic is complete when:

- [ ] All 5 stories merged to develop
- [ ] Zero bare `except Exception` in codebase (all replaced with specific exceptions)
- [ ] All API endpoints validate input (email, phone, amounts, enums)
- [ ] All error responses follow standard format: `{"detail": "...", "error_code": "..."}`
- [ ] Database constraint errors properly caught and converted to HTTP 4xx/5xx
- [ ] Payment errors from Stripe/Tigo mapped to user-friendly messages
- [ ] Linting passes (no unused imports, proper exception hierarchy)
- [ ] All new tests pass (from EPIC-72)

---

## Definition of Done (Epic)

- [ ] All user stories complete and merged
- [ ] All acceptance criteria checked
- [ ] Code review approved by secondary reviewer
- [ ] Version bumped in `pyproject.toml`
- [ ] CHANGELOG.md updated with summary
- [ ] Deployed to staging and verified

---

*Last updated: 2026-03-27*
*Owner: Error Handling Squad*
