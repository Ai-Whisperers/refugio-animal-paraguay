---
story: S8
epic: EPIC-77
ticket: RAP-514
title: "Voucher expiry and refund policy"
status: ready
points: 3
priority: P2
track: Backend
sprint: 11
version: V1
created: 2026-03-27T20:00:00
---

# S8: Voucher expiry and refund policy

## Story
As a **system**, I want **to automatically handle voucher expiry and refunds** so that **donors get refunded for unused vouchers and donors are notified**.

## Description
Implement automated expiry handling for vouchers and refund logic when vouchers expire without being used.

## Acceptance Criteria
- [ ] Voucher expiry: each voucher has expires_at = purchased_at + 90 days
- [ ] Cron job (daily): check for vouchers with status=purchased or status=claimed and expires_at < now(), set status=expired
- [ ] Expiry email to donor: when voucher expires, send email "Your voucher has expired" with: voucher code, clinic name, service type, notice that refund will be processed
- [ ] Expiry email to rescuer: if voucher was claimed (status=claimed), notify rescuer that claimed voucher expired and was not used
- [ ] Auto-refund logic: upon expiry of purchased voucher, trigger refund to donor's original payment method within 5 business days
- [ ] Refund mechanism: query Donation record to get payment_method (stripe|sepa), if Stripe refund via Stripe API, if SEPA create reverse transaction (manual or automated)
- [ ] Admin override to extend expiry: admin can extend voucher expiry by 30 days if needed, stores reason for extension
- [ ] Admin override to refund: admin can manually initiate refund with reason, sets status=refunded, refund_reason field
- [ ] Refund audit trail: maintain record of all refunds with: reason, timestamp, who initiated
- [ ] Bulk refund report: admin can view all refunds processed, total amount, payment method breakdown
- [ ] Manual refund endpoint: POST /admin/vouchers/{code}/refund with body {reason, extend_days}, processes refund immediately
- [ ] Refund confirmation: donor receives email confirmation of refund with amount and timing
- [ ] Prevention of re-use: once status=expired or status=refunded, voucher cannot be claimed or redeemed
- [ ] Expiry date display: on all voucher displays, show expiry date prominently (e.g., "Expires in 45 days")

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage) - test expiry detection, refund logic, admin override
- [ ] Integration test: voucher expires after 90 days and status changes to expired
- [ ] Integration test: refund triggered on Stripe payment
- [ ] Integration test: refund triggered on SEPA payment (mocked)
- [ ] Integration test: admin can extend expiry
- [ ] Integration test: admin can manually refund
- [ ] Integration test: expired voucher cannot be claimed
- [ ] Cron job test: verify daily job runs and expires vouchers
- [ ] Email test: verify expiry and refund confirmation emails sent
- [ ] Deployed to staging and verified

## Technical Notes
- Cron job: use celery beat or APScheduler to run daily at 2 AM UTC
- Cron query: SELECT * FROM vet_vouchers WHERE status IN ('purchased', 'claimed') AND expires_at < NOW()
- Stripe refund: use Stripe API refund endpoint with payment_intent_id from Donation record
- SEPA refund: create reverse transaction (may require manual processing or bank API integration)
- Refund status: store refund_status on Donation record, track payment_status field
- Email templates: expiry_email.html, refund_confirmation.html
- Admin endpoint: POST /admin/vouchers/{code}/refund requires admin auth
- Audit logging: log all refund operations with user_id, timestamp, reason
- Bulk refund report: GET /admin/vouchers/refunds with date range filters, export as CSV
- Prevent re-use: check status != 'expired' and status != 'refunded' before allowing claim/redeem

## Story Points: 3
