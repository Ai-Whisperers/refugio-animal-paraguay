# RAP-012 Post-Implementation Review Notes

**Reviewer**: Automated gap review
**Date**: 2026-03-26
**Files reviewed**: 6 new, 3 modified

---

## 1. Missing Edge Cases

### 1.1 No validation on photo_urls format
`IntakeCreate.photo_urls` accepts `list[str]` with no URL validation. Malformed strings, empty strings, or non-URL values are silently accepted. Consider adding `AnyHttpUrl` or a regex validator for V2.

### 1.2 No upper bound on photo_urls list length
A client could submit hundreds of photo URLs in a single request. There is no `max_length` on the `photo_urls` field. Should add a reasonable cap (e.g., 20) to prevent abuse and DB bloat.

### 1.3 birth_date parsed as string, not native date
`IntakeCreate.birth_date` is typed as `str | None` and parsed manually in the endpoint with `date.fromisoformat()`. Using a Pydantic `date` type would push validation to the schema layer and simplify the endpoint. Current approach works but is inconsistent with Pydantic-first validation patterns used elsewhere.

### 1.4 No duplicate intake guard
Nothing prevents creating two intake records for the same animal name/details in rapid succession. The `animal_id` UNIQUE constraint on `intake_records` prevents duplicate *records per animal*, but nothing prevents accidentally creating two distinct animals from the same real-world intake event. This is acceptable for MVP but worth noting.

### 1.5 finder_phone has no format validation
`finder_phone` accepts any string up to 50 chars. No phone number format validation. Acceptable for Paraguay context (mixed formats) but worth standardizing later.

---

## 2. Incomplete Error Handling

### 2.1 No explicit DB error handling in create_intake
The `create_intake` endpoint does not catch `IntegrityError` or other SQLAlchemy exceptions. If `db.flush()` fails (e.g., constraint violation, connection loss), the raw 500 will propagate. The session rollback is handled by the middleware/dependency, but the error message will be opaque to the client.

### 2.2 handle_quarantine_trigger is fire-and-forget logging
The quarantine stub only logs. When EPIC-4 replaces it with actual medical record creation, failures in that function could silently fail if not properly integrated into the transaction. The TODO is clear but the integration point needs attention during EPIC-4.

---

## 3. Security Concerns

### 3.1 photo_urls are stored without sanitization
Photo URLs are stored as-is from user input. No sanitization, no domain allowlisting. Could be used for SSRF if the URLs are later fetched server-side (e.g., for thumbnail generation). Currently read-only storage, so low risk, but flag for when photo processing is added.

### 3.2 No rate limiting on POST /animals/intake
Authenticated staff can create unlimited intake records. Combined with the unbounded photo_urls list, this could be used for resource exhaustion. Rate limiting is planned in RAP-013 (CORS + Rate Limiting story) which will address this cross-cuttingly.

### 3.3 Staff can intake animals without restrictions
Any staff user can create intakes. No additional permission check beyond `require_staff`. This is correct per current RBAC design but worth reviewing if intake should be restricted to specific roles (e.g., intake_coordinator) in future.

---

## 4. Missing Test Coverage

### 4.1 No test for concurrent intake creation
No test verifying behavior when two intakes are created simultaneously (race condition on animal creation).

### 4.2 No test for very long text fields
`location_found`, `condition_on_arrival`, and `notes` are `Text` columns with no length validation in the schema. No tests for extremely long strings (e.g., 100KB).

### 4.3 No test for empty photo_urls list behavior
While the default is tested, no explicit test for `photo_urls: []` being sent in the payload (vs. omitted entirely).

### 4.4 No test for intake_date ordering in list endpoint
The list endpoint orders by `intake_date.desc()` but no test verifies the ordering.

---

## 5. Integration Concerns

### 5.1 Router registration order dependency
The intake router MUST be registered before the animals router in `app.py` to avoid `/animals/{id}` matching "intake". This is documented in a code comment but is fragile. If someone reorders the router registrations, intake endpoints break silently (returning 422 instead of routing correctly). Consider using a more explicit path prefix or documenting this in CLAUDE.md's key decisions.

### 5.2 AnimalStatus enum must include INTAKE and QUARANTINE
The intake workflow depends on `AnimalStatus.INTAKE` and `AnimalStatus.QUARANTINE` existing. If the enum is modified without checking intake, the workflow breaks. No compile-time enforcement of this dependency.

### 5.3 Migration 005 CHECK constraint must stay in sync with IntakeSource enum
The CHECK constraint in the migration hardcodes `('stray', 'surrender', 'rescue', 'transfer')`. If `IntakeSource` enum is extended, a new migration must update the CHECK constraint. No automated enforcement.

---

## 6. Technical Debt

### 6.1 B008 ruff warnings across all API files
`Depends()` and `Query()` in function default parameters trigger B008 (function-call-in-default-argument). This is a known FastAPI pattern and pre-exists across all API files. Not introduced by this PR, but the count grows with each new endpoint.

### 6.2 `type()` objects in unit tests as ORM stand-ins
Unit tests use `type("_FakeFoo", (), {...})()` to create fake ORM objects because SQLAlchemy instruments `__new__`. This works but is brittle — if the schema adds required fields, the fake objects silently lack them. Consider a shared test factory or `dataclass`-based fakes.

### 6.3 HTTP_422_UNPROCESSABLE_ENTITY deprecation
The `status.HTTP_422_UNPROCESSABLE_ENTITY` constant used in create_intake is deprecated in favor of `HTTP_422_UNPROCESSABLE_CONTENT` in newer Starlette versions. Non-blocking but will trigger deprecation warnings eventually.

---

## 7. Recommendations

| Priority | Item | Effort |
|----------|------|--------|
| P1 | Add `max_length` to `photo_urls` field (cap at 20) | 10 min |
| P1 | Add URL validation to `photo_urls` entries | 30 min |
| P2 | Use Pydantic `date` type for `birth_date` instead of manual parsing | 30 min |
| P2 | Add DB error handling in create_intake (IntegrityError -> 409) | 30 min |
| P3 | Document router registration order in architecture notes | 10 min |
| P3 | Add ordering test for list endpoint | 15 min |
| P3 | Add long-text-field tests | 15 min |
| P4 | Standardize fake ORM objects in unit tests | 1 hr |
| P4 | Update deprecated HTTP status constant | 5 min |

---

*Review complete. No fixes applied per review protocol — issues documented only.*
