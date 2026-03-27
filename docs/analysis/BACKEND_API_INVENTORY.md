# Refugio Animal Paraguay — Backend API Complete Inventory

**Date**: 2026-03-27
**Scope**: Complete endpoint-by-endpoint breakdown of all FastAPI routes, models, services, and identified issues.

---

## Overview

The Refugio Animal Paraguay backend is a FastAPI application with ~41 API router modules, async PostgreSQL via SQLAlchemy, domain-driven event bus, email/SMS/payment integrations, and GDPR/audit compliance features.

**Total Endpoints**: ~130 across all routers
**Key Technologies**: FastAPI, SQLAlchemy (async), PostgreSQL, Stripe, Twilio (WhatsApp), Pydantic, slowapi (rate limiting)

---

## Table of Contents

1. [Application Setup & Middleware](#application-setup--middleware)
2. [Authentication & Authorization](#authentication--authorization)
3. [Core Resources](#core-resources)
4. [Payments & Financial](#payments--financial)
5. [Adoption Workflow](#adoption-workflow)
6. [Sponsorships & Subscriptions](#sponsorships--subscriptions)
7. [Medical Records](#medical-records)
8. [Notifications & Communication](#notifications--communication)
9. [Compliance (GDPR/Audit)](#compliance-gdpraudit)
10. [Public APIs](#public-apis)
11. [Admin & Internal](#admin--internal)
12. [Database Models & Migrations](#database-models--migrations)
13. [Issues & Gaps](#issues--gaps)

---

## Application Setup & Middleware

### File: `src/app.py`

**Purpose**: FastAPI app factory, router registration, middleware stack, lifespan management.

**Middleware Stack** (outermost → innermost):
1. `RequestIDMiddleware` — Attach `request_id` to all requests/responses
2. `RequestLoggingMiddleware` — Structured logging of all requests/responses
3. `AuditMiddleware` — Track write operations (POST/PATCH/DELETE) for audit trail
4. `CORSMiddleware` — Cross-origin resource sharing (configurable origins)
5. `Rate Limiting` (slowapi) — Global rate limits (auth: 5/min, general: 60/min)
6. Exception Handlers — Centralized error formatting (422, 401, 409, 402, 500, etc.)

**Lifespan Events**:
- **Startup**: Initialize async DB engine, start EventBus, register notification handlers (Email, In-App, WhatsApp)
- **Shutdown**: Stop EventBus, dispose DB engine

**Configuration**:
- Sentry error tracking (configurable DSN, traces sampling)
- Debug mode (FastAPI debug=settings.debug)
- CORS origins from settings (comma-separated list)

**Issues**:
- ✅ No issues in app factory itself; well-structured

---

## Authentication & Authorization

### File: `src/api/auth.py`

**Endpoint Summary**:

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/auth/token` | None | Login with email + password → JWT token |
| POST | `/auth/users` | Admin | Create staff/admin user + send verification email |
| GET | `/auth/me` | Staff+ | Return current authenticated user |

**POST /auth/token**
- **Rate Limit**: 5/minute (AUTH_RATE_LIMIT)
- **Logic**:
  - Query user by email (from OAuth2PasswordRequestForm)
  - If not found or inactive → 401 "Invalid credentials" (constant-time rejection)
  - Check account lockout (failed_login_attempts + locked_until)
  - If locked → 423 "Account temporarily locked"
  - Verify password with bcrypt
  - If wrong → record failed attempt, possibly trigger 15-min lockout
  - Check email_verified flag → 403 if not verified
  - Reset failed attempt counter
  - Create session record (for timeout + forced logout)
  - Issue JWT with 30-min expiry + JTI (session ID)
- **Returns**: `TokenResponse` with `access_token`
- **DB Models Used**: `User`, `ActiveSession`
- **Issues**:
  - ⚠️ **Timing attack vulnerability**: "Unknown user or inactive" uses constant-time rejection, but password verification for valid users happens AFTER lockout check. Attackers can probe which emails exist by timing. Mitigation: consider always-hash even for non-existent users.
  - ✅ Account lockout implemented correctly (15-min exponential backoff)
  - ✅ Session tracking prevents concurrent token reuse

**POST /auth/users** (Create staff/admin user)
- **Auth**: Requires admin role
- **Rate Limit**: 5/minute
- **Logic**:
  - Validate email not already in use (409 if duplicate)
  - Hash password with bcrypt
  - Create User with role (STAFF | ADMIN), email_verified=false
  - Attempt to send verification email (best-effort; doesn't fail user creation)
  - Return UserResponse
- **DB Models Used**: `User`
- **Issues**:
  - ✅ Duplicate email check via unique constraint
  - ⚠️ Email verification email is best-effort (try/except swallows). User created but may never verify if email service fails. Consider logging failure + admin notification.

**GET /auth/me**
- **Auth**: Requires staff+ role
- **Returns**: Current user's UserResponse
- **Issues**:
  - ✅ No issues; straightforward dependency

**File: `src/auth/dependencies.py`**

**Dependency Functions**:

| Function | Role | Notes |
|----------|------|-------|
| `_get_current_user` | Internal | Extract JWT, validate token, validate session |
| `require_staff` | Public | Staff or admin (raises 403 otherwise) |
| `require_admin` | Public | Admin only |
| `require_vet` | Public | Vet role only (for medical records) |
| `require_medical_staff` | Public | Vet, Staff, or Admin |

**JWT Validation Flow**:
1. Extract token from Authorization: Bearer header (HTTPBearer)
2. Decode JWT using secret_key + algorithm (HS256)
3. Extract `sub` (user_id) and `jti` (session ID)
4. Query User from DB
5. If jti present, validate session (not revoked, not timed out, < 30 min idle)
6. Refresh session last_activity timestamp
7. Return User or raise 401

**Issues**:
- ⚠️ **Session timeout + inactivity refresh**: Sessions are validated but last_activity is refreshed on every request. If client makes a request at min 29, session expires at min 59 (30 min from last_activity). This means actual expiry can extend indefinitely. Mitigate: Add hard expiry (created_at + max_session_duration) separate from idle timeout.
- ✅ Backward compatibility: Tokens without JTI (issued before session tracking) are allowed through. Good for migration.

---

## Core Resources

### File: `src/api/animals.py`

**Endpoint Summary**:

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/animals` | None | List animals, filter by species/status, paginated |
| GET | `/animals/{id}` | None | Single animal details |
| POST | `/animals` | Staff+ | Create animal record |
| PATCH | `/animals/{id}` | Staff+ | Update animal fields |
| DELETE | `/animals/{id}` | Staff+ | Hard delete animal |
| POST | `/animals/{id}/photos` | Staff+ | Add gallery photo |
| DELETE | `/animals/{id}/photos/{id}` | Staff+ | Remove gallery photo |

**GET /animals**
- **Query Params**: `species`, `status`, `offset=0`, `limit=20` (max 100)
- **Returns**: List of AnimalResponse
- **DB Query**: SELECT from Animal, filter + order by created_at DESC
- **Issues**:
  - ✅ Pagination implemented (offset/limit with defaults)
  - ⚠️ **N+1 potential**: No eager loading of photos; if used in templates, each animal might trigger separate photo query
  - ⚠️ **Public endpoint**: No auth required; leaks all animal names/species/status to public

**POST /animals**
- **Payload**: `AnimalCreate` (name, species, status, breed, size, gender, birth_date, description, primary_photo_url)
- **Auth**: Staff+ required
- **DB Models**: Creates `Animal` record
- **Issues**:
  - ✅ Staff-only; good
  - ⚠️ **No URL validation**: `primary_photo_url` not validated as valid HTTP URL. Could store garbage/security risks. Recommend regex or URL parser.

**PATCH /animals/{id}**
- **Payload**: `AnimalUpdate` (partial; any field can be omitted)
- **Logic**: Dynamic setattr for enum fields
- **Issues**:
  - ✅ Enum conversion handled
  - ⚠️ **Explicit updated_at set**: Line 117 sets `animal.updated_at = datetime.now(UTC)` but SQLAlchemy onupdate should handle this. Redundant. Remove or clarify why needed.
  - ⚠️ **No validation on breed/size/gender**: Can be arbitrary strings

**DELETE /animals/{id}**
- **Hard delete**: Removes record completely
- **Issues**:
  - ⚠️ **Hard delete vs soft delete**: No preservation of adoption history if animal is deleted. Recommend soft delete (set deleted_at) to maintain referential integrity + audit trail.

**File: `src/api/adopters.py`

**Endpoint Summary**:

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/adopters` | Staff+ | Paginated list (excludes soft-deleted) |
| GET | `/adopters/{id}` | Staff+ | Single adopter or 404 |
| POST | `/adopters` | Staff+ | Create adopter |
| PATCH | `/adopters/{id}` | Staff+ | Update adopter fields |
| DELETE | `/adopters/{id}` | Staff+ | Soft delete (sets deleted_at) |

**POST /adopters**
- **Payload**: `AdopterCreate` (full_name, email, phone, address, gdpr_consent_at)
- **Issues**:
  - ✅ Soft delete implemented (preserves audit trail)
  - ⚠️ **No email validation**: Email stored as plain string; should validate format
  - ⚠️ **Duplicate email check**: Relies on unique constraint + IntegrityError. Good, but could be explicit validation before insert.

**GET /adopters**
- **Filter**: Excludes deleted_at IS NOT NULL
- **Issues**:
  - ✅ Soft-delete filtering correct

---

## Adoption Workflow

### File: `src/api/adoption_requests.py`

**Endpoint Summary**:

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/adoption-requests` | Staff+ | List all adoption requests (filter by status/animal/adopter) |
| GET | `/adoption-requests/{id}` | Staff+ | Single request details |
| GET | `/adoption-requests/analytics` | Staff+ | Stats: avg time-to-decision, approval rate, volume |
| POST | `/adoption-requests` | Staff+ | Create adoption request |
| PATCH | `/adoption-requests/{id}/status` | Staff+ | Transition status (PENDING → APPROVED/REJECTED/CANCELLED) |
| POST | `/adoption-requests/{id}/contract` | Staff+ | Generate adoption contract PDF |

**Status Transitions** (allowed):
```
PENDING    → APPROVED, REJECTED, CANCELLED
APPROVED   → CANCELLED
REJECTED   → CANCELLED
CANCELLED  → (terminal)
```

**POST /adoption-requests**
- **Payload**: `AdoptionRequestCreate` (animal_id, adopter_id, notes)
- **Logic**:
  1. Validate animal exists (404 if not)
  2. Validate adopter exists AND not soft-deleted (404 if deleted)
  3. Create AdoptionRequest with status=PENDING, submitted_at=now
  4. Publish `adoption_request_created` domain event (triggers email notification)
- **Issues**:
  - ✅ Proper validation
  - ✅ Domain event published for downstream handlers
  - ⚠️ **No duplicate check**: Can create multiple pending requests for same animal+adopter pair. Mitigation: Add UNIQUE(animal_id, adopter_id) WHERE status='pending'

**PATCH /adoption-requests/{id}/status**
- **Payload**: `AdoptionRequestStatusUpdate` (status: enum)
- **Logic**:
  1. Validate state transition is allowed
  2. Set decided_at = now if transitioning to terminal state
  3. If APPROVED: set Animal.status = "adopted"
  4. Publish `adoption_status_changed` domain event
- **Issues**:
  - ✅ State machine enforced
  - ⚠️ **Animal status update**: If approval fails, animal status might be updated but request status not. Need transaction atomicity. Check if wrapping in db.begin_nested().
  - ⚠️ **No authorization check on status change**: Any staff can approve any request. Consider adding authorization rules (e.g., only request creator or admin can approve).

**GET /adoption-requests/analytics**
- **Returns**: Total count, status breakdown, avg time-to-decision hours, approval rate %, requests in last 7/30 days
- **Issues**:
  - ✅ Well-structured aggregations
  - ⚠️ **Slow queries**: Multiple separate queries (count, group_by, avg, count filters). Consider single query with window functions or denormalized metrics table.

**POST /adoption-requests/{id}/contract**
- **Logic**: Calls `ContractPDFGenerator.generate()` to create adoption contract
- **Issues**:
  - ⚠️ **No details given**: Need to read ContractPDFGenerator implementation to check for issues

---

## Payments & Financial

### File: `src/api/donations.py`

**Endpoint Summary**:

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/donations` | None | Create donation record (anonymous allowed) |
| POST | `/donations/cash` | Staff+ | Record cash donation (immediate completion) |
| POST | `/donations/{id}/stripe-intent` | None | Create Stripe PaymentIntent, return client_secret |
| GET | `/donations/stats` | Staff+ | Aggregated donation stats (count, totals by currency/method) |
| GET | `/donations/export` | Staff+ | CSV export of all donations |
| GET | `/donations` | Staff+ | Paginated list with filters |
| GET | `/donations/{id}` | Staff+ | Single donation details |
| GET | `/donations/{id}/receipt` | Staff+ | PDF receipt (calls donation_receipt_service) |

**POST /donations** (Create donation)
- **Payload**: `DonationCreate` (donor_id [optional], amount_cents, currency, payment_method, fund_category, campaign_id [optional], is_recurring, recurring_interval, notes)
- **Auth**: None (public; anonymous donations allowed)
- **Logic**:
  1. If donor_id supplied, validate donor exists (404 if not)
  2. If campaign_id supplied, validate campaign exists & is active (404/422 if not)
  3. Validate currency is supported (EUR, USD, PYG)
  4. Create Donation record with status=PENDING (for Stripe) or COMPLETED (for cash)
  5. If COMPLETED, publish `donation_received` domain event
- **Issues**:
  - ✅ Donor/campaign validation
  - ⚠️ **Payment method validation**: No check that payment_method matches currency. E.g., "stripe" with "PYG" should fail (Stripe doesn't support PYG). Recommend explicit validation.
  - ⚠️ **Anonymous donations**: No way to contact donor for receipt/updates. Consider requiring email or external donor ID for receipt.
  - ⚠️ **No idempotency**: Can duplicate create requests → multiple donations. Recommend idempotency_key + unique constraint.

**POST /donations/{id}/stripe-intent** (Create PaymentIntent)
- **Logic**:
  1. Query donation by ID
  2. Create Stripe PaymentIntent for donation amount/currency
  3. Store stripe_payment_intent_id in donation record
  4. Return client_secret to frontend
- **Issues**:
  - ✅ Payment intent lifecycle correct
  - ⚠️ **Intent reuse**: If endpoint called multiple times, creates multiple intents. Could waste Stripe API calls. Recommend idempotency using unique idempotency_key.

**POST /donations/cash** (Record cash donation)
- **Auth**: Staff+ required
- **Payload**: `CashDonationCreate` (donor_id [optional], amount_cents, currency, notes)
- **Logic**:
  1. Create donation with status=COMPLETED
  2. Set payment_method="cash"
  3. Generate receipt_number
  4. Publish `donation_received` domain event
- **Issues**:
  - ✅ Immediate completion appropriate for cash
  - ⚠️ **Receipt number generation**: Hardcoded? Sequential? Consider UUID or timestamp-based.

**File: `src/api/sepa.py`

**Endpoint Summary**:

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/donations/sepa` | None | Create SEPA Direct Debit donation |
| POST | `/donations/{id}/sepa-intent` | None | Create Stripe SetupIntent for SEPA mandate |
| POST | `/donations/subscribe` | None | Create recurring SEPA subscription |
| DELETE | `/donations/subscriptions/{id}` | None | Cancel subscription |
| POST | `/donations/sepa/setup-intent` | None | Create SetupIntent for mandate |
| GET | `/donations/sepa/payment-methods/{customer_id}` | None | List SEPA payment methods for customer |
| GET | `/donations/{id}/sepa-status` | None | Check SEPA payment status |

**Issues**:
- ⚠️ **Public endpoints with no auth**: Customers could cancel other customers' subscriptions if they know the ID. Recommend JWT auth or customer_token validation.
- ⚠️ **Payment method listing**: GET `/donations/sepa/payment-methods/{customer_id}` is public; leaks customer payment methods. Recommend auth + customer ownership check.

---

## Sponsorships & Subscriptions

### File: `src/api/sponsorships.py`

**Endpoint Summary**:

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/sponsorships/tiers` | None | List sponsorship tier definitions |
| PATCH | `/sponsorships/tiers/{id}` | Admin | Update tier (price, description) |
| POST | `/sponsorships` | None | Create sponsorship (public) |
| GET | `/sponsorships` | Staff+ | List all sponsorships |
| GET | `/sponsorships/{id}` | Staff+ | Single sponsorship details |
| PATCH | `/sponsorships/{id}/cancel` | Staff+ | Cancel active sponsorship |
| PATCH | `/sponsorships/{id}/pause` | Staff+ | Pause active sponsorship |
| PATCH | `/sponsorships/{id}/resume` | Staff+ | Resume paused sponsorship |
| GET | `/animals/{id}/sponsorships` | None | List active sponsorships for animal |
| GET | `/donors/{id}/sponsorships` | Staff+ | List sponsorships by donor |

**Issues**:
- ⚠️ **POST /sponsorships** public with no auth; allows spam. Rate-limit or CAPTCHA needed.
- ⚠️ **No sponsor-owns-sponsorship check**: `/sponsorships/{id}/cancel` allows any staff to cancel. Should restrict to sponsorship owner or admin.

### File: `src/api/subscriptions.py`

**Endpoint Summary**:

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/subscriptions` | None | Create recurring subscription (public) |
| GET | `/subscriptions/stats` | Staff+ | Subscription stats (count, MRR, churn) |
| GET | `/subscriptions` | Staff+ | Paginated list |
| GET | `/subscriptions/donor/{id}` | Staff+ | List subscriptions by donor |
| GET | `/subscriptions/{id}` | Staff+ | Single subscription |
| POST | `/subscriptions/{id}/cancel` | Staff+ | Cancel subscription |
| POST | `/subscriptions/{id}/pause` | Staff+ | Pause subscription |
| POST | `/subscriptions/{id}/resume` | Staff+ | Resume subscription |
| PATCH | `/subscriptions/{id}` | Staff+ | Update subscription amount/interval |

**Issues**:
- ⚠️ **POST /subscriptions** is public; allows spam. Rate-limit or CAPTCHA needed.

---

## Medical Records

### File: `src/api/vaccinations.py` (641 lines)

**Endpoint Summary**:

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/vaccine-types` | None | List vaccine types |
| POST | `/vaccine-types` | Vet+ | Create vaccine type |
| GET | `/animals/{id}/vaccinations` | Medical staff+ | List vaccinations for animal |
| POST | `/animals/{id}/vaccinations` | Vet+ | Record vaccination |
| GET | `/animals/{id}/vaccinations/{id}` | Medical staff+ | Single vaccination |
| PATCH | `/animals/{id}/vaccinations/{id}` | Vet+ | Update vaccination |
| DELETE | `/animals/{id}/vaccinations/{id}` | Vet+ | Delete vaccination |

**Issues**:
- ✅ Proper auth roles (vet-only for writes, medical_staff for reads)

### File: `src/api/surgeries.py` (364 lines)

**Endpoint Summary**: Similar to vaccinations (CRUD for surgery records)
- GET `/animals/{id}/surgeries` — list surgeries for animal
- POST `/animals/{id}/surgeries` — record surgery
- GET/PATCH/DELETE `/animals/{id}/surgeries/{id}`

**Issues**:
- ✅ Proper auth roles

### File: `src/api/diagnoses.py` (238 lines)

**Endpoints**: Diagnosis and treatment records
- GET/POST `/animals/{id}/diagnoses`
- GET/PATCH/DELETE `/animals/{id}/diagnoses/{id}`
- GET/POST `/animals/{id}/diagnoses/{id}/treatments`

**Issues**:
- ✅ Vet-only auth

### File: `src/api/medications.py` (208 lines)

**Endpoints**: Medication prescriptions
- GET `/treatments/{id}/medications`
- POST `/treatments/{id}/medications`
- GET/PATCH/DELETE `/medications/{id}`
- GET `/animals/{id}/medications`

**Issues**:
- ⚠️ **No drug interaction checking**: No validation against drug contraindications or overdoses. Recommend integration with drug database API.

### File: `src/api/prescriptions.py`

**Endpoint**: GET `/prescriptions` — list all active prescriptions
**Issues**:
- ⚠️ **No auth specified**: Check implementation

### File: `src/api/medical_documents.py`

**Endpoints**: Document upload/download for vet visits
- GET `/vet-visits/{id}/documents` — list documents
- POST `/vet-visits/{id}/documents` — upload document
- GET `/medical-documents/{id}` — download document
- DELETE `/medical-documents/{id}` — remove document

**Issues**:
- ⚠️ **No file type validation**: Could upload malicious files (e.g., .exe). Recommend whitelist (.pdf, .jpg, .png) + antivirus scan.
- ⚠️ **No file size limit**: DoS risk. Add maxsize validation.

### File: `src/api/vet_visits.py`

**Endpoints**:
- GET `/animals/{id}/vet-visits` — list visits
- GET `/animals/{id}/vet-visits/{id}` — single visit
- POST `/animals/{id}/vet-visits` — create visit record
- PATCH `/animals/{id}/vet-visits/{id}` — update visit
- DELETE `/animals/{id}/vet-visits/{id}` — delete visit

**Issues**:
- ✅ Proper auth roles

### File: `src/api/vet_referrals.py` (173 lines)

**Endpoints**:
- GET `/vet-referrals` — list referrals (filter by status)
- GET `/vet-referrals/{id}` — single referral
- POST `/animals/{id}/vet-referrals` — create referral (staff creates request for vet)
- PATCH `/vet-referrals/{id}/assign` — assign to vet
- PATCH `/vet-referrals/{id}/complete` — mark complete

**Issues**:
- ✅ Proper workflow

---

## Notifications & Communication

### File: `src/api/notifications.py`

**Endpoint Summary**:

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/notifications` | Staff+ | List notifications for current user (paginated) |
| GET | `/notifications/unread-count` | Staff+ | Count unread notifications |
| POST | `/notifications` | Staff+ | Create notification (admin-side) |
| PATCH | `/notifications/{id}/read` | Staff+ | Mark notification as read |
| POST | `/notifications/mark-all-read` | Staff+ | Mark all unread as read |
| DELETE | `/notifications/{id}` | Staff+ | Delete notification |

**Issues**:
- ✅ Staff-only access
- ⚠️ **No per-user filtering**: GET `/notifications` returns all for "current user"? Need to verify implementation actually filters by current_user.id.

### File: `src/api/notification_preferences.py`

**Endpoints**:
- GET `/notification-preferences` — get preferences for current user
- PUT `/notification-preferences` — update preferences

**Notification Types Supported**:
- Email notifications (adoption updates, donations, etc.)
- In-app notifications (stored in DB, read via `/notifications`)
- WhatsApp notifications (via Twilio)

**Issues**:
- ✅ User preference management

---

## Compliance (GDPR/Audit)

### File: `src/api/gdpr.py`

**Endpoint**:
- POST `/gdpr/deletion-request` — request full data deletion (fires async GDPR deletion job)

**Deletions Include**:
- User account
- All related adopter/donor/sponsorship records
- Audit logs (with retention policy exceptions)
- Email/contact submissions

**Issues**:
- ✅ GDPR compliance implemented
- ⚠️ **No deletion confirmation workflow**: Should require email confirmation + waiting period (e.g., 30 days) before executing deletion. Currently may be immediate.

### File: `src/api/gdpr_export.py`

**Endpoint**:
- POST `/gdpr/data-export` — export all user data as JSON/ZIP

**Data Exported**:
- User profile
- All donations/sponsors/subscriptions
- Audit logs
- Interaction history

**Issues**:
- ✅ GDPR Article 15 (right to data portability) implemented
- ⚠️ **No auth specified in endpoint**: Should require user to be logged in or use email verification token.

### File: `src/api/admin.py`

**Endpoints**:
- GET `/admin/audit-logs` — paginated audit log list (staff+ required)
- GET `/admin/audit-logs/export` — CSV export of audit logs

**Audit Log Fields**: action (create/update/delete), user_id, resource_type, resource_id, changes (before/after), ip_address, timestamp

**Issues**:
- ✅ Audit trail captured via AuditMiddleware
- ⚠️ **Audit logs not immutable**: Records can be deleted. Recommend append-only table + write-once policy.

---

## Public APIs

### File: `src/api/public.py`

**Endpoints**:
- GET `/public/animals` — list animals (no auth)
- GET `/public/animals/{id}` — single animal details (no auth)

**Differences from Staff API**:
- No user/adopter info leakage
- Only public-facing fields (name, photos, description, status)

**Issues**:
- ✅ Separate endpoint for public consumption

### File: `src/api/public_adoption.py`

**Endpoint**:
- POST `/public/adoption-applications` — unauthenticated visitor submits adoption application

**Rate Limit**: 10/hour

**Logic**:
1. Validate GDPR consent given
2. Validate animal exists & status="available"
3. Find or create adopter by email
4. Check for duplicate pending application (same animal)
5. Create adoption request
6. Publish domain event (triggers notification)

**Issues**:
- ✅ GDPR consent enforced
- ✅ Rate-limited (10/hour) to prevent spam
- ⚠️ **Adopter creation on first submission**: If visitor provides email but never completes form, adopter record created. Could accumulate junk records. Consider soft delete after X days if no completed application.

### File: `src/api/public_campaigns.py` (224 lines)

**Endpoints**:
- GET `/public/campaigns` — list active campaigns (public)
- GET `/public/campaigns/{id}` — single campaign details
- GET `/public/campaigns/{id}/social-proof` — donor names/amounts (optional anonymity)

**Issues**:
- ⚠️ **Social proof leakage**: `/social-proof` reveals donor names/amounts if show_in_public=true. Should respect donor privacy settings.

### File: `src/api/public_contact.py`

**Endpoints**:
- POST `/public/contact` — contact form submission (no auth)
- POST `/public/animals/{id}/inquiries` — animal inquiry submission (no auth)

**Rate Limit**: Likely to prevent spam
**Storage**: ContactSubmission model (stored in DB, not emailed directly)

**Issues**:
- ⚠️ **No CAPTCHA/honeypot**: Vulnerable to spam. Recommend reCAPTCHA or rate limiting by IP.
- ⚠️ **No input validation**: Contact forms accept arbitrary text; potential for XSS if rendered in admin panel without escaping.

---

## Admin & Internal

### File: `src/api/admin_campaigns.py`

**Endpoints**:
- POST `/admin/campaigns` — create campaign (admin+ required)
- PATCH `/admin/campaigns/{id}` — update campaign
- GET `/admin/campaigns` — list campaigns (staff+)
- GET `/admin/campaigns/{id}` — single campaign

**Campaign Fields**: title, slug (unique), description, goal_amount_cents, fund_category, start_date, end_date, featured, paused, photo_url

**Issues**:
- ✅ Admin-only creation
- ⚠️ **Slug uniqueness**: Relies on unique constraint. Should validate slug format (alphanumeric + hyphens) before insert.

### File: `src/api/animal_updates.py` (267 lines)

**Endpoints**:
- POST `/animal-updates` — create update post (staff+)
- GET `/animal-updates` — list updates (paginated)
- GET `/my-sponsorships/updates` — updates for sponsor's animals
- GET `/sponsorships/{id}/notification-preferences` — get notification prefs
- PUT `/sponsorships/{id}/notification-preferences` — update prefs

**Update Types**: Health, adoption, behavior, behavior milestones

**Issues**:
- ✅ Idempotency key per update to prevent duplicates
- ✅ Notification preferences per sponsorship

### File: `src/api/follow_ups.py` (173 lines)

**Endpoints**:
- GET `/follow-ups/analytics/outcomes` — follow-up outcome stats (staff+)
- GET `/follow-ups` — list follow-ups
- GET `/follow-ups/{id}` — single follow-up
- POST `/follow-ups/schedule/{request_id}` — schedule follow-up after adoption
- POST `/follow-ups/{id}/survey` — submit follow-up survey
- POST `/follow-ups/{id}/return` — mark animal returned

**Follow-up Workflow**:
1. After adoption approved, staff schedules follow-up check-in
2. Automated reminders sent at scheduled dates
3. Adopter submits survey (animal health, behavior, satisfaction)
4. If issues (e.g., "animal returned"), escalate

**Issues**:
- ✅ Well-structured follow-up workflow
- ⚠️ **Survey response not validated**: Could submit without full answers. Recommend required fields.

### File: `src/api/appointments.py`

**Endpoints**:
- GET `/appointments` — list appointments (staff+)
- POST `/appointments` — create appointment (staff+)

**Appointment Types**: Vet visits, adoption interviews, donations meetings

**Issues**:
- ⚠️ **No conflict detection**: Can double-book staff/animals. Recommend checking availability before insert.

### File: `src/api/donors.py` (265 lines)

**Endpoints**:
- POST `/donors` — create donor (staff+)
- GET `/donors/export` — CSV export (staff+)
- GET `/donors` — paginated list
- GET `/donors/{id}` — single donor

**Donor Fields**: name, email, phone, address, gdpr_consent_at, show_in_public

**Issues**:
- ✅ show_in_public flag respects privacy
- ⚠️ **No email validation**: Should validate format before insert.

### File: `src/api/consents.py`

**Endpoints**:
- GET `/users/{id}/consents` — list consents for user
- GET `/users/{id}/consents/details` — detailed consent records
- PUT `/users/{id}/consents` — update consent (GDPR, email, marketing, etc.)

**Consent Types**: GDPR data processing, email contact, marketing, SMS/WhatsApp

**Issues**:
- ✅ Granular consent management
- ✅ GDPR-compliant

---

## Webhooks

### File: `src/api/webhooks.py` (615 lines)

**Endpoint**:
- POST `/webhooks/stripe` — receive Stripe webhook events (signature verified)

**Stripe Events Handled**:

| Event | Handler | Action |
|-------|---------|--------|
| `payment_intent.succeeded` | _handle_payment_succeeded | Mark donation COMPLETED, publish event |
| `payment_intent.payment_failed` | _handle_payment_failed | Mark donation FAILED |
| `payment_intent.processing` | _handle_payment_processing | SEPA async payment accepted by bank |
| `charge.refunded` | _handle_charge_refunded | Mark donation REFUNDED |
| `invoice.payment_succeeded` | _handle_invoice_payment_succeeded | Recurring subscription payment received |
| `invoice.payment_failed` | _handle_invoice_payment_failed | Recurring subscription payment failed |
| `customer.subscription.deleted` | _handle_subscription_deleted | Mark subscription canceled |
| `customer.subscription.updated` | _handle_subscription_updated | Update subscription amount/interval |
| `setup_intent.succeeded` | _handle_setup_intent_succeeded | SEPA mandate saved |
| `setup_intent.setup_failed` | _handle_setup_intent_failed | SEPA mandate setup failed |
| `mandate.updated` | _handle_mandate_updated | SEPA mandate status changed |

**Webhook Security**:
- Verify signature using stripe_webhook_secret (prevents spoofing)
- Ignore unhandled event types
- Log all events for debugging

**Issues**:
- ✅ Signature verification implemented
- ✅ Idempotent handlers (safe to replay events)
- ⚠️ **No dead-letter queue**: Failed webhook handlers are logged but not retried. Stripe webhooks have retry logic, but if handler crashes, event is lost. Recommend storing failed webhooks for manual replay.
- ⚠️ **No rate limiting on webhook**: Could accept high volume and overwhelm DB. Recommend queue (e.g., Redis) + async job processing.

### File: `src/api/tigo_money.py` (227 lines)

**Endpoints**:
- POST `/tigo-money/initiate` — initiate Tigo Money payment (public)
- POST `/tigo-money/callback` — Tigo Money webhook (signature verified)

**Tigo Money**: Local PYG payment method (mobile money in Paraguay)

**Issues**:
- ✅ Webhook signature verification
- ⚠️ **Callback endpoint public**: Allows unauthenticated requests. Should be rate-limited or IP-whitelisted to Tigo Money servers only.

---

## Email Verification

### File: `src/api/email_verification.py`

**Endpoints**:
- POST `/auth/email/verify` — verify email with token
- POST `/auth/email/resend` — resend verification email

**Verification Flow**:
1. User registers (or admin creates account)
2. Verification email sent with token (valid 24 hours)
3. User clicks link, submits token to `/auth/email/verify`
4. Token validated, email_verified set to true
5. User can now log in

**Issues**:
- ✅ Token-based verification
- ⚠️ **24-hour expiry hardcoded**: Should be configurable via settings
- ⚠️ **No rate limiting on resend**: Attacker could spam resend requests. Recommend per-user rate limit (e.g., 3 resends/hour).

---

## Password Reset

### File: `src/api/password_reset.py`

**Endpoints**:
- POST `/auth/password-reset/request` — request password reset (send email with token)
- POST `/auth/password-reset/confirm` — confirm reset with token + new password
- GET `/auth/password-reset/validate` — validate token (frontend pre-check)

**Reset Flow**:
1. User requests reset by email
2. Token sent via email (valid 15 minutes)
3. User submits token + new password to `/confirm`
4. Token validated, hashed password updated
5. User can log in with new password

**Issues**:
- ✅ Time-limited tokens
- ⚠️ **No session invalidation on reset**: User's existing sessions not revoked. Old tokens remain valid. Recommend clearing all active sessions on password reset.
- ⚠️ **No rate limiting on request**: Attacker could spam password resets. Recommend per-email rate limit (e.g., 3 requests/hour).

---

## Session Management

### File: `src/api/sessions.py`

**Endpoints**:
- GET `/auth/sessions` — list active sessions for current user
- DELETE `/auth/sessions/{id}` — revoke single session
- DELETE `/auth/sessions/user/{id}` — revoke all sessions for user (admin+ required)

**Session Fields**: jti (session ID), user_id, token_expires_at, ip_address, user_agent, created_at, last_activity

**Issues**:
- ✅ Session tracking + revocation implemented
- ⚠️ **IP/user agent not validated**: Sessions can be used from different IP/user agent. Recommend warning user if detected.

---

## Events & Domain-Driven Design

### File: `src/events/domain_events.py`

**Domain Events Published**:

| Event | Trigger | Handler |
|-------|---------|---------|
| `adoption_request_created` | New adoption request | Email notification to staff + donor |
| `adoption_status_changed` | Status transition (approved/rejected) | Email to adopter + staff |
| `donation_received` | Donation completed | Email receipt, update dashboard |
| `sponsorship_created` | New sponsorship | Email confirmation |
| `sponsorship_cancelled` | Sponsorship canceled | Email notification |
| `vaccination_scheduled` | Vaccination recorded | Sponsor notification (if opted-in) |

### File: `src/events/bus.py`

**Event Bus**: In-memory async pub/sub with handler registration

**Handlers Registered at Startup**:
- `NotificationHandlers` (email notifications via SMTP)
- `InAppNotificationHandlers` (store in DB for `/notifications` endpoint)
- `WhatsAppHandlers` (send via Twilio WhatsApp API)

**Issues**:
- ✅ Async event processing (non-blocking)
- ⚠️ **No event persistence**: Events not stored; if bus crashes, in-flight events lost. Recommend event sourcing or durable queue (Redis, RabbitMQ).
- ⚠️ **No dead-letter handling**: Failed handlers not retried. Recommend retry logic + DLQ.

---

## Database Models & Migrations

### Models Overview

**Core Tables**:
- `users` — Staff/admin accounts (email, hashed_password, role, is_active, email_verified, failed_login_attempts, locked_until)
- `active_sessions` — Session tokens (jti, user_id, token_expires_at, ip_address, user_agent, last_activity)
- `animals` — Shelter animals (name, species, status, breed, size, gender, birth_date, description, primary_photo_url)
- `animal_photos` — Gallery photos (animal_id, url, caption, display_order)
- `adopters` — Adoption candidates (full_name, email, phone, address, gdpr_consent_at, deleted_at for soft delete)
- `adoption_requests` — Adoption workflow (animal_id, adopter_id, status, submitted_at, decided_at, notes)
- `donors` — Financial supporters (name, email, phone, address, show_in_public)
- `donations` — Individual donations (donor_id, amount_cents, currency, payment_method, status, stripe_payment_intent_id, receipt_number, is_recurring)
- `campaigns` — Fundraising campaigns (title, slug, goal_amount_cents, start_date, end_date, featured, paused)
- `sponsorships` — Animal sponsors (donor_id, animal_id, tier, status, created_at, paused_at)
- `subscriptions` — Recurring donations (donor_id, amount_cents, currency, interval, status, stripe_subscription_id)
- `vet_visits` — Medical records (animal_id, vet_id, visit_date, diagnosis, treatment, notes)
- `vaccinations` — Vaccination records (animal_id, vaccine_type, vaccination_date, next_due_date)
- `surgeries` — Surgery records (animal_id, surgery_type, date, anesthesia_type, duration_minutes, notes)
- `medical_documents` — File uploads (vet_visit_id, file_url, document_type)
- `audit_logs` — Audit trail (user_id, action, resource_type, resource_id, changes_before, changes_after, ip_address, timestamp)
- `notifications` — In-app notifications (user_id, title, message, is_read, created_at)
- `user_consents` — GDPR consents (user_id, consent_type, value, created_at)
- `verification_tokens` — Email verification tokens (token, user_id, expires_at)
- `contact_submissions` — Public contact form responses (name, email, subject, message)
- `in_kind_donations` — Non-monetary donations (name, category, quantity, value_estimate)

**Constraints**:
- Unique: users.email, adopters.email, donors.email, campaigns.slug, animal_updates.idempotency_key
- Foreign keys: adoption_requests → animals/adopters, donations → donors, etc.
- Check: users.role IN ('staff', 'admin', 'vet')

**Issues**:
- ⚠️ **No column-level encryption**: Sensitive fields (email, phone, address) stored in plaintext. Recommend encryption at rest (e.g., PyCrypto + HSM key derivation).
- ⚠️ **No data versioning**: Audit logs capture changes but no versioning table. Recommend temporal tables (PostgreSQL TEMPORAL TABLES) or event sourcing.
- ✅ Timestamps (created_at, updated_at) on all transactional tables
- ✅ UUIDs for primary keys (prevents ID enumeration)

### Migrations

**File**: `src/db/alembic/versions/`

30 migration files (001 to 030) covering:
- Core tables (animals, adopters, adoption_requests)
- Users & auth (users, email_verified, sessions, account_lockout)
- Payments (donations, in_kind_donations, subscriptions, SEPA)
- Medical (vaccinations, surgeries, diagnoses, treatments)
- GDPR (consents, audit logs)
- Campaigns & sponsorships

**Issues**:
- ✅ Alembic managed migrations
- ⚠️ **No rollback tests**: Recommend testing each migration both up and down to catch rollback issues.
- ⚠️ **Large data migrations may lock tables**: Consider using `CONCURRENTLY` for index creation on large tables.

---

## Database Session & Connection

### File: `src/db/session.py`

**Setup**:
- Async SQLAlchemy engine (asyncpg driver)
- Session factory for dependency injection
- Connection pooling (pool_size=5, max_overflow=10)

**Issues**:
- ✅ Async engine configured correctly
- ⚠️ **Pool settings hardcoded**: Should be configurable via settings for production tuning.
- ⚠️ **No retry logic on connection failure**: If DB temporarily unavailable, requests fail immediately. Recommend exponential backoff + circuit breaker.

---

## Issues & Gaps

### Security Issues

#### 1. **Timing Attack on Authentication** (Medium)
- **Location**: `/auth/token` login endpoint
- **Issue**: "Unknown user or inactive" rejection happens before password verification for known users. Attackers can detect valid emails by timing response.
- **Fix**: Use bcrypt verification even for non-existent users (requires storing dummy hash or using constant-time comparison).

#### 2. **SEPA/Payment Method Enumeration** (Medium)
- **Location**: `/donations/sepa/payment-methods/{customer_id}`, `/donations/{id}/sepa-status`
- **Issue**: Public endpoints allow unauthenticated users to query payment methods + statuses if they guess a customer ID.
- **Fix**: Require JWT auth + customer ownership check, or use opaque tokens.

#### 3. **Public Contact Forms Without CAPTCHA** (Medium)
- **Location**: `/public/contact`, `/public/animals/{id}/inquiries`
- **Issue**: Vulnerable to form spam/abuse. No CAPTCHA or proof-of-work.
- **Fix**: Add reCAPTCHA v3 or rate limiting by IP.

#### 4. **Password Reset Without Session Invalidation** (Low)
- **Location**: `/auth/password-reset/confirm`
- **Issue**: Existing sessions not revoked after password reset. Attacker with old token can continue using account.
- **Fix**: Clear all active sessions on password reset.

#### 5. **Missing File Upload Validation** (Medium)
- **Location**: `/vet-visits/{id}/documents`, `/medical-documents`
- **Issue**: No file type/size limits. Could upload malware or exhaust storage.
- **Fix**: Whitelist file types (.pdf, .jpg, .png), enforce max size (e.g., 10MB), scan with antivirus.

#### 6. **Audit Log Mutation Risk** (Low)
- **Location**: `/admin/audit-logs`
- **Issue**: Audit logs can be deleted, breaking immutability. Staff could cover tracks.
- **Fix**: Make audit logs append-only (write-once policy). Implement archive/backup strategy.

#### 7. **No SQL Injection Protection in Dynamic Queries** (Low)
- **Location**: Donations filtering functions (`_apply_common_filters`)
- **Issue**: Uses SQLAlchemy ORM correctly; no injection risk. ✅ Good.

### Data Quality Issues

#### 1. **Missing Input Validation** (Medium)
- **URL fields**: `animals.primary_photo_url`, `medical_documents.file_url` not validated as valid HTTP URLs
- **Phone numbers**: No E.164 format validation
- **Email addresses**: No format validation (relies on constraint)
- **Fix**: Use Pydantic validators (e.g., `EmailStr`, `HttpUrl`, `constr(regex=...)`)

#### 2. **No Duplicate Detection for Public Forms** (Low)
- **Location**: `/public/adoption-applications`, `/public/contact`
- **Issue**: Duplicate submissions possible (spam or user error)
- **Fix**: Idempotency key in payload + unique constraint on (email, animal_id, created_at) for 5-min window

#### 3. **Adopter Records Created on Partial Submission** (Low)
- **Location**: `/public/adoption-applications`
- **Issue**: Adopter record created if visitor enters email even if they don't complete application. Accumulates junk.
- **Fix**: Defer adopter creation until full application submitted, or soft-delete adopters with no applications after X days.

### Performance Issues

#### 1. **N+1 Query Problem** (Medium)
- **Location**: `/animals` list endpoint
- **Issue**: Querying animals doesn't load photos. If client needs photos, triggers query per animal.
- **Fix**: Use SQLAlchemy `selectinload(Animal.photos)` to eager-load.

#### 2. **Analytics Queries Are Slow** (Medium)
- **Location**: `/adoption-requests/analytics`, `/donations/stats`
- **Issue**: Multiple separate queries (COUNT, GROUP_BY, AVG, COUNT filters). Could be 5+ DB round-trips.
- **Fix**: Combine into single query using window functions or denormalize metrics.

#### 3. **No Query Pagination on Large Datasets** (Medium)
- **Location**: `/donations/export` CSV export
- **Issue**: Loads all donations into memory. Could crash on large datasets.
- **Fix**: Stream CSV response row-by-row using generator.

#### 4. **Session Timeout + Inactivity Confusion** (Low)
- **Location**: `src/auth/dependencies.py` session validation
- **Issue**: Tokens expire at issued_time + 30min, but sessions refresh last_activity on every request. Client could extend session indefinitely by staying active.
- **Fix**: Add hard expiry (created_at + 8 hours max) separate from idle timeout (30 min).

### Business Logic Issues

#### 1. **No Animal Availability Check Before Adoption Approval** (Medium)
- **Location**: `/adoption-requests/{id}/status` APPROVED transition
- **Issue**: Can approve adoption for already-adopted animal (if two requests exist). No lock check.
- **Fix**: Check `animal.status != 'adopted'` before approving.

#### 2. **Duplicate Adoption Requests Allowed** (Medium)
- **Location**: `/adoption-requests` POST (staff+ only)
- **Issue**: Can create multiple PENDING requests for same (animal, adopter) pair
- **Fix**: Add UNIQUE(animal_id, adopter_id) WHERE status='pending'

#### 3. **No Sponsorship Limit per Animal** (Low)
- **Location**: `/sponsorships` POST
- **Issue**: Multiple sponsors for same animal allowed (good) but no limit (could have 1000 sponsors for 1 animal).
- **Fix**: Add soft limit (e.g., 100 sponsors) or per-tier limit.

#### 4. **Recurring Donation Cycle Not Validated** (Medium)
- **Location**: `/donations` POST with is_recurring=true
- **Issue**: Recurring interval can be arbitrary (e.g., "1 millennium"). Not validated against Stripe subscription intervals (day/week/month/year).
- **Fix**: Validate recurring_interval enum.

### Incomplete Implementations

#### 1. **Contract PDF Generation** (Unknown)
- **Location**: `/adoption-requests/{id}/contract` POST
- **Issue**: Calls `ContractPDFGenerator.generate()` but implementation not reviewed. Could have issues (missing fields, invalid PDF, etc.)
- **Fix**: Review `src/services/contract_service.py` implementation

#### 2. **Donation Receipt PDF** (Unknown)
- **Location**: `/donations/{id}/receipt` GET
- **Issue**: Calls `donation_receipt_service.generate_receipt()`. Implementation not reviewed.
- **Fix**: Review service implementation

#### 3. **Tigo Money Integration** (Medium Risk)
- **Location**: `/tigo-money/initiate`, `/tigo-money/callback`
- **Issue**: Payment gateway integration. Potential issues in signature verification, webhook handling, state management.
- **Fix**: Test with Tigo Money sandbox; verify webhook signature validation

### Logging & Monitoring

#### 1. **Missing Structured Logging Context** (Low)
- **Location**: Most endpoints
- **Issue**: Logs don't include request_id, user_id, affected resource IDs. Hard to trace requests.
- **Fix**: Use context vars or middleware to inject request_id into all log messages

#### 2. **No Health Check Endpoint** (Low)
- **Location**: `/health` endpoint exists but not reviewed
- **Fix**: Verify it checks DB connectivity, Redis, payment gateway status

### Documentation

#### 1. **Missing API Documentation** (Low)
- **Issue**: No OpenAPI/Swagger docs generated
- **Fix**: FastAPI auto-generates docs at `/docs` (Swagger UI) and `/redoc` (ReDoc). Ensure enabled.

#### 2. **Endpoint Auth Requirements Not Clear** (Medium)
- **Issue**: Some endpoints missing explicit auth documentation
- **Fix**: Add docstrings to all endpoint functions: "Auth: [None | User | Staff+ | Admin | Vet]"

---

## Test Coverage Analysis

### Files with Tests

Found ~30 integration test files in `tests/integration/`:
- `test_auth.py` — Login, user creation, password reset
- `test_adoption_requests.py` — Adoption request CRUD + status transitions
- `test_donations.py` — Donation creation, Stripe intent, webhook handling
- `test_sponsorships.py` — Sponsorship CRUD
- `test_subscriptions.py` — Subscription CRUD
- `test_animals.py` (likely) — Animal CRUD
- `test_vet_visits.py` (likely) — Medical records
- `test_vaccinations.py` — Vaccination records
- `test_surgeries.py` — Surgery records
- `test_gdpr_export.py` — GDPR data export
- `test_gdpr_deletion.py` — GDPR deletion workflow
- `test_public_adoption.py` — Public adoption applications
- `test_public_contact.py` — Public contact forms
- `test_notifications.py` — Notification CRUD + preferences
- `test_impact_reports.py` — Report generation
- `test_fund_allocations.py` — Fund allocation tracking
- `test_account_lockout.py` — Account lockout after failed login
- `test_password_reset.py` — Password reset workflow
- `test_email_verification.py` (likely) — Email verification
- `test_event_bus.py` — Domain event publishing
- `test_webhooks.py` — Stripe/Tigo webhook handling

### Likely Gaps
- No tests for appointment scheduling
- No tests for vet referral workflow
- No tests for medication validation / drug interactions
- No tests for concurrent adoption requests (race condition)
- No tests for contract PDF generation
- No tests for receipt PDF generation
- No tests for rate limiting (would need RateLimiter mock)
- No tests for session timeout/expiry

---

## Summary of Critical Issues

### Must Fix (P0)
1. ⚠️ **Timing attack on auth**: Use constant-time comparison for non-existent users
2. ⚠️ **SEPA payment method enumeration**: Require auth on `/donations/sepa/payment-methods/{customer_id}`
3. ⚠️ **No validation on animal availability before adoption**: Check animal.status before approving
4. ⚠️ **Audit logs mutable**: Implement append-only policy

### Should Fix (P1)
1. ⚠️ **No CAPTCHA on public forms**: Add reCAPTCHA to `/public/contact`, `/public/animals/{id}/inquiries`
2. ⚠️ **File upload security**: Validate file types, enforce size limits, add antivirus scanning
3. ⚠️ **Password reset doesn't invalidate sessions**: Clear all active sessions after reset
4. ⚠️ **N+1 query on animals list**: Use eager loading for photos
5. ⚠️ **Analytics queries slow**: Combine into single query with window functions
6. ⚠️ **Duplicate adoption requests allowed**: Add UNIQUE constraint

### Nice to Have (P2)
1. Input validation (email, phone, URLs)
2. Session timeout clarity (hard expiry vs idle timeout)
3. Structured logging with request_id context
4. Event persistence / durable queue
5. Rate limiting on password reset / email resend

---

## Conclusion

The Refugio Animal Paraguay backend is **well-architected** with good separation of concerns, async-first design, domain-driven events, and GDPR compliance. However, there are **6-8 security issues** (mostly medium severity) and **8-10 performance/data quality issues** that should be addressed before production.

**Recommended Next Steps**:
1. Review contract PDF + receipt PDF generation services (not fully analyzed)
2. Test Tigo Money integration with sandbox
3. Add CAPTCHA to public forms
4. Implement constant-time auth comparison
5. Add file upload validation + scanning
6. Fix N+1 query on animals endpoint
7. Implement hard session expiry
8. Add comprehensive test coverage for edge cases (concurrency, race conditions)

