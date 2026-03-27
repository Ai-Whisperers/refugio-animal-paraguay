---
epic: EPIC-74
title: "Logging, Monitoring & Observability"
status: ready
priority: 90
sprint: priority
version: V3.1
points: 19
created: 2026-03-27
---

# EPIC-74: Logging, Monitoring & Observability

## Overview

**Goal**: Add structured logging, error tracking, and database backup automation so production issues are visible and data is safe.

**Why it matters**: Without observability, bugs in production are invisible. Without backups, data loss is catastrophic. Both are critical for V3.1 stability.

**Target users**: Operations team, developers, system administrators.

## Scope

### In Scope
- Structured JSON logging using structlog (replace print and basic logging)
- Error tracking integration with Sentry
- Enhanced health check endpoint with dependency status
- Request/response logging middleware with sensitive field masking
- Automated daily database backups with 30-day retention

### Out of Scope
- Custom Grafana dashboards (use Sentry/logs UI)
- APM instrumentation beyond Sentry (no New Relic, DataDog)
- Log analysis tools (use Sentry for errors, basic grep for logs)
- Email alerts (can be added later)

## Features

- [ ] RAP-415: Add structured JSON logging (structlog) — 5 pts
- [ ] RAP-416: Integrate Sentry error tracking — 3 pts
- [ ] RAP-417: Improve health check endpoint — 3 pts
- [ ] RAP-418: Add request/response logging middleware — 3 pts
- [ ] RAP-419: Set up automated database backups — 5 pts

## Dependencies

- Depends on: EPIC-73 (error handling for structured logging context)
- Blocks: V3.1 release; production deployment
- Related: EPIC-72 (tests will verify logging)

## Key Decisions Made

1. **Logging framework**: structlog (JSON-native, async-friendly)
2. **Error tracking**: Sentry (standard in Python ecosystem)
3. **Backup strategy**: pg_dump daily, gzip, 30-day retention
4. **Backup location**: `/opt/backups/` on VPS
5. **Log output**: Structured JSON to stdout (Docker captures to logs)

## Risks

- **Risk**: Structured logging is new — team learning curve
  → **Mitigation**: Provide examples, update docs, pair on first implementation

- **Risk**: Sentry quota exceeded by verbose logging
  → **Mitigation**: Sample errors (10% of requests), exclude health checks

---

## Acceptance Criteria (Epic Level)

The epic is complete when:

- [ ] All 5 stories merged to develop
- [ ] All application logs are structured JSON
- [ ] No print() or basic logger calls remain
- [ ] Sentry captures all errors with user context
- [ ] Health check endpoint returns status of all dependencies
- [ ] Request logging includes method, path, status_code, duration, user_id
- [ ] Database backups run daily and are verified
- [ ] All acceptance criteria met
- [ ] Code review approved
- [ ] Deployed to staging and verified

---

## Definition of Done (Epic)

- [ ] All user stories complete and merged
- [ ] All acceptance criteria checked
- [ ] Code review approved by secondary reviewer
- [ ] CHANGELOG.md updated
- [ ] Version bumped in `pyproject.toml`
- [ ] Deployed to staging with monitoring enabled
- [ ] Team briefed on new logging format

---

*Last updated: 2026-03-27*
*Owner: Observability Squad*
