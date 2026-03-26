---
epic_id: EPIC-11
story_id: S03
task_id: T01
title: "Implement Content Delivery Endpoints for About and Educational Pages"
status: ready
type: technical_task
priority: high
estimated_points: 5
created_at: 2026-03-25
dependencies:
  - EPIC-10 (Authentication Infrastructure)
  - EPIC-6 (Communications & Email System)
tags:
  - backend
  - fastapi
  - postgresql
  - caching
  - multilingual
---

# Task: Implement Content Delivery Endpoints for About and Educational Pages

## Overview

Implement four public HTTP endpoints for retrieving educational and informational content pages (About Us, Adoption Process, Animal Care Standards, FAQ). These endpoints serve pre-configured, cacheable content to website visitors. Unlike contact forms or animal inquiries, these endpoints do not require rate limiting. Each endpoint supports multilingual content with language fallback to Spanish. Responses are cached in-memory for 5 minutes to optimize performance and reduce database queries.

## Technical Specifications

### Endpoints

#### GET /api/v1/content/about

Retrieves the "About Us" page containing shelter mission, history, and values information.

**Query Parameters:**
- `language` (optional, string): Language code (es, nl, en). Default: es.

**Success Response (HTTP 200):**

The response body contains the following fields: `id` (UUID string of the content record), `page_type` (always `about_us`), `title` (string, the page title), `subtitle` (optional string), `content` (full HTML string for the page body), `meta_description` (optional string, SEO meta), `meta_keywords` (optional string), `language` (string, the language code actually served — may be `es` if Spanish fallback was triggered), `published_at` (ISO 8601 datetime when the page was first published), `last_updated_at` (ISO 8601 datetime of the most recent edit), `cache_ttl_seconds` (integer, always 300), and `response_time_ms` (integer milliseconds elapsed to serve the response).

**Error Responses:**
- HTTP 404 Not Found: Page not published or no Spanish fallback available
- HTTP 503 Service Unavailable: Database or cache layer failure

#### GET /api/v1/content/adoption-process

Retrieves the "Adoption Process" page with step-by-step adoption workflow documentation.

**Query Parameters:**
- `language` (optional, string): Language code (es, nl, en). Default: es.
- `include_timeline` (optional, boolean): Include estimated timelines. Default: true.

**Success Response (HTTP 200):**

The response body contains the same base fields as the About endpoint (`id`, `page_type`, `title`, `subtitle`, `content`, `language`, `published_at`, `last_updated_at`, `cache_ttl_seconds`) plus a `steps` array. Each step object in `steps` contains: `order` (integer, 1-based position), `title` (string, the step name in Spanish), `description` (string, narrative explanation of that step), and `estimated_duration_days` (integer, included only when `include_timeline` is true). Example steps include "Búsqueda y Selección" as step 1 with an estimated duration of one day, and "Solicitud de Adopción" as step 2 also with a one-day estimate.

#### GET /api/v1/content/animal-care-standards

Retrieves the "Animal Care Standards" page documenting shelter protocols, health standards, and regulatory compliance (CITES, Paraguayan regulations).

**Query Parameters:**
- `language` (optional, string): Language code (es, nl, en). Default: es.
- `section` (optional, string): Specific section filter (health, nutrition, housing, cites_compliance). Omit for full page.

**Success Response (HTTP 200):**

The response body contains the base fields plus a `sections` object and a `regulatory_certifications` array. The `sections` object has up to four keys: `health`, `nutrition`, `housing`, and `cites_compliance`. Each section object contains a `title` string, a `content` string with detailed prose, and a `compliance` string naming the applicable standard or regulation. The `regulatory_certifications` array contains plain strings listing active certifications such as "CITES Compliant", "Paraguayan Ministry of Environment Approved", and "ISO 14971 Health/Safety". The `content` field at the top level contains the full HTML page with all sections combined. When the `section` query parameter is provided, only the matching section key appears inside `sections`.

#### GET /api/v1/content/faq

Retrieves the "Frequently Asked Questions" page with common visitor questions and answers.

**Query Parameters:**
- `language` (optional, string): Language code (es, nl, en). Default: es.
- `category` (optional, string): FAQ category filter (adoption, animals, donations, visiting). Omit for all.

**Success Response (HTTP 200):**

The response body contains the base fields plus a `categories` array. Each category object in `categories` has a `name` string (the machine key, e.g. `adoption`), a `title` string (the Spanish display label, e.g. `Adopción`), and a `questions` array. Each question object in `questions` has an `id` (UUID string), a `question` string in Spanish, an `answer` string, and an `order` integer indicating display position within the category. When the `category` query parameter is provided, only the matching category appears in the `categories` array.

### Database Schema

**Table: portal_content**

This table stores all publishable page content. The primary key is a UUID generated by `gen_random_uuid()`. The `page_type` column is a VARCHAR(50) constrained by a CHECK to exactly four values: `about_us`, `adoption_process`, `animal_care_standards`, and `faq`. The `title` column is VARCHAR(500) and is required. The `subtitle` column is optional VARCHAR(500). The `content` column is TEXT and is required — it stores the full HTML body. The `meta_description` column is optional VARCHAR(160) for SEO use. The `meta_keywords` column is optional VARCHAR(200). The `language_code` column is VARCHAR(5), required, defaulting to `es`. The `published` column is a boolean required, defaulting to false (content is draft by default — a security requirement). The `published_at` column is a nullable timestamptz. The `created_by_user_id` and `updated_by_user_id` columns are UUID foreign keys referencing `users(id)`. The `created_at` and `updated_at` columns are timestamptz with `NOW()` defaults.

A UNIQUE constraint spans `(page_type, language_code, published)` — this enforces that only one published version of each page type per language can exist at any given time.

Three indexes are required for query performance: a composite index on `(page_type, published)` for the primary lookup by type and publication state, an index on `language_code` for language fallback queries, and an index on `published_at DESC` for administrative sorting by recency.

**Table: faq_entries**

This table stores individual FAQ question-and-answer pairs. The primary key is a UUID generated by `gen_random_uuid()`. The `page_id` column is a UUID foreign key referencing `portal_content(id)` with `ON DELETE CASCADE` — when a FAQ content page is deleted all its entries are deleted automatically. The `question` column is VARCHAR(1000), required. The `answer` column is TEXT, required. The `category` column is VARCHAR(50), required, defaulting to `general`. The `display_order` column is INT, required, for controlling sort order within a category. The `published` column is boolean defaulting to false. The `created_by_user_id` and `updated_by_user_id` columns are UUID foreign keys to `users(id)`. The `created_at` and `updated_at` columns are timestamptz with `NOW()` defaults.

Three indexes support efficient queries: on `page_id` for joining to the parent page, on `category` for category-filtered FAQ retrieval, and on `published` for filtering to only published entries.

### Caching Strategy

1. **Cache Key Structure**: `content:{page_type}:{language_code}`
2. **TTL**: 300 seconds (5 minutes)
3. **Cache Population**:
   - On-demand first access (lazy loading)
   - Cache invalidation on content update/publish (immediate)
   - Fallback to Spanish if requested language not published
4. **Cache Storage**: In-memory Python dictionary. Each cache entry stores the serialized response value, the TTL in seconds (always 300), and the creation timestamp captured via `time.time()`. The expiry check compares `time.time() - entry.created_at` against `entry.ttl_seconds` on each get — expired entries are evicted lazily on access. A module-level `content_cache` instance is shared across all requests within a single process.
5. **Cache Hit Priority**: Exact language match → Spanish fallback → None (404)

**Cache invalidation trigger:**
- When content is published via admin endpoint (T02)
- When content is updated via admin endpoint (T02)
- On scheduled refresh: Daily at 00:00 UTC

### Multilingual Support

1. **Language Fallback Chain**:
   - 1st priority: Exact match (es, nl, en)
   - 2nd priority: Spanish (es) — default/fallback language
   - 3rd priority: None — return HTTP 404

2. **Language Codes Supported**:
   - `es` — Spanish (Paraguayan, primary)
   - `nl` — Dutch (European donor base)
   - `en` — English (secondary)

### Response Requirements

1. **Cached Responses** (target under 500ms):
   - Content served directly from cache
   - Include `Cache-Control: public, max-age=300` header
   - Include `X-Cache: HIT` response header

2. **Uncached Responses** (target under 1000ms):
   - Content fetched from database
   - Stored in cache immediately
   - Include `X-Cache: MISS` response header

3. **404 Responses**:
   - No published content in requested language or Spanish fallback
   - Body: `{"error": "Content not found", "page_type": "about_us", "language": "es"}`
   - No cache-control header

### Error Handling

1. **Database Errors**:
   - HTTP 503 Service Unavailable
   - Log error with context (page_type, language, user_agent)
   - Include `Retry-After: 60` header

2. **Validation Errors**:
   - HTTP 400 Bad Request if `language` parameter invalid
   - Body: `{"error": "Invalid language code", "valid_codes": ["es", "nl", "en"]}`

3. **Not Found**:
   - HTTP 404 if page_type or language combination unpublished
   - Body: `{"error": "Content not found", "page_type": "about_us", "language": "es"}`

## Acceptance Criteria

- [ ] Four endpoints implemented (about, adoption-process, animal-care-standards, faq)
- [ ] All endpoints support `language` query parameter with fallback to Spanish
- [ ] Responses cached in-memory with 300-second TTL
- [ ] Cached responses return within <500ms
- [ ] Uncached responses return within <1000ms
- [ ] Cache hits include `X-Cache: HIT` header
- [ ] Cache misses include `X-Cache: MISS` header
- [ ] FAQ endpoint supports optional `category` filter parameter
- [ ] Animal care standards endpoint supports optional `section` filter parameter
- [ ] Adoption process endpoint includes optional timeline estimates
- [ ] HTTP 404 returned for unpublished content with no fallback
- [ ] HTTP 503 returned on database errors with `Retry-After` header
- [ ] HTTP 400 returned for invalid language codes with valid options listed
- [ ] No rate limiting applied (informational endpoints)
- [ ] Multilingual content respects language priority chain
- [ ] Portal_content table created with published flag and soft-delete support
- [ ] FAQ entries stored in faq_entries table with proper foreign keys
- [ ] Composite indexes created for performance optimization
- [ ] All responses follow Pydantic v2 schema validation
- [ ] Response times logged to audit trail for monitoring
- [ ] Code passes linting (zero warnings/errors)
- [ ] Unit tests written covering all endpoints and cache behavior
- [ ] Integration tests validate database interactions
- [ ] Performance tests verify response time targets
- [ ] Security tests confirm no data leakage

## Implementation Considerations

### Cache Implementation

The cache is implemented as a Python class named `SimpleCache` in `src/cache/content_cache.py`. It wraps a private dictionary mapping string keys to cache entry objects. Each entry stores the cached value, the TTL in seconds, and a float timestamp from `time.time()` captured at insertion time. The `get` method checks whether the current time minus the stored timestamp exceeds the TTL — if so, the entry is deleted from the dictionary and the method returns None. The `set` method inserts or overwrites the key with a fresh entry. The `invalidate` method removes a specific key if it exists, silently ignoring missing keys. A single module-level instance named `content_cache` is imported wherever cache access is needed.

### Pydantic Response Schemas

The `ContentResponse` Pydantic v2 base model lives in `src/schemas/portal/content.py`. It has these fields: `id` as a string (UUID rendered as string), `page_type` as a string, `title` as a string, `subtitle` as an optional string defaulting to None, `content` as a string (full HTML), `meta_description` as an optional string, `meta_keywords` as an optional string, `language` as a string, `published_at` as a datetime, `last_updated_at` as a datetime (mapped from `updated_at`), `cache_ttl_seconds` as an integer with default 300, and `response_time_ms` as an integer.

The `FAQCategory` model has `name` as a string, `title` as a string, and `questions` as a list of dictionaries. The `FAQResponse` model extends `ContentResponse` and adds a `categories` field as a list of `FAQCategory` objects.

### Database Query Strategy

For each endpoint, the handler first constructs the cache key as `content:{page_type}:{language_code}` and checks the in-memory cache. If a hit is found, the cached value is returned immediately with the `X-Cache: HIT` header. On a miss, the handler executes a SQLAlchemy async SELECT against `portal_content` filtered by `page_type`, `language_code`, and `published = True`. If no result is found and the requested language is not already Spanish, the query is repeated with `language_code = 'es'` as the fallback. If still no result, HTTP 404 is raised. On success, the result is serialized, stored in the cache with TTL 300, and returned with the `X-Cache: MISS` header.

Language parameter validation uses a Python `StrEnum` class named `LanguageCode` with values `es`, `nl`, and `en`. FastAPI receives this enum as the query parameter type — invalid values are automatically rejected with HTTP 422 Unprocessable Entity, which the endpoint exception handler converts to the standardized HTTP 400 body described above.

### Response Time Tracking

Each endpoint records `time.time()` at its entry point and calculates `response_time_ms` as the integer millisecond difference before returning. This value is both included in the response body and passed to the structured logger alongside `page_type`, `language`, and a boolean `cached` flag. This data feeds monitoring dashboards (defined in EPIC-9) that alert on P95 response time regressions.

### Error Handling

`SQLAlchemyError` exceptions are caught and converted to HTTP 503 with the `Retry-After: 60` header. All errors are logged via Python's standard `logging` module with `page_type`, `language`, `user_agent`, and the exception message as structured extra fields. Stack traces are logged at ERROR level but never exposed in API response bodies.

## Success Metrics

1. **Response Time**:
   - Cached responses: <500ms (target: <300ms)
   - Uncached responses: <1000ms (target: <700ms)
   - All endpoints consistently within targets

2. **Cache Efficiency**:
   - Cache hit rate: >90% for high-traffic endpoints
   - Cache miss rate: <10% (expected on cold start or expired entries)
   - Cache invalidation: Immediate on content update

3. **Data Accuracy**:
   - Content always matches latest published version
   - Language fallback works correctly (requested → es → 404)
   - No stale data served beyond TTL

4. **Error Handling**:
   - 4xx errors returned for client errors (invalid language, not found)
   - 5xx errors returned for server errors (database, cache failure)
   - All errors logged with full context
   - Error messages non-revealing (no stack traces)

5. **Availability**:
   - All four endpoints operational and responding
   - No cascading failures (cache failure doesn't crash API)
   - Graceful degradation (serves from DB if cache fails)

## Testing Strategy

### Unit Tests

1. **Cache Behavior**:
   - Test cache hit on repeated requests
   - Test cache miss on expired TTL
   - Test cache invalidation
   - Test concurrent access to cache

2. **Language Fallback**:
   - Test exact language match returned
   - Test fallback to Spanish when exact match unavailable
   - Test 404 when Spanish also unavailable
   - Test invalid language code returns 400

3. **Response Schema Validation**:
   - Test all required fields present
   - Test response_time_ms calculated correctly
   - Test cache_ttl_seconds set to 300
   - Test published_at and last_updated_at in ISO format

### Integration Tests

1. **Database Interactions**:
   - Test content fetched from correct portal_content row
   - Test soft-delete respected (published=false not returned)
   - Test composite index utilized (verified via EXPLAIN ANALYZE)
   - Test concurrent requests don't corrupt cache

2. **API Contracts**:
   - Test HTTP 200 with cached response includes X-Cache: HIT
   - Test HTTP 200 with uncached response includes X-Cache: MISS
   - Test HTTP 404 returned with proper error body
   - Test HTTP 503 returned on database error with Retry-After header

### Performance Tests

1. **Load Testing**:
   - 100 concurrent requests to cached endpoint (should all complete <500ms)
   - 100 concurrent requests to uncached endpoint (should all complete <1000ms)
   - Burst of 50 requests after cache expiration (verify TTL honored)

2. **Cache Performance**:
   - Measure hit ratio under sustained load
   - Measure memory usage with various TTL durations
   - Test cache doesn't cause memory leaks with long-running processes

### Security Tests

1. **Input Validation**:
   - SQL injection attempts in language parameter blocked
   - XSS payloads in content HTML not executable
   - Large inputs (>1MB) rejected gracefully

2. **Data Leakage**:
   - Unpublished content never returned
   - Draft content never returned
   - User IDs of editors not exposed in response

## Dependencies and Constraints

### Required Systems

- EPIC-10 Authentication Infrastructure (JWT tokens already available)
- PostgreSQL 16 with SQLAlchemy 2.x ORM (connection pooling)
- FastAPI 0.100+ with async support
- Pydantic v2 for schema validation

### External Dependencies

- Python `time` module (built-in) for TTL tracking
- No external caching library needed (simple in-memory implementation)
- Email notifications leverage existing EPIC-6 communications system

### Constraints

1. **Database Constraint**: portal_content.published must default to False (security)
2. **Performance Constraint**: Cache TTL must be exactly 300 seconds (per S03 specs)
3. **Content Constraint**: All content must be valid HTML (sanitization in T02)
4. **Language Constraint**: Only es, nl, en supported; no custom languages
5. **Concurrency Constraint**: In-memory cache must be thread-safe (simple dict sufficient for FastAPI)

### Known Limitations

1. **Single-Instance Deployment**: In-memory cache not shared across server instances (acceptable for MVP)
2. **No Cache Warmup**: Content loaded on-demand, not preloaded on startup
3. **No Cache Monitoring**: No endpoint to inspect cache state (can add in future)
4. **Language-Specific URLs**: URLs don't change by language (query param only)
5. **No Content Versioning**: Only latest published version served; no version history

## Related Tasks

- **T02**: Implement content management backend (create/edit/publish endpoints for admins)
- **EPIC-6**: Email notifications for content updates
- **EPIC-10**: Authentication for admin endpoints in T02
