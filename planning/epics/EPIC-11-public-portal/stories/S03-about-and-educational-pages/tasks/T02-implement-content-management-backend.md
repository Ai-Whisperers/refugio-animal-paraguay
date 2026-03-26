---
epic_id: EPIC-11
story_id: S03
task_id: T02
status: ready
type: technical_task
priority: high
estimated_points: 8
created: 2026-03-25
---

# T02: Implement Content Management Backend (Admin/Staff)

## Objective

Implement role-based admin endpoints for creating, editing, publishing, and archiving multilingual content pages. Enforce strict access control (staff: create/edit, admin: publish/archive), validate content, trigger cache invalidation, and maintain audit logs.

## Description

This task delivers the content management layer for the public portal. While T01 handles public read-only access to cached content, T02 implements the protected admin endpoints that allow staff to author content and admins to publish/control visibility. This includes comprehensive validation, role-based access control (RBAC), cache invalidation on publish, and audit logging for compliance and accountability.

---

## Technical Specification

### Database Schema Extensions

#### Content Management Audit Log Table

The `portal_content_audit_log` table records every create, edit, publish, and archive action performed on portal content pages. The primary key is a BIGSERIAL auto-incrementing integer — not a UUID. This is intentional for audit log tables because integer PKs are more compact for the high-volume insert pattern typical of audit trails. The `content_id` column is a BIGINT foreign key referencing `portal_content(id)`. The `action` column is VARCHAR(50) and holds one of four string values: `created`, `edited`, `published`, or `archived`. The `action_by` column is a BIGINT foreign key referencing `users(id)` — who performed the action. The `action_at` column is a TIMESTAMP defaulting to `CURRENT_TIMESTAMP`. The `change_summary` column is TEXT and stores a JSON-serialized string representing a diff of what changed — for example, for an edit it might encode the old and new title values, or the old and new content lengths. The `ip_address` column uses PostgreSQL's native `INET` type (not a plain VARCHAR) — this type natively validates IP address format and supports subnet operations. The `created_at` column is a TIMESTAMP defaulting to `CURRENT_TIMESTAMP`.

Two indexes support efficient audit log queries: a non-unique index on `content_id` for retrieving the full history of a specific page, and a non-unique index on `action_at` for time-range filtering when admins review recent activity.

#### FAQ Entry Audit Log Table

The `faq_entries_audit_log` table mirrors the structure of `portal_content_audit_log` but targets FAQ entries instead of content pages. The primary key is also a BIGSERIAL integer. The `faq_id` column is a BIGINT foreign key referencing `faq_entries(id)`. All other columns (`action`, `action_by`, `action_at`, `change_summary`, `ip_address`, `created_at`) are identical in type and purpose to their counterparts in `portal_content_audit_log`.

Two indexes: on `faq_id` for per-entry history queries, and on `action_at` for time-range filtering.

### Endpoint Specifications

#### 1. CREATE Content Page

**Endpoint**: `POST /api/v1/admin/content`
**Access**: staff, admin roles
**Rate Limit**: 10 requests/minute (authenticated)

**Request Body**:

The create request accepts the following fields. The `page_type` field must be one of the four valid enum values: `about`, `adoption_process`, `animal_care_standards`, or `faq`. The `language_code` field is a string constrained to 2–5 characters, defaulting to `es`. The `title` field is a string with a minimum length of 5 and maximum of 255 characters. The `content` field is a string with a minimum of 50 characters and a maximum of 50,000 characters (50KB maximum, enforced at the Pydantic validation layer before any database write). The `meta_description` field is optional, minimum 10 characters, maximum 160 characters — the 160-character ceiling is the SEO standard for Google. The `draft` field is a boolean defaulting to True — all content is created as a draft unless explicitly set to False.

**Response**: `201 Created`

The response body includes the `id` of the newly created record, the `page_type`, `language_code`, `title`, `created_by` (user ID), `created_at` (ISO 8601), and `status` which is either `draft` or `published`.

**Validation Rules**:
- Title must be unique per (page_type, language_code, published=true) combination
- Draft pages can have duplicate titles per user
- Content max 50KB (prevents bloat)
- Language code must be valid (es, en, nl, pt)
- Meta description must be ≤160 chars (SEO standard)

**Database Operations**:

The service function first checks whether the caller is creating a non-draft page. If `draft` is False, it queries `portal_content` for any existing row with the same `page_type`, `language_code`, and `published = True`. If such a row exists, a ValueError is raised indicating the conflict. The function then inserts a new `portal_content` row with `published` set to the negation of the `draft` flag. After flushing to obtain the new record's ID, it inserts an audit log row into `portal_content_audit_log` with `action = 'created'`, the user ID, and a JSON-encoded `change_summary` containing the title and the draft flag value. Both the content insert and the audit insert are committed in a single transaction.

---

#### 2. EDIT Content Page

**Endpoint**: `PATCH /api/v1/admin/content/{content_id}`
**Access**: staff (own content only), admin (any content)
**Rate Limit**: 20 requests/minute

**Request Body**:

The update request accepts optional fields: `title` (5–255 chars), `content` (50–50,000 chars), and `meta_description` (10–160 chars). All three are optional — only the fields provided in the request body are updated. A request with no fields provided results in a 400 error. The request body also includes a `version` integer representing the version number the client last read — this enables optimistic locking.

**Response**: `200 OK`

The response body includes `id`, `title`, `content_preview` (the first 200 characters of the updated content body), `updated_at` (ISO 8601), `updated_by` (user ID), and `version` (the new incremented version number).

**Authorization Rules**:

The `check_content_edit_permission` service function enforces RBAC. If the user's role is `admin`, permission is granted unconditionally — admins can edit any content whether draft or published. If the user's role is `staff`, permission is granted only when two conditions are both true: the `created_by_id` on the content record matches the requesting user's ID, and the content's `published` field is False (staff can only edit their own drafts, never published pages). Any other role combination returns False and the endpoint raises HTTP 403.

**Validation Rules**:
- Cannot edit published pages without admin role
- Changes trigger audit log entry
- Version incremented on each edit (for conflict detection)
- Cannot edit another user's content unless admin

**Database Operations**:

The update service function fetches the `portal_content` row by ID (HTTP 404 if not found), then calls `check_content_edit_permission`. For each optional field in the request that is provided and differs from the current value, the change is recorded in a `changes` dictionary as an object with `old` and `new` keys — except for `content` where only `old_length` and `new_length` are stored (to avoid recording the full body twice in the audit log). If the `changes` dictionary is empty after checking all three optional fields, a ValueError is raised indicating no changes were provided. The record's `version` field is incremented by one and `updated_at` is set to the current UTC time. An audit log entry is inserted with `action = 'edited'` and the JSON-encoded `changes` dictionary as the `change_summary`. The content update and the audit insert are committed in a single transaction.

---

#### 3. PUBLISH Content Page

**Endpoint**: `POST /api/v1/admin/content/{content_id}/publish`
**Access**: admin role only
**Rate Limit**: 10 requests/minute

**Request Body**:

The publish request has one optional field: `scheduled_at`, a string in ISO 8601 datetime format. When omitted, the page is published immediately. When provided, the page is scheduled for future publishing.

**Response**: `200 OK`

The response body includes `id`, `page_type`, `language_code`, `status` (either `published` or `scheduled`), `published_at` (ISO 8601 datetime if published immediately, otherwise null), and `scheduled_for` (ISO 8601 datetime if a future publishing time was provided, otherwise null).

**Business Rules**:
- Only admins can publish content
- Draft content must be published before it's available to public
- Can schedule publishing for future time
- Published pages are cached immediately
- Publishing invalidates cache

**Implementation**:

The publish service function raises HTTP 403 if the user's role is not `admin`. It fetches the `portal_content` row (HTTP 404 if not found) and raises ValueError if the content is already published. When `scheduled_at` is not provided, the function sets `published = True` and `published_at` to the current UTC datetime, then immediately invalidates the cache key `content:{page_type}:{language_code}`. When `scheduled_at` is provided, it parses the string to a datetime, verifies it is in the future (raises ValueError if not), and stores it in a `scheduled_publish_at` column without setting `published = True`. The scheduled job is registered with APScheduler or Celery to set `published = True` and invalidate the cache key at the scheduled time. In both cases, an audit log entry is inserted with `action = 'published'` and a JSON change summary containing the `published_at` and `scheduled_for` values.

---

#### 4. ARCHIVE Content Page

**Endpoint**: `POST /api/v1/admin/content/{content_id}/archive`
**Access**: admin role only
**Rate Limit**: 10 requests/minute

**Request Body**:

The archive request requires one field: `reason`, a string with a minimum length of 10 characters and a maximum of 500 characters. The minimum length is enforced by Pydantic — a reason of fewer than 10 characters is rejected at the validation layer before any database operation. This prevents empty or trivially short reasons from polluting the audit log.

**Response**: `200 OK`

The response body includes `id`, `status` (always `archived`), `archived_at` (ISO 8601), and `archived_by` (user ID).

**Business Rules**:
- Only admins can archive content
- Archived content is unpublished and hidden from public
- Soft-delete via published flag
- Cache is invalidated
- Audit trail preserved

**Implementation**:

The archive service function raises HTTP 403 if the user's role is not `admin`. It fetches the row and raises ValueError if the content is not currently published (cannot archive unpublished content — it makes no sense to archive a draft). The function sets `published = False` and `archived_at` to the current UTC datetime. It then invalidates the cache key `content:{page_type}:{language_code}`. An audit log entry is inserted with `action = 'archived'` and a JSON change summary containing the `reason` string and the `archived_at` timestamp. This provides a durable record of why the page was taken down, which satisfies compliance requirements for content history.

---

#### 5. MANAGE FAQ ENTRIES

**Endpoints**:
- `POST /api/v1/admin/faq` — Create FAQ entry
- `PATCH /api/v1/admin/faq/{faq_id}` — Edit FAQ entry
- `POST /api/v1/admin/faq/{faq_id}/publish` — Publish FAQ entry
- `POST /api/v1/admin/faq/{faq_id}/archive` — Archive FAQ entry

**Access Control**: Same as content (staff create/edit, admin publish/archive)

**Create FAQ Request Fields**:

The `language_code` is a string defaulting to `es`. The `category` is a required string of 3–50 characters matching one of the valid category values (adoption, animals, donations, visiting). The `question` is a required string of 10–255 characters. The `answer` is a required string of 50–5,000 characters. The `display_order` is an integer defaulting to 0 for ordering within a category. The `draft` boolean defaults to True.

**FAQ Response Fields**:

The response includes `id` (integer), `category` (string), `question` (string), `answer_preview` (the first 200 characters of the answer, not the full text), `created_at` (ISO 8601), and `status` (either `draft` or `published`).

Audit logging for FAQ entries uses the `faq_entries_audit_log` table with the same pattern as portal content: insert an audit row with `faq_id`, `action`, `action_by`, `change_summary` JSON, and the `ip_address` as a PostgreSQL INET value.

---

### Cache Invalidation Strategy

Cache invalidation is managed by a service class named `CacheInvalidationManager` in `src/cache/invalidation.py`. It exposes three async methods:

`invalidate_on_publish` takes `page_type`, `language_code`, and the shared cache instance, constructs the key as `content:{page_type}:{language_code}`, and calls `cache.invalidate(key)`. It logs the invalidation event at INFO level.

`invalidate_faq_cache` takes `language_code` and the cache instance, constructs the key as `faq:{language_code}`, and calls `cache.invalidate(key)`.

`schedule_cache_invalidation` takes `content_id`, `page_type`, `language_code`, `scheduled_at` datetime, the cache instance, and a scheduler reference. It registers a one-time job with the scheduler using a run date of `scheduled_at`. The job is identified by `invalidate_{content_id}` for deduplication — if the same content is rescheduled, the existing job is replaced. When the job fires it calls `invalidate_on_publish` with the appropriate arguments. This approach works with both APScheduler's `DateTrigger` and Celery's `apply_async(eta=...)`.

---

### Audit Logging

All admin actions are recorded for compliance by a service class named `AuditLogger` in `src/audit/logger.py`. The `log_action` async method accepts user_id, action string, entity_type string (either `content` or `faq`), entity_id integer, change_summary as a Python dictionary, ip_address as a string, and the active database session. It creates the appropriate audit log record — `portal_content_audit_log` for content entities, `faq_entries_audit_log` for FAQ entities — serializing the `change_summary` dictionary to a JSON string for storage in the `change_summary TEXT` column. The `ip_address` string is stored as a PostgreSQL INET column — SQLAlchemy maps Python strings to the INET type automatically when the column is declared with `INET()`. The audit record and the triggering operation (content create/update/publish/archive) are always committed in the same transaction to ensure consistency — an audit entry can never exist without its corresponding action having been committed.

---

## Acceptance Criteria

### Content Management

- [ ] Staff can create draft content pages with validation
- [ ] Staff can edit their own draft pages
- [ ] Staff cannot edit published pages or other users' content
- [ ] Admin can create and publish content in one action
- [ ] Admin can edit any content (draft or published)
- [ ] Admin can publish draft pages with immediate or scheduled publishing
- [ ] Admin can archive published pages with reason tracking
- [ ] Publishing a page immediately invalidates its cache
- [ ] Scheduled publishing works correctly (cache invalidated at scheduled time)
- [ ] All admin actions are logged in audit trail with user ID, action, timestamp, IP address
- [ ] Audit log captures before/after changes as JSON
- [ ] Page titles are unique per (page_type, language_code) for published pages
- [ ] Draft pages can have duplicate titles (different users experimenting)
- [ ] Content length limits enforced (50KB max)
- [ ] Language codes validated against supported list (es, en, nl, pt)
- [ ] Meta descriptions limited to 160 characters (SEO standard)

### FAQ Management

- [ ] Staff can create draft FAQ entries with category and ordering
- [ ] FAQ entries support custom display ordering
- [ ] Staff can edit their own draft FAQ entries
- [ ] Admin can publish FAQ entries
- [ ] Admin can archive FAQ entries with reason
- [ ] FAQ cache invalidated on publish/archive
- [ ] FAQ entries grouped by category in public endpoint (T01)
- [ ] Audit logging applies to FAQ changes

### Authorization & Security

- [ ] Role-based access control enforced on all endpoints
- [ ] Staff cannot access admin endpoints
- [ ] Invalid JWT tokens rejected (401)
- [ ] Expired JWT tokens rejected (401)
- [ ] Rate limiting enforced (10/min for publish, 20/min for edit)
- [ ] Request body size limits enforced (50KB content max)
- [ ] IP address captured in audit logs
- [ ] No hardcoded admin accounts; roles come from users table
- [ ] Concurrent edits handled safely (version incrementation)
- [ ] No SQL injection vulnerabilities (parameterized queries only)

### API Contract

- [ ] POST /api/v1/admin/content returns 201 Created with content ID
- [ ] PATCH /api/v1/admin/content/{id} returns 200 OK with updated content preview
- [ ] POST /api/v1/admin/content/{id}/publish returns 200 OK with status
- [ ] POST /api/v1/admin/content/{id}/archive returns 200 OK with archived status
- [ ] All endpoints return proper error codes (400 validation, 401 auth, 403 forbidden, 404 not found, 503 server)
- [ ] All error responses include error_code and error_message fields
- [ ] Response times: <500ms for create/edit, <200ms for publish/archive

### Data Integrity

- [ ] Database transactions guarantee ACID properties
- [ ] No partial updates on error (rollback on exception)
- [ ] Audit logs cannot be edited or deleted
- [ ] Deleted content still traceable in audit log
- [ ] Version field prevents overwrite conflicts

### Testing Requirements

#### Unit Tests
- [ ] Content creation validates input (title length, content length, language code)
- [ ] Permission checks work correctly for staff vs admin
- [ ] Cache invalidation triggers on publish
- [ ] Audit log entries created with correct data
- [ ] Error messages are specific and actionable

#### Integration Tests
- [ ] Create → Edit → Publish → Archive flow works end-to-end
- [ ] Staff cannot modify published pages
- [ ] Admin can modify any page
- [ ] Scheduled publishing creates audit entry
- [ ] Cache is actually invalidated (verify T01 gets fresh data)
- [ ] Multiple users editing same draft handled safely

#### Security Tests
- [ ] JWT tokens required for all admin endpoints
- [ ] Invalid/expired tokens rejected
- [ ] Rate limiting prevents brute force (verify 429 responses)
- [ ] XSS prevention: HTML content sanitized before storage
- [ ] CSRF tokens included in requests (if form-based)
- [ ] Audit logs cannot be deleted via admin API

#### Performance Tests
- [ ] Create endpoint returns <500ms (write to DB + audit log)
- [ ] Edit endpoint returns <500ms
- [ ] Publish endpoint returns <200ms (cache invalidation fast)
- [ ] Archive endpoint returns <200ms
- [ ] Bulk audit log queries (admin viewing history) <1000ms for 1000 entries

---

## Implementation Considerations

### Error Handling

The `handle_admin_errors` function in `src/utils/error_handlers.py` converts exceptions to standardized API error response tuples. A `ValueError` becomes HTTP 400 with `error_code = "VALIDATION_ERROR"` and the exception message as `error_message`. An `HTTPException` is passed through with its own status code and detail. An `IntegrityError` from SQLAlchemy becomes HTTP 409 Conflict with `error_code = "CONFLICT"` and the message "Resource already exists". Any other unhandled exception is logged at ERROR level and returned as HTTP 500 with `error_code = "SERVER_ERROR"` and the message "An error occurred" — the actual exception details are never exposed in the response body.

### Concurrent Edit Handling

The PATCH endpoint implements optimistic locking using the `version` integer field on `portal_content`. The client sends the `version` number it most recently read as part of the update request body. The server fetches the current content record and compares its `version` to the value in the request. If the two differ, the content was modified by another user between the client's last read and the current update attempt — the server raises HTTP 409 Conflict with the message "Content was modified by another user. Refresh and retry." If the versions match, the update proceeds and the record's `version` is incremented by one before committing. This prevents silent overwrites when two admins edit the same page concurrently.

### Batch Operations

A `bulk_publish` function in `src/services/content_management.py` handles publishing multiple content pages in a single admin action. It accepts a list of `content_id` integers, a user ID, the database session, and the cache instance. It iterates over each content ID, fetches the row, sets `published = True`, and invalidates the cache key `content:{page_type}:{language_code}` for that record. Successes and failures are tracked in a results dictionary with `success` count, `failed` count, and an `errors` list where each error entry contains the `content_id` and the exception message. All successful updates are committed in a single `db.commit()` call after the loop completes. This batch approach minimizes the number of database round-trips compared to calling the single-publish endpoint repeatedly.

---

## Related Tasks

- **T01** — Implement public content read endpoints (completed)
- **T03** — Frontend admin dashboard for content management
- **S04** — Donation landing pages (dependent on content infrastructure)

---

## Dependencies

- PostgreSQL 16 (audit tables with BIGSERIAL PK and INET ip_address type)
- SQLAlchemy 2.x (ORM, async session)
- FastAPI (web framework, dependency injection for JWT guards)
- Pydantic v2 (validation, constrained types for field length limits)
- JWT library (authentication, role extraction from token claims)
- Background scheduler for scheduled publishing (APScheduler or Celery — decision TBD in Phase 2)

---

## Validation Before Closure

- [ ] All endpoints tested with valid and invalid inputs
- [ ] Role-based access control verified for each endpoint
- [ ] Audit logs accurate and complete
- [ ] Cache invalidation working (verified via T01 cache test)
- [ ] Rate limiting functional
- [ ] Error messages follow WHAT+WHY+HOW format
- [ ] Performance targets met (<500ms typical operations)
- [ ] Security scan clean (no SQL injection, XSS vectors)
- [ ] All acceptance criteria marked complete
