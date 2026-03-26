# RAP-018 Plan

## Objective
Implement a comprehensive audit trail system that records all authenticated actions for GDPR Article 30 compliance.

## Description
The shelter needs a tamper-evident log of every authenticated action (create, update, delete) for compliance and accountability. The audit trail captures who did what, when, to which resource, and from where (IP/user agent). Admin/compliance users can query, filter, and export the audit log.

## Acceptance Criteria
- [ ] FastAPI middleware records all authenticated POST/PUT/PATCH/DELETE requests
- [ ] AuditLog model stores user_id, action, resource_type, resource_id, timestamp, ip_address, user_agent
- [ ] Admin-only GET /audit-logs endpoint with filtering (user, action, resource_type, date range)
- [ ] GET /audit-logs/export endpoint returns CSV of filtered results
- [ ] No sensitive data (passwords, tokens) recorded in audit logs
- [ ] Unit tests cover middleware logic and audit log creation (80%+ coverage)
- [ ] Integration tests verify audit trail for 5+ critical action types
- [ ] Proper database indexes on (user_id, timestamp), (resource_type, resource_id, timestamp), (timestamp)

## Complexity Assessment
**Track**: Complex Implementation

### Simple Fix Criteria (ALL must be met)
- [ ] Single, clear root cause identified — N/A (new feature)
- [x] Solution affects <=3 files — NO (7+ files)
- [ ] Change impact <=10 lines — NO (300+ lines)
- [ ] Low risk of side effects — Middleware touches all requests
- [ ] Solution pattern is well-understood — Yes

**Assessment result**: Complex — multiple files (model, migration, middleware, API, schemas, tests), middleware affects all request processing.

## Approach

### Phase 1: Data Layer
- AuditLog ORM model with AuditAction and ResourceType enums
- Alembic migration 005 (on develop branch, 005 slot is free)

### Phase 2: Middleware
- FastAPI middleware that intercepts authenticated requests
- Extracts user_id from JWT, action from HTTP method, resource from URL path
- Writes audit record after response (fire-and-forget via event bus)

### Phase 3: Query API
- GET /audit-logs — paginated, filterable by user_id, action, resource_type, resource_id, date range
- GET /audit-logs/export — CSV download of filtered results
- Admin-only access

### Phase 4: Tests
- Unit tests for middleware logic, path parsing, action mapping
- Integration tests for 5+ action types (create animal, update animal, delete animal, create adopter, approve adoption)

## Dependencies
- Depends on: JWT auth system (RAP-007, done), Event Bus (RAP-017, done)
- Blocks: S02-gdpr-data-management

## Risks
- Risk: Middleware adds latency to every request -> Mitigation: fire-and-forget via event bus, async DB write
- Risk: Audit table grows large -> Mitigation: proper indexes, pagination, future retention policy
