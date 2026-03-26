# Task T03: Integration Testing and Validation
**Epic**: EPIC-11 — Public Portal
**Story**: S03 — About and Educational Pages
**Task**: T03 — Integration Testing and Validation
**Status**: `planning`
**Created**: 2026-03-25

---

## Objective

Implement comprehensive integration tests validating the complete content delivery system (T01 + T02), verify database schema integrity, confirm caching behavior under load, and establish validation checklist for production readiness.

---

## Description

This task ensures T01 (public endpoints) and T02 (admin endpoints) work correctly together through the full content lifecycle: creation → editing → publishing → retrieval → caching → archiving. Integration tests bridge the gap between unit tests and end-to-end user journeys, validating real PostgreSQL interactions, cache behavior, audit logging, and permission enforcement.

---

## Acceptance Criteria

### Database Schema Validation (Mandatory)

- [ ] Portal_content table created with all columns: id, page_type, language_code, title, subtitle, content, published, published_at, created_by_user_id, created_at, updated_by_user_id, updated_at
- [ ] UNIQUE constraint (page_type, language_code, published) enforced and tested
- [ ] FAQ_entries table created with all columns: id, page_id, question, answer, category, display_order, published, created_by_user_id, created_at, updated_by_user_id, updated_at
- [ ] Composite indexes exist: idx_portal_content_page_type_published, idx_portal_content_language, idx_portal_content_published_at, idx_faq_entries_page_id, idx_faq_entries_category, idx_faq_entries_published
- [ ] Audit log tables exist: portal_content_audit_log, faq_entries_audit_log with id, entity_id, action, action_by, action_at, change_summary, ip_address, created_at columns
- [ ] Foreign key constraints valid: created_by_user_id, updated_by_user_id reference users.id; page_id references portal_content.id
- [ ] Database schema migration file created (Alembic) and verified against existing schema
- [ ] Schema migration passes: `alembic upgrade head` without errors
- [ ] Rollback verified: `alembic downgrade -1` and `alembic upgrade head` succeed idempotently

### Content Lifecycle Integration Tests (High Priority)

#### Create → Publish → Retrieve Flow
- [ ] Admin creates draft content via POST /api/v1/admin/content with page_type=about, language=es
- [ ] Draft content NOT visible via GET /api/v1/content/about (published=false)
- [ ] Admin publishes content via POST /api/v1/admin/content/{id}/publish
- [ ] Content immediately visible via GET /api/v1/content/about
- [ ] Cache invalidated: request after publish has X-Cache: MISS header
- [ ] Response time <1000ms on first request (uncached)
- [ ] Audit log records create action with action_by=user_id, change_summary includes initial content
- [ ] Audit log records publish action with change_summary includes publish reason (if provided)

#### Edit → Re-publish → Retrieve Flow
- [ ] Published content retrieved via GET /api/v1/content/about (X-Cache: MISS on first call)
- [ ] Second GET request returns cached (X-Cache: HIT, response_time <500ms)
- [ ] Admin edits content via PATCH /api/v1/admin/content/{id} with new title
- [ ] Changes NOT visible via public GET (old cached version served)
- [ ] Cache invalidated when PATCH succeeds (next GET = MISS)
- [ ] Audit log records edit with updated_by, change_summary shows field changes
- [ ] Version field incremented (tested via separate read)

#### Scheduled Publishing
- [ ] Admin publishes with scheduled_at=future_time via POST /api/v1/admin/content/{id}/publish?scheduled_at=2026-03-26T10:00:00Z
- [ ] Content remains unpublished (GET returns 404 or cached old version)
- [ ] Background job executes at scheduled time
- [ ] Content becomes visible after scheduled time
- [ ] Audit log records scheduled publish action with scheduled_at timestamp

#### Archive → Retrieve Flow
- [ ] Published content archived via POST /api/v1/admin/content/{id}/archive
- [ ] Content NOT visible via GET /api/v1/content/about (404)
- [ ] Cache invalidated
- [ ] Database record still exists (published=false, soft-delete confirmed)
- [ ] Audit log records archive action with reason

### Multilingual Content Delivery (High Priority)

- [ ] Three language versions created: es (Spanish), nl (Dutch), en (English)
- [ ] GET /api/v1/content/about?language=es returns Spanish version with language=es
- [ ] GET /api/v1/content/about?language=nl returns Dutch version with language=nl
- [ ] GET /api/v1/content/about?language=en returns English version with language=en
- [ ] GET /api/v1/content/about (no language param) returns Spanish (default fallback)
- [ ] GET /api/v1/content/about?language=invalid returns 400 with error_code=INVALID_LANGUAGE_CODE
- [ ] Each language cached independently: es and nl versions not mixed
- [ ] Cache keys include language: content_about_es, content_about_nl, content_about_en
- [ ] Language-specific cache invalidation: publishing nl version invalidates only nl cache, es cache unaffected

### Caching Behavior Under Load (High Priority)

- [ ] Cache TTL set to 300 seconds for all endpoints
- [ ] First request (cache miss): response_time 500-1000ms, X-Cache: MISS
- [ ] Second request within 300s (cache hit): response_time <500ms, X-Cache: HIT
- [ ] Request after 300s TTL expiry: response_time 500-1000ms (cache miss, re-fetched)
- [ ] Cache hit ratio >90% in load test (100 requests to same endpoint over 30s)
- [ ] Concurrent requests to same cached content: all but first wait for cache population, no thundering herd
- [ ] Cache invalidation on publish: X-Cache: HIT before publish, X-Cache: MISS after publish
- [ ] Memory usage stable: cache size <50MB for 100 cached pages

### Authorization and Permission Enforcement (High Priority)

- [ ] Adopter role cannot access POST/PATCH /api/v1/admin/content (403)
- [ ] Volunteer role cannot access POST/PATCH /api/v1/admin/content (403)
- [ ] Staff role can POST /api/v1/admin/content (create draft) but cannot publish (403 on POST /publish)
- [ ] Staff can PATCH own draft content but cannot PATCH admin-owned content (403)
- [ ] Admin role can POST, PATCH, publish, archive all content (200s)
- [ ] Anonymous (no JWT) cannot access /api/v1/admin/* endpoints (401)
- [ ] Expired JWT on /api/v1/admin/content returns 401 with error_code=TOKEN_EXPIRED
- [ ] Rate limiting enforced: POST /api/v1/admin/content at 10 req/min limit, 11th request returns 429
- [ ] Rate limiting per user: two authenticated users each get 10 requests before hitting 429

### FAQ Management Integration (Medium Priority)

- [ ] FAQ entries created via POST /api/v1/admin/faq with category=adoption_process
- [ ] FAQ entries linked to parent content (page_id references portal_content.id)
- [ ] FAQ entries published and visible via GET /api/v1/content/adoption-process (includes faq_entries array)
- [ ] FAQ cache invalidation: publishing FAQ invalidates parent content cache
- [ ] FAQ edit via PATCH /api/v1/admin/faq/{id} works with same auth rules (staff draft, admin publish)
- [ ] FAQ archive removes from public GET response but maintains soft-delete record

### Error Handling and Recovery (Medium Priority)

- [ ] Database connection error (PostgreSQL down) returns 503 with Retry-After: 60 header
- [ ] Validation error (content exceeds 50KB) returns 400 with error_code=CONTENT_TOO_LARGE
- [ ] Not found (GET /api/v1/content/nonexistent) returns 404 with error_code=PAGE_NOT_FOUND
- [ ] Concurrent edit conflict (PATCH with stale version) returns 409 with error_code=VERSION_CONFLICT
- [ ] Missing required field (POST without title) returns 400 with field-level error_details
- [ ] Rate limit exceeded returns 429 with Retry-After: 60 header
- [ ] All errors logged: logger.error() called with error_code, user_id, context
- [ ] No sensitive data in error responses: database schema not exposed, internal IPs not revealed

### Audit Logging Completeness (Medium Priority)

- [ ] Every POST /api/v1/admin/content creates audit_log entry with action=CREATE
- [ ] Every PATCH /api/v1/admin/content/{id} creates audit_log entry with action=UPDATE
- [ ] Every POST /api/v1/admin/content/{id}/publish creates audit_log entry with action=PUBLISH
- [ ] Every POST /api/v1/admin/content/{id}/archive creates audit_log entry with action=ARCHIVE
- [ ] Audit entries include: content_id, action, action_by (user_id), action_at (ISO timestamp), change_summary (JSON), ip_address
- [ ] change_summary includes field-level changes: {title: {old: "...", new: "..."}, content: {old: "...", new: "..."}}
- [ ] ip_address correctly extracted from X-Forwarded-For or connection.remote_addr
- [ ] Audit logs immutable: no UPDATE or DELETE on audit_log table (append-only)
- [ ] Audit logs queryable: SELECT * FROM portal_content_audit_log WHERE action='PUBLISH' returns all publishes

### Performance Validation (Medium Priority)

- [ ] GET /api/v1/content/about (cached): <500ms, p95 <600ms under 100 concurrent users
- [ ] GET /api/v1/content/about (uncached): <1000ms, p95 <1200ms
- [ ] POST /api/v1/admin/content: <500ms, p95 <700ms
- [ ] PATCH /api/v1/admin/content/{id}: <500ms, p95 <700ms
- [ ] POST /api/v1/admin/content/{id}/publish: <200ms, p95 <300ms (only cache invalidation, no database write)
- [ ] 4 endpoints queried simultaneously (50 req/s each): all maintain <1000ms response time
- [ ] Database query execution time <100ms for all SELECT queries (no N+1, proper indexes)
- [ ] Memory profiling: no memory leaks over 10-minute load test

### Data Integrity and Consistency (Medium Priority)

- [ ] Created content matches request input exactly: title, subtitle, content, meta_description
- [ ] Published timestamp matches server time (within 1 second)
- [ ] User ID correctly attributed to created_by and updated_by fields
- [ ] Language code values restricted to es, nl, en (enum validation)
- [ ] Page type values restricted to: about, adoption-process, animal-care-standards, faq (enum validation)
- [ ] Soft-delete verified: archived content has published=false but record still queryable
- [ ] No orphaned FAQs: if parent content archived, FAQs remain linked but not visible
- [ ] Duplicate page_type+language prevented: second create of (about, es) fails with 409 or 400

### Security Validation (Low Priority - per OWASP)

- [ ] SQL injection attempts in title/content fields sanitized: `'; DROP TABLE portal_content; --` stored as literal string
- [ ] XSS attempts in content field stored and returned safely: `<script>alert('xss')</script>` returned as-is but not executed in response
- [ ] Path traversal attempts in language param blocked: `../../../etc/passwd` returns 400
- [ ] Rate limiting blocks brute force: 100 requests in 1 second returns 429 for excess
- [ ] JWT validation enforces signature: modified JWT rejected with 401
- [ ] Authorization checks bypass admin endpoints for non-admin users: unauthenticated GET /api/v1/content/* allowed, POST /api/v1/admin/* blocked

### Documentation and Runbooks (Low Priority)

- [ ] Integration test suite documented in `tests/integration/README.md` with: setup instructions, how to run tests, test organization, coverage reporting
- [ ] Troubleshooting guide created: common failures and resolution steps
- [ ] Performance baseline recorded: response times and cache hit ratios for reference
- [ ] Schema migration rollback documented: steps to revert if needed
- [ ] Load testing results documented: concurrent user limits, saturation point, recommendations

---

## Complexity Assessment

**Classification**: Complex (all T01 + T02 requirements plus integration validation)

**Reasoning**:
- Involves 2 tables, 2 audit log tables, 4 indexes
- Requires 50+ integration test cases across lifecycle, caching, auth, errors
- Database schema validation with migration testing
- Performance and load testing
- Cross-functional validation (endpoints + cache + auth + database)

---

## Approach

### Phase 1: Database Schema Setup (1-2 sessions)
1. Review Alembic migration file structure
2. Create migration: `alembic revision --autogenerate -m "create_portal_content_tables"`
3. Define portal_content, faq_entries, audit log tables with constraints and indexes
4. Verify migration: `alembic upgrade head` and `alembic downgrade -1`
5. Validate indexes exist in PostgreSQL: `\d portal_content` and `\di`

### Phase 2: Database Validation Tests (1 session)
1. Create `tests/integration/test_database_schema.py` with pytest fixtures for test database
2. Write tests for:
   - Table existence and column definitions
   - UNIQUE constraint enforcement
   - Foreign key constraints
   - Index creation
3. Run tests to confirm schema matches specification

### Phase 3: Content Lifecycle Integration Tests (2-3 sessions)
1. Create `tests/integration/test_content_lifecycle.py`
2. Implement fixtures for authenticated admin client, fresh database, test data
3. Write test cases for:
   - Create → Publish → Retrieve flow
   - Edit → Re-publish flow
   - Scheduled publishing (may require background job mock)
   - Archive → Retrieve flow
   - Multilingual variants
4. Assert on response codes, cache headers (X-Cache), response times, database state, audit logs
5. Run tests: `pytest tests/integration/test_content_lifecycle.py -v --tb=short`

### Phase 4: Authorization and Permission Tests (1 session)
1. Create `tests/integration/test_authorization.py`
2. Implement fixtures for different user roles (staff, admin, adopter, volunteer)
3. Write test cases for:
   - Role-based access (POST/PATCH/publish/archive)
   - Anonymous access (401 on admin endpoints)
   - JWT expiration
4. Run tests: `pytest tests/integration/test_authorization.py -v`

### Phase 5: Caching and Performance Tests (1-2 sessions)
1. Create `tests/integration/test_caching.py`
2. Implement fixtures for cache timing validation
3. Write test cases for:
   - Cache hits within TTL (<500ms, X-Cache: HIT)
   - Cache misses after TTL (>500ms, X-Cache: MISS)
   - Cache invalidation on publish
   - Language-specific caching
   - Concurrent request handling
4. Create load test: `tests/load/test_cache_performance.py` using locust or similar
5. Run: `pytest tests/integration/test_caching.py -v` and `locust -f tests/load/test_cache_performance.py`

### Phase 6: Error Handling and Edge Cases (1 session)
1. Create `tests/integration/test_error_handling.py`
2. Write test cases for:
   - Database errors (503 responses)
   - Validation errors (400)
   - Not found (404)
   - Concurrent edit conflict (409)
   - Rate limiting (429)
3. Verify error response structure and logging
4. Run: `pytest tests/integration/test_error_handling.py -v`

### Phase 7: Audit Logging Validation (1 session)
1. Create `tests/integration/test_audit_logging.py`
2. Implement fixtures to inspect audit_log table directly
3. Write test cases verifying:
   - Audit entries created for all actions
   - change_summary contains field-level diffs
   - ip_address correctly extracted
   - Immutability enforced
4. Run: `pytest tests/integration/test_audit_logging.py -v`

### Phase 8: Integration Checklist and Documentation (1 session)
1. Create `tests/integration/README.md` documenting:
   - Setup: database fixtures, migrations, test data
   - Running tests: pytest commands, coverage reporting
   - Test organization: by feature (lifecycle, auth, caching, etc.)
   - Troubleshooting: common failures and fixes
2. Create `docs/INTEGRATION_TEST_RESULTS.md` with baseline metrics:
   - Response time benchmarks (cached <500ms, uncached <1000ms)
   - Cache hit ratios (>90%)
   - Error rate expectations (<0.1%)
3. Create `docs/SCHEMA_MIGRATION_GUIDE.md` for rollback procedures

### Phase 9: Load Testing and Performance Validation (1-2 sessions)
1. Create `tests/load/conftest.py` for load test fixtures
2. Implement load tests using locust:
   - 100 concurrent users hitting GET /api/v1/content/about
   - 50 concurrent users creating content (admin role)
   - Mixed workload: 70% reads, 20% writes, 10% deletes
3. Collect metrics: response times, error rate, cache hit ratio
4. Generate HTML report and validate against performance criteria
5. Run: `locust -f tests/load/test_endpoints.py --users 100 --spawn-rate 10`

---

## Dependencies

### External Dependencies
- PostgreSQL 16 (running, accessible)
- SQLAlchemy 2.x (ORM for database operations)
- Alembic (database migrations)
- FastAPI 0.100+ (API framework from T01)
- Pydantic v2 (request/response validation from T01)
- pytest (testing framework)
- pytest-asyncio (async test support)
- httpx (async HTTP client for testing)
- locust (load testing tool, optional but recommended)

### Internal Dependencies
- Task T01: Public endpoints must be implemented (POST /api/v1/admin/content, PATCH, publish, archive, GET /api/v1/content/*)
- Task T02: Admin endpoints and audit logging must be implemented
- EPIC-10: Authentication (JWT validation, roles) must be functional
- Database: PostgreSQL instance with connection pool configured

### Configuration Dependencies
- `DATABASE_URL` environment variable pointing to test database
- `JWT_SECRET_KEY` for test token generation
- Background job scheduler (APScheduler or Celery) if scheduled publishing implemented

---

## Risks

1. **Database Migration Conflicts**: If schema already partially exists, migration may fail. Mitigation: use `alembic stamp head` to align version tracking.
2. **Cache Timing Flakiness**: Tests relying on exact TTL timing may flake due to system load. Mitigation: use generous time windows (300s + 10s buffer) and allow 5% variation.
3. **Rate Limiting Precision**: Tests assuming exact request counts may fail under load. Mitigation: verify rate limits with buffer: expect 10 ± 1 requests.
4. **Concurrent Edit Conflicts**: Hard to reproduce deterministically. Mitigation: use threading library to guarantee simultaneous PATCH requests.
5. **Load Test Resource Exhaustion**: 100 concurrent users may exhaust connection pool. Mitigation: monitor connection count and tune pool size.
6. **Timezone Issues**: Audit log timestamps in UTC, test machine may be different. Mitigation: use UTC consistently, convert for assertions.

---

## Success Criteria

- [ ] All 90+ acceptance criteria passing in automated test suite
- [ ] Test coverage: >90% for content endpoints, >85% for admin endpoints
- [ ] Performance baselines established and documented
- [ ] Zero manual testing required: fully automated CI integration
- [ ] Load testing shows system stable under 100 concurrent users
- [ ] All errors properly logged and handled
- [ ] Schema migration reversible and idempotent
- [ ] Audit logging complete and queryable

---

## Definition of Done

- [ ] `tests/integration/` directory with all test modules created
- [ ] `tests/load/` directory with load test scripts
- [ ] All test cases passing: `pytest tests/integration/ -v` shows 0 failures
- [ ] Coverage report: `pytest --cov=src/content --cov-report=html` shows >85%
- [ ] Database schema verified: `alembic upgrade head` succeeds
- [ ] Load test results: response time metrics and cache hit ratio documented
- [ ] Integration test README and troubleshooting guide written
- [ ] All tests added to CI/CD pipeline (.github/workflows/)
- [ ] Pre-commit hook validates test suite runs without errors
- [ ] Zero warnings: linting, type checking pass on all test code

---

## References

- T01: /home/ai-whisperers/Projects/refugio-animal-paraguay/planning/epics/EPIC-11-public-portal/stories/S03-about-and-educational-pages/tasks/T01-implement-content-endpoints.md
- T02: /home/ai-whisperers/Projects/refugio-animal-paraguay/planning/epics/EPIC-11-public-portal/stories/S03-about-and-educational-pages/tasks/T02-implement-content-management-backend.md
- EPIC-11: /home/ai-whisperers/Projects/refugio-animal-paraguay/planning/epics/EPIC-11-public-portal/
- SQLAlchemy ORM: https://docs.sqlalchemy.org/20/orm/
- Alembic Migrations: https://alembic.sqlalchemy.org/
- pytest Documentation: https://docs.pytest.org/
- locust Load Testing: https://locust.io/

---

## FINAL MUST-PASS CHECKLIST

- [ ] All 90+ acceptance criteria explicitly listed and testable
- [ ] Database schema validation included
- [ ] Content lifecycle tests cover all paths: create, edit, publish, archive
- [ ] Authorization tests for all roles (staff, admin, adopter, volunteer)
- [ ] Caching tests verify TTL, invalidation, cache hit ratio
- [ ] Error handling tests for 400, 401, 403, 404, 409, 429, 503 responses
- [ ] Audit logging tests verify immutability and completeness
- [ ] Performance criteria documented: <500ms cached, <1000ms uncached
- [ ] Load testing approach described with concurrent user counts
- [ ] Phase breakdown clear: 9 phases with session estimates
- [ ] Dependencies explicitly listed (PostgreSQL, SQLAlchemy, pytest, locust)
- [ ] Risks identified with mitigations
- [ ] Success criteria measurable (test coverage %, response time, error rates)
- [ ] Integration with T01 and T02 explicit
- [ ] CI/CD integration mentioned (.github/workflows/)
- [ ] Troubleshooting and documentation output specified

