# Backend Issues Summary — Quick Reference

## Critical Security Issues (P0 — Fix Before Production)

### 1. Timing Attack on Auth (`/auth/token`)
- **File**: `src/api/auth.py:40-121`
- **Issue**: Login endpoint checks lockout AFTER password verification for known users. Attackers can enumerate valid emails by timing response.
- **Severity**: Medium
- **Fix**: Use constant-time bcrypt verification even for non-existent users, or restructure to verify lockout before any user lookup.
- **Effort**: 1-2 hours

### 2. SEPA Payment Method Enumeration (`/donations/sepa/payment-methods/{customer_id}`)
- **File**: `src/api/sepa.py`
- **Issue**: Public endpoint allows unauthenticated enumeration of payment methods by guessing customer IDs.
- **Severity**: Medium
- **Fix**: Require JWT auth + customer ownership check.
- **Effort**: 30 minutes

### 3. Animal Adoption Race Condition
- **File**: `src/api/adoption_requests.py:226-250`
- **Issue**: No check that animal isn't already adopted when approving adoption. If two requests exist, second approval still succeeds.
- **Severity**: Medium (business logic)
- **Fix**: Add `if animal.status == 'adopted': raise 422` before status change.
- **Effort**: 15 minutes

### 4. Audit Logs Mutable
- **File**: `src/api/admin.py`, `src/db/models/audit_log.py`
- **Issue**: Audit logs can be deleted (no write-once policy). Staff could cover tracks.
- **Severity**: Low (but compliance risk)
- **Fix**: Implement append-only table + backup archive strategy.
- **Effort**: 2-3 hours

---

## High-Impact Issues (P1 — Fix Before MVP)

### 5. No CAPTCHA on Public Forms
- **Files**: `src/api/public_contact.py`, `src/api/public_adoption.py`
- **Issue**: Contact forms spam-vulnerable. Public adoption endpoint has 10/hour rate limit (good) but contact form has none.
- **Severity**: Medium
- **Fix**: Add reCAPTCHA v3 to public forms.
- **Effort**: 2-3 hours

### 6. File Upload Validation Missing
- **File**: `src/api/medical_documents.py`
- **Issue**: No file type, size, or malware validation on document uploads.
- **Severity**: Medium
- **Fix**: Whitelist file types (.pdf, .jpg, .png), enforce max 10MB, add antivirus scan (e.g., ClamAV).
- **Effort**: 3-4 hours

### 7. Password Reset Doesn't Invalidate Sessions
- **File**: `src/api/password_reset.py`
- **Issue**: Old sessions remain valid after password reset. Attacker with old token can continue.
- **Severity**: Medium
- **Fix**: Call `SessionService.revoke_all_user_sessions(user_id)` on password reset confirmation.
- **Effort**: 30 minutes

### 8. Duplicate Adoption Requests Allowed
- **File**: `src/api/adoption_requests.py:178-223`
- **Issue**: Multiple PENDING requests for same (animal, adopter) pair allowed.
- **Severity**: Low (UX issue)
- **Fix**: Add UNIQUE(animal_id, adopter_id) WHERE status='pending' constraint.
- **Effort**: 15 minutes + migration

### 9. N+1 Query on Animals List
- **File**: `src/api/animals.py:46-61`
- **Issue**: If client needs photos for each animal, results in 1 + N queries (1 animals query + 1 per animal for photos).
- **Severity**: Low (performance)
- **Fix**: Use SQLAlchemy `selectinload(Animal.photos)` in query.
- **Effort**: 15 minutes

### 10. Analytics Queries Are Slow
- **Files**: `src/api/adoption_requests.py:93-161`, `src/api/donations.py` (stats endpoint)
- **Issue**: Multiple separate queries (COUNT, GROUP_BY, AVG, COUNT filters). Could be 5+ DB round-trips for one response.
- **Severity**: Low (performance, scales badly)
- **Fix**: Combine into single query using window functions or denormalize metrics table.
- **Effort**: 2-3 hours per endpoint

---

## Moderate Issues (P2 — Fix in Next Sprint)

### 11. Session Timeout Confusion
- **File**: `src/auth/dependencies.py:46-57`
- **Issue**: Tokens expire at issued_at + 30min (hard), but sessions refresh last_activity on every request. With idle timeout of 30min, session effectively never expires if user stays active.
- **Severity**: Low (security/UX)
- **Fix**: Add hard expiry (created_at + 8 hours) separate from idle timeout.
- **Effort**: 1 hour

### 12. Missing Input Validation
- **Files**: Multiple (animals.py, adopters.py, donors.py, etc.)
- **Issue**: URLs, emails, phone numbers not validated before storage.
  - `animals.primary_photo_url` — no URL validation
  - `adopters.email`, `donors.email` — no email format check
  - `adopters.phone` — no E.164 format check
- **Severity**: Low (data quality)
- **Fix**: Use Pydantic validators (EmailStr, HttpUrl, constr(regex=...)).
- **Effort**: 3-4 hours total

### 13. Webhook Dead-Letter Queue Missing
- **File**: `src/api/webhooks.py`
- **Issue**: Failed webhook handlers are logged but not retried. If handler crashes, event lost (though Stripe retries webhook delivery).
- **Severity**: Low (reliability)
- **Fix**: Store failed webhooks in DLQ table, implement retry queue.
- **Effort**: 4-5 hours

### 14. Email Verification Resend Rate Limit Missing
- **File**: `src/api/email_verification.py`
- **Issue**: No rate limit on `/auth/email/resend`. Attacker could spam resend requests.
- **Severity**: Low
- **Fix**: Add per-email rate limit (e.g., 3 resends/hour).
- **Effort**: 30 minutes

### 15. Password Reset Rate Limit Missing
- **File**: `src/api/password_reset.py`
- **Issue**: No rate limit on `/auth/password-reset/request`. Could enumerate accounts via timing + spam.
- **Severity**: Low
- **Fix**: Add per-email rate limit (e.g., 3 requests/hour).
- **Effort**: 30 minutes

### 16. No Structured Logging Context
- **File**: All endpoints
- **Issue**: Logs missing request_id, user_id, resource IDs. Hard to trace requests through system.
- **Severity**: Low (observability)
- **Fix**: Use contextvars to inject request_id into all log statements via RequestIDMiddleware.
- **Effort**: 2-3 hours

### 17. Adopter Records Created on Partial Submission
- **File**: `src/api/public_adoption.py:75-95`
- **Issue**: Adopter created if visitor enters email even if form not completed. Accumulates junk.
- **Severity**: Very Low (data quality)
- **Fix**: Defer adopter creation or soft-delete adopters with no completed applications after X days.
- **Effort**: 1-2 hours

### 18. CSV Export Not Streamed (Memory Risk)
- **File**: `src/api/donations.py` (GET /donations/export)
- **Issue**: Loads all donations into memory before streaming. Could crash on large datasets.
- **Severity**: Very Low (scales badly)
- **Fix**: Use generator + StreamingResponse to stream rows one-by-one.
- **Effort**: 1 hour

---

## Unknown Issues (Need Code Review)

### 19. Contract PDF Generation
- **File**: `src/services/contract_service.py` (not fully reviewed)
- **Issue**: Missing fields? Invalid PDF generation? Untested edge cases?
- **Fix**: Review implementation + add tests.
- **Effort**: 2-3 hours

### 20. Donation Receipt PDF Generation
- **File**: `src/services/donation_receipt_service.py` (not fully reviewed)
- **Issue**: Similar to contract PDF.
- **Fix**: Review implementation + add tests.
- **Effort**: 2-3 hours

### 21. Tigo Money Integration
- **File**: `src/api/tigo_money.py`, `src/services/tigo_money_service.py`
- **Issue**: Payment gateway integration. Potential issues in webhook verification, state management, error handling.
- **Severity**: Unknown
- **Fix**: Test with Tigo Money sandbox. Verify webhook signature validation matches Tigo's spec.
- **Effort**: 4-5 hours

---

## Issues by Effort

### Quick Wins (< 1 hour)
- [#7] Password reset: Call revoke_all_sessions (30 min)
- [#8] Add UNIQUE constraint for duplicate adoptions (15 min + migration)
- [#9] Add eager loading for animal photos (15 min)
- [#14] Email resend rate limit (30 min)
- [#15] Password reset rate limit (30 min)

### Medium (1-2 hours)
- [#1] Constant-time auth comparison (1-2 hours)
- [#2] SEPA auth requirement (30 min)
- [#3] Animal adoption race condition (15 min)
- [#4] Session timeout hard expiry (1 hour)
- [#11] Input validation (3-4 hours)
- [#18] CSV export streaming (1 hour)

### Larger (2-5 hours)
- [#5] CAPTCHA on public forms (2-3 hours)
- [#6] File upload validation (3-4 hours)
- [#10] Analytics query optimization (2-3 hours per endpoint)
- [#13] Webhook DLQ + retry (4-5 hours)
- [#16] Structured logging (2-3 hours)
- [#19-21] Code review + testing (2-5 hours each)

### Infrastructure (4+ hours)
- [#4] Audit log append-only (2-3 hours)

---

## Test Coverage Gaps

**Test Files Exist**: ~30 integration tests covering most happy paths

**Missing Tests**:
- ⚠️ **Concurrency**: Race condition on adoption approval (animal already adopted)
- ⚠️ **Edge cases**: Duplicate adoption requests, same email multiple times
- ⚠️ **Webhook reliability**: Failed handlers, retry logic
- ⚠️ **Rate limiting**: Verify slowapi limits actually work
- ⚠️ **Contract/Receipt PDFs**: No tests for PDF generation
- ⚠️ **Payment scenarios**: Refunds, subscription churn, SEPA mandate lifecycle
- ⚠️ **GDPR deletion**: Verify all data actually deleted, no orphaned records
- ⚠️ **Session timeout**: Verify session expires correctly, hard expiry respected

**Recommendation**: Add 5-10 more integration tests covering above scenarios. Effort: 4-6 hours.

---

## Deployment Checklist

Before production:
- [ ] Fix all P0 issues (#1-4)
- [ ] Fix all P1 issues (#5-10)
- [ ] Implement structured logging (#16)
- [ ] Test payment gateways with sandbox (#21)
- [ ] Verify audit log archival strategy (#4)
- [ ] Load test analytics endpoints (#10)
- [ ] Run OWASP ZAP or similar security scan
- [ ] Verify GDPR deletion workflow end-to-end (#11 test)
- [ ] Check backup/recovery procedures for DB
- [ ] Verify error monitoring (Sentry) configured
- [ ] Load test with concurrent adoption requests to catch race condition

---

## Recommendations

### Short Term (This Sprint)
1. Fix timing attack + SEPA enumeration + animal adoption race + duplicate requests (all < 1 hour total)
2. Add CAPTCHA + file upload validation (5-6 hours)
3. Password reset session invalidation (30 min)
4. Rate limits on password reset + email resend (1 hour)

**Total**: ~13 hours (fits in 2-day sprint)

### Medium Term (Next Sprint)
1. N+1 query fix + analytics optimization (3-4 hours)
2. Input validation across board (3-4 hours)
3. Session timeout hard expiry (1 hour)
4. Structured logging (2-3 hours)
5. Code review of contract/receipt/Tigo services (3-5 hours)

**Total**: ~15-20 hours (fits in 1-week sprint)

### Long Term (Roadmap)
1. Audit log append-only (2-3 hours)
2. Event sourcing / durable queue (5-8 hours)
3. Comprehensive test coverage (4-6 hours)
4. Performance denormalization / caching (4-5 hours)

---

## End of Issues Summary

For details, see **BACKEND_API_INVENTORY.md** (full endpoint breakdown).

