---
name: rest-api-patterns
description: REST API design, request validation, versioning, error response standards, and pagination patterns
load-when: Designing API endpoint URLs, response envelopes, error schemas, or pagination for this project
not-when: FastAPI implementation details (use fastapi-patterns), database queries (use postgresql-patterns)
project-specific: Refugio error response envelope format, cursor-based pagination, EUR/PYG amount representation in JSON
---

# REST API Patterns

Load this skill when designing, implementing, or reviewing REST API endpoints.

## URL Design

### Resource Naming

```
# ✅ Nouns, plural, lowercase, hyphenated
GET    /animals
GET    /animals/{id}
POST   /animals
PUT    /animals/{id}
PATCH  /animals/{id}
DELETE /animals/{id}

# Nested resources (when relationship is strong)
GET    /animals/{id}/vaccinations
POST   /animals/{id}/vaccinations
GET    /adoptions/{id}/documents

# ✅ Actions as sub-resources (not verbs in URL)
POST   /adoptions/{id}/approve
POST   /adoptions/{id}/reject
POST   /donations/{id}/refund

# ❌ Verbs in URLs
GET    /getAnimals
POST   /createAnimal
PUT    /updateAnimal/{id}
```

### Query Parameters

```
# Filtering
GET /animals?status=available&species=dog

# Sorting
GET /animals?sort=name&order=asc
GET /animals?sort=-created_at         # prefix '-' for descending

# Pagination
GET /animals?page=2&per_page=20
GET /animals?cursor=eyJpZCI6MTAwfQ   # cursor-based for large datasets

# Field selection (sparse fieldsets)
GET /animals?fields=id,name,status,photo_url

# Search
GET /animals?q=golden+retriever
```

---

## HTTP Status Codes

| Code | Use Case | Notes |
|------|----------|-------|
| `200 OK` | Successful GET, PUT, PATCH | Return updated resource for PUT/PATCH |
| `201 Created` | Successful POST | Include `Location` header |
| `204 No Content` | Successful DELETE | No body |
| `400 Bad Request` | Validation error, malformed request | Include error details |
| `401 Unauthorized` | Not authenticated | Token missing or invalid |
| `403 Forbidden` | Authenticated but not authorized | Don't reveal resource existence |
| `404 Not Found` | Resource doesn't exist | Use for public resources only |
| `409 Conflict` | Duplicate, state conflict | e.g., duplicate email |
| `422 Unprocessable Entity` | Semantic validation error | Passes format but fails business rules |
| `429 Too Many Requests` | Rate limit exceeded | Include `Retry-After` header |
| `500 Internal Server Error` | Unexpected server error | Never expose stack traces |

---

## Error Response Format

Consistent error structure across all endpoints:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The request contains invalid data.",
    "details": [
      {
        "field": "email",
        "code": "INVALID_FORMAT",
        "message": "Email must be a valid RFC 5322 address."
      },
      {
        "field": "age",
        "code": "BELOW_MINIMUM",
        "message": "Adopter must be at least 18 years old.",
        "context": { "minimum": 18, "provided": 16 }
      }
    ],
    "request_id": "req_01HXYZ...",
    "docs_url": "https://docs.example.com/errors/VALIDATION_ERROR"
  }
}
```

### Error Code Convention

```
DOMAIN_SPECIFIC_ERROR    # e.g., ADOPTION_PENDING_EXISTS
VALIDATION_ERROR         # Request data invalid
NOT_FOUND               # Resource doesn't exist
UNAUTHORIZED            # Auth required
FORBIDDEN               # Auth present but not allowed
CONFLICT                # Duplicate or state conflict
RATE_LIMITED            # Too many requests
INTERNAL_ERROR          # Unexpected server error (no details)
```

---

## Request Validation

### Validation Order

1. **Parse** — Is the body valid JSON/form data?
2. **Schema** — Do required fields exist? Are types correct?
3. **Format** — Are formats valid (email, date, UUID)?
4. **Business rules** — Does it make sense for the domain?

### Python (FastAPI / Pydantic)

```python
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import date


class CreateAdopterRequest(BaseModel):
    name: str
    email: EmailStr
    date_of_birth: date
    phone: Optional[str] = None

    @field_validator("name")
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Name cannot be blank")
        return v.strip()

    @field_validator("date_of_birth")
    @classmethod
    def must_be_adult(cls, v: date) -> date:
        from datetime import date as today_date
        age = (today_date.today() - v).days // 365
        if age < 18:
            raise ValueError(f"Must be at least 18 years old (provided age: {age})")
        return v
```

### TypeScript (Zod)

```typescript
import { z } from 'zod';

const CreateAdopterSchema = z.object({
  name: z.string().min(1, 'Name cannot be blank').max(200),
  email: z.string().email('Invalid email format'),
  dateOfBirth: z.string().date().refine((val) => {
    const age = Math.floor((Date.now() - new Date(val).getTime()) / 31536000000);
    return age >= 18;
  }, 'Must be at least 18 years old'),
  phone: z.string().optional(),
});

type CreateAdopterRequest = z.infer<typeof CreateAdopterSchema>;
```

---

## Pagination

### Offset-Based (simple, works for small datasets)

```json
// Request: GET /animals?page=2&per_page=20
// Response:
{
  "data": [...],
  "pagination": {
    "page": 2,
    "per_page": 20,
    "total": 143,
    "total_pages": 8,
    "has_next": true,
    "has_prev": true
  }
}
```

### Cursor-Based (stable, works for large/live datasets)

```json
// Request: GET /animals?cursor=eyJpZCI6MTAwfQ&limit=20
// Response:
{
  "data": [...],
  "pagination": {
    "next_cursor": "eyJpZCI6MTIwfQ",
    "prev_cursor": "eyJpZCI6ODl9",
    "has_next": true,
    "limit": 20
  }
}
```

Use cursor-based when:
- Dataset is large (>10,000 items)
- Items are frequently added/removed (offsets become unstable)
- Infinite scroll UX (no page numbers needed)

---

## API Versioning

### URL versioning (recommended for breaking changes)

```
/v1/animals      ← stable
/v2/animals      ← new version with breaking changes
```

### Header versioning (for minor changes)

```
Accept: application/vnd.api+json; version=2
```

### Deprecation headers

```
Deprecation: true
Sunset: Sat, 01 Jan 2027 00:00:00 GMT
Link: <https://docs.example.com/migration/v2>; rel="deprecation"
```

---

## Authentication Headers

```
# Bearer token (JWT or opaque)
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...

# API key
X-API-Key: key_live_abc123...

# Never in query params (shows in logs)
❌ GET /animals?api_key=secret
```

---

## Response Envelope

Consistent structure for all list and single-resource responses:

```json
// Single resource
{
  "data": {
    "id": "uuid",
    "type": "animal",
    "attributes": { ... }
  },
  "meta": {
    "request_id": "req_01HXYZ"
  }
}

// Collection
{
  "data": [...],
  "pagination": { ... },
  "meta": {
    "request_id": "req_01HXYZ",
    "generated_at": "2026-03-25T10:00:00Z"
  }
}
```

Or simpler flat structure (acceptable for smaller APIs):

```json
// Single
{ "id": "uuid", "name": "...", ... }

// Collection
{
  "items": [...],
  "total": 143,
  "page": 1
}
```

Pick one and use it consistently throughout the API.

---

## Rate Limiting Headers

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 842
X-RateLimit-Reset: 1711360800
Retry-After: 30    # on 429 response
```

---

## Idempotency

For POST requests that could be retried (payments, emails):

```
# Client sends idempotency key
POST /donations
Idempotency-Key: 01HXYZ-unique-client-key

# Server: if key seen before, return previous response (don't process again)
# If key new: process and store result with key
```

Store idempotency keys for 24-48 hours minimum.

---

## Common Anti-Patterns

```
❌ Verbs in URLs: /getAnimal, /deleteAnimalById
❌ Inconsistent pluralization: /animal vs /adopters
❌ Returning 200 for errors: { "status": "error", "message": "..." }
❌ Exposing internal IDs: /animals/1, /animals/2 (use UUIDs)
❌ Returning entire database row: exposing internal fields (created_at_internal_ts)
❌ No pagination on list endpoints (will break at scale)
❌ Different error shapes per endpoint
❌ Secrets in URLs or query params
❌ 500 responses with stack traces exposed to client
```
