# Refugio Animal Paraguay — Backend Inventory Documentation

This directory contains three comprehensive documents analyzing the complete Refugio Animal Paraguay backend API:

## 📄 Documents

### 1. **BACKEND_API_INVENTORY.md** (50KB)
**Complete endpoint-by-endpoint breakdown**

- All ~130 API endpoints across 41 router modules
- Authentication & authorization model
- Database models & migrations (30 versions)
- For each endpoint:
  - HTTP method and path
  - Required authentication/roles
  - Request/response schema
  - Business logic
  - Database models involved
  - Issues and gaps

**Best for**: Understanding the full API, code review, architecture decisions

### 2. **BACKEND_ISSUES_SUMMARY.md** (11KB)
**Quick reference for critical issues**

- 21 identified issues categorized by severity (P0, P1, P2)
- Issues ranked by effort (quick wins to major refactors)
- Test coverage gaps
- Deployment checklist
- Sprint planning recommendations

**Best for**: Bug fixing, sprint planning, production readiness

### 3. **ENDPOINT_EXAMPLES.md** (14KB)
**API usage examples with curl**

- Real curl commands for all major endpoints
- Request/response JSON examples
- Error response formats
- Testing workflow for manual testing
- Common HTTP status codes

**Best for**: Testing, integration, onboarding new developers

---

## 🚀 Quick Start

### For Code Review
1. Read sections in this order:
   - BACKEND_API_INVENTORY.md → "Overview"
   - BACKEND_API_INVENTORY.md → "Application Setup & Middleware"
   - BACKEND_API_INVENTORY.md → "Core Resources" (Animals, Adopters)
   - BACKEND_ISSUES_SUMMARY.md → "Critical Security Issues" (P0)

### For Bug Fixing
1. Open BACKEND_ISSUES_SUMMARY.md
2. Filter by severity (P0 = must fix, P1 = should fix, P2 = nice to have)
3. Sort by effort (quick wins first)
4. Click into BACKEND_API_INVENTORY.md for full context on specific endpoints

### For Testing
1. Reference ENDPOINT_EXAMPLES.md for curl commands
2. Use the "Testing Workflow" section for end-to-end manual testing
3. Compare your responses with provided JSON examples

---

## 📊 Key Statistics

- **Total Endpoints**: ~130 across 41 routers
- **API Routes**: Auth, Animals, Donations, Adoptions, Medical, Sponsorships, GDPR, Admin
- **Database Tables**: 23 core + audit + notifications
- **Migrations**: 30 versions
- **Security Issues Found**: 6 medium + 4 low severity
- **Performance Issues**: 4 identified
- **Test Files**: ~30 integration tests (good coverage, some gaps)

---

## ⚠️ Critical Issues (Must Fix Before Production)

1. **Timing attack on auth** — `/auth/token` leaks valid user emails via response timing
2. **SEPA payment enumeration** — `/donations/sepa/payment-methods/` allows public API key guessing
3. **Animal adoption race condition** — Multiple concurrent approvals could mark animal adopted multiple times
4. **Audit logs mutable** — No write-once policy; staff could cover tracks

See BACKEND_ISSUES_SUMMARY.md for full severity breakdown + fixes.

---

## 🏗️ Architecture Overview

### Stack
- **Framework**: FastAPI (async)
- **ORM**: SQLAlchemy (async)
- **DB**: PostgreSQL (asyncpg driver)
- **Auth**: JWT (HS256)
- **Payments**: Stripe, SEPA, Tigo Money, cash
- **Email**: SMTP
- **SMS**: Twilio (WhatsApp)
- **Rate Limiting**: slowapi
- **Error Tracking**: Sentry
- **Events**: In-memory async pub/sub (no durability)

### Middleware Stack (Outermost → Innermost)
1. RequestIDMiddleware — Attach request_id to all requests
2. RequestLoggingMiddleware — Log all requests/responses
3. AuditMiddleware — Track write operations (GDPR compliance)
4. CORSMiddleware — Cross-origin resource sharing
5. Rate Limiting (slowapi) — Auth: 5/min, General: 60/min
6. Exception Handlers — Centralized error formatting

### Key Features
- ✅ Soft-delete support (GDPR compliance)
- ✅ Event-driven notifications (email, SMS, in-app)
- ✅ Audit trail for all changes
- ✅ Account lockout (15-min after 5 failed logins)
- ✅ Session tracking (forced logout, timeout)
- ✅ GDPR data export + deletion
- ✅ Rate limiting on sensitive endpoints
- ⚠️ No event durability (in-memory bus only)
- ⚠️ No webhook dead-letter queue
- ⚠️ No hard session expiry (only idle timeout)

---

## 🔐 Security Model

### Roles
- **Public** (unauthenticated): View animals, submit adoption applications, donate
- **Staff**: Manage animals, adoption requests, donations, notifications
- **Admin**: Create users, manage staff, run GDPR operations
- **Vet**: Manage medical records (vaccinations, surgeries, diagnoses)

### Auth Flow
1. Login with email + password → JWT token (30 min expiry)
2. Token includes user_id + JTI (session ID)
3. Every request validates JWT + session (not revoked, not timed out)
4. Failed logins tracked; account locks after 5 failures (15 min lockout)

### Data Protection
- ✅ Passwords hashed with bcrypt
- ✅ JWT signed with HMAC-SHA256
- ✅ Database constraints enforced
- ✅ Input validation via Pydantic
- ⚠️ No column-level encryption at rest
- ⚠️ No in-transit encryption beyond HTTPS

---

## 📈 Performance Characteristics

### Query Performance
- ✅ Indexed on frequently-queried columns (email, status, animal_id)
- ⚠️ N+1 risk on animal photos (see BACKEND_ISSUES_SUMMARY.md)
- ⚠️ Analytics endpoints use 5+ separate queries

### Payload Sizes
- List endpoints paginated (default 20, max 100 items)
- CSV exports not streamed (load entire dataset into memory)
- File uploads not validated for size

### Rate Limiting
- Auth: 5 requests/minute/IP
- General: 60 requests/minute/IP
- Public adoption: 10 applications/hour/IP
- Per-user: No per-user rate limits (relies on IP-based)

---

## 🧪 Testing

### Test Coverage
- ~30 integration tests covering:
  - ✅ Authentication (login, token expiry, lockout)
  - ✅ CRUD operations (animals, donations, adoption requests)
  - ✅ Webhooks (Stripe, Tigo Money)
  - ✅ GDPR workflows (export, deletion)
  - ✅ Notifications

### Test Gaps
- ⚠️ No concurrent/race condition tests (adoption race)
- ⚠️ No webhook retry/DLQ tests
- ⚠️ No contract/receipt PDF generation tests
- ⚠️ No rate limit enforcement tests
- ⚠️ No payment gateway sandbox tests

---

## 📋 Files by Purpose

### API Routers (src/api/)
| File | Endpoints | Auth | Purpose |
|------|-----------|------|---------|
| auth.py | /auth/token, /auth/users, /auth/me | None, Admin, Staff | User authentication |
| animals.py | /animals/* | Public (GET), Staff+ (write) | Animal CRUD |
| adopters.py | /adopters/* | Staff+ | Adopter CRUD |
| adoption_requests.py | /adoption-requests/* | Staff+ | Adoption workflow |
| donations.py | /donations/* | Public (POST), Staff+ (GET) | Donations + Stripe |
| sepa.py | /donations/sepa/* | Public | SEPA Direct Debit |
| tigo_money.py | /tigo-money/* | None | Local PYG payments |
| sponsorships.py | /sponsorships/* | Public (POST), Staff+ (GET) | Animal sponsorships |
| subscriptions.py | /subscriptions/* | Public (POST), Staff+ (GET) | Recurring donations |
| vaccinations.py | /vaccines/*, /animals/{id}/vaccinations/* | Vet+ | Medical records |
| surgeries.py | /animals/{id}/surgeries/* | Vet+ | Surgery records |
| vet_visits.py | /animals/{id}/vet-visits/* | Vet+ | Vet visit logs |
| gdpr.py | /gdpr/deletion-request | User (auth) | GDPR deletion |
| gdpr_export.py | /gdpr/data-export | User (auth) | GDPR data export |
| public.py | /public/animals* | Public | Public animal listings |
| public_adoption.py | /public/adoption-applications | Public | Public adoption app |
| public_contact.py | /public/contact, /public/animals/{id}/inquiries | Public | Contact forms |
| admin.py | /admin/audit-logs, /admin/audit-logs/export | Staff+ | Audit logs |

### Core Services (src/services/)
| Service | Purpose |
|---------|---------|
| account_lockout_service.py | Track failed logins, enforce lockout |
| session_service.py | Create/validate/refresh sessions (JWT + DB) |
| email_verification_service.py | Generate/validate email verification tokens |
| password_reset_service.py | Password reset workflow |
| notification_service.py | Email + SMS notification dispatch |
| donation_receipt_service.py | PDF receipt generation |
| contract_service.py | Adoption contract PDF |
| gdpr_export_service.py | Export user data as JSON/ZIP |
| gdpr_deletion_service.py | Delete all user data (async) |
| sepa_notification_service.py | SEPA-specific email notifications |
| post_op_checklist_service.py | Post-surgery follow-up checklist |
| sponsorship_service.py | Sponsorship lifecycle |
| subscription_service.py | Recurring donation lifecycle |

### Database Models (src/db/models/)
23 core tables + relationships defined as SQLAlchemy ORM models.
See BACKEND_API_INVENTORY.md → "Database Models & Migrations" for full schema.

---

## 🚢 Deployment Checklist

Before going to production:

### Must Fix (P0)
- [ ] Fix timing attack on auth
- [ ] Add auth requirement to SEPA endpoints
- [ ] Fix animal adoption race condition
- [ ] Implement audit log immutability

### Should Fix (P1)
- [ ] Add CAPTCHA to public forms
- [ ] Add file upload validation
- [ ] Invalidate sessions on password reset
- [ ] Add UNIQUE constraint for duplicate adoption requests
- [ ] Fix N+1 query on animal photos

### Nice to Have (P2)
- [ ] Input validation (email, phone, URLs)
- [ ] Session timeout hard expiry
- [ ] Structured logging with request_id
- [ ] Event persistence / durable queue
- [ ] Rate limiting on password reset

### Infrastructure
- [ ] HTTPS/TLS enabled
- [ ] Database backup + recovery tested
- [ ] Sentry error monitoring configured
- [ ] Email service verified (SMTP)
- [ ] Stripe/Tigo Money sandbox tested
- [ ] Load testing (concurrent adoptions, large exports)
- [ ] OWASP ZAP security scan
- [ ] Database indexing reviewed

---

## 📞 Support

For detailed analysis of a specific endpoint:
1. Open BACKEND_API_INVENTORY.md
2. Search for the endpoint (e.g., "POST /donations")
3. Review the full section including issues

For troubleshooting a specific issue:
1. Open BACKEND_ISSUES_SUMMARY.md
2. Find issue by number or keyword
3. Follow the "Fix" recommendation
4. See estimated effort

For API testing:
1. Open ENDPOINT_EXAMPLES.md
2. Copy curl command for endpoint
3. Adjust token/IDs as needed
4. Compare response with provided examples

---

**Generated**: 2026-03-27  
**Status**: Complete backend analysis with 21 identified issues  
**Next Steps**: Fix P0 issues, add CAPTCHA, validate file uploads, test Tigo integration

