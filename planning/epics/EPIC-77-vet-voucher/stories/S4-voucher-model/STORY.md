---
story: S4
epic: EPIC-77
ticket: RAP-510
title: "VetVoucher model and lifecycle API"
status: ready
points: 5
priority: P0
track: Backend
sprint: 11
version: V1
created: 2026-03-27T20:00:00
---

# S4: VetVoucher model and lifecycle API

## Story
As a **system**, I want **to track voucher lifecycle from purchase through redemption** so that **all parties know voucher status and history**.

## Description
Create VetVoucher model with complete lifecycle tracking. Vouchers move through states: purchased -> claimed -> redeemed -> (expired|refunded).

## Acceptance Criteria
- [ ] VetVoucher model/table with columns: id (UUID PK), code (UUID, UNIQUE), donor_id (FK to users), clinic_id (FK to VetClinic), service_id (FK to ClinicService), rescuer_id (FK to users, nullable), animal_id (FK to animals, nullable), status (enum: purchased|claimed|redeemed|expired|refunded), amount_cents (integer), currency (string), purchased_at, claimed_at (nullable), redeemed_at (nullable), expires_at, refunded_at (nullable), refund_reason (string, nullable), created_at, updated_at
- [ ] Status transitions: purchased -> claimed (rescuer claims) or purchased -> expired (after 90 days) or purchased -> refunded (admin/automatic). claimed -> redeemed (clinic redeems) or claimed -> expired. redeemed and expired are terminal states.
- [ ] GET /api/vouchers endpoint: list all vouchers (different queries for donor/rescuer/clinic views), supports filtering by status, clinic, service type
- [ ] GET /api/vouchers/{code} endpoint: retrieve voucher by code, validates code format (UUID), returns voucher with all details
- [ ] GET /api/vouchers/for-rescuer endpoint: authenticated rescuer sees available vouchers for their area (location-based filtering), returns: code, clinic_name, service_type, amount
- [ ] GET /api/vouchers/for-clinic endpoint: authenticated clinic sees their vouchers by status, supports filtering by status: claimed (ready to redeem), redeemed (completed), expired
- [ ] POST /api/vouchers/{code}/claim endpoint: rescuer claims voucher, requires rescuer auth, sets rescuer_id=current_user, status=claimed, claimed_at=now(), returns confirmation
- [ ] POST /api/vouchers/{code}/redeem endpoint: clinic redeems voucher, requires clinic auth, validates status=claimed, sets status=redeemed, redeemed_at=now(), requires animal_id and proof_photo_id, returns confirmation
- [ ] POST /api/vouchers/{code}/refund endpoint: admin refunds voucher, sets status=refunded, refunded_at=now(), refund_reason required, triggers refund to donor's payment method
- [ ] Validation: cannot claim already-claimed voucher, cannot redeem non-claimed voucher, cannot refund already-redeemed voucher
- [ ] Expiry checking: status stays purchased if unclaimed past expiry date (will be marked expired by cron job)
- [ ] API response format: {id, code, donor_id, clinic_id, rescuer_id, animal_id, status, amount_cents, currency, purchased_at, claimed_at, redeemed_at, expires_at, clinic_name, service_type}
- [ ] Audit trail: every status change logged with who made change and timestamp
- [ ] Query optimization: indexes on status, clinic_id, rescuer_id, donor_id, expires_at

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage) - test status transitions, expiry logic, claim/redeem validation
- [ ] Integration test: create voucher, claim as rescuer, redeem as clinic
- [ ] Integration test: expiry transitions handled correctly
- [ ] Integration test: refund flow works
- [ ] Integration test: filtering and listing works for all user types
- [ ] Database migration created with proper indexes
- [ ] Deployed to staging and verified

## Technical Notes
- Backend: FastAPI endpoints for voucher operations
- Database: VetVoucher table with proper constraints and indexes on status, clinic_id, rescuer_id, donor_id, expires_at, code (UNIQUE)
- Status enum: SQLAlchemy Enum type for strict validation
- Timestamps: use UTC datetime for all temporal fields
- Refund mechanism: trigger Stripe refund or reverse SEPA transfer based on original payment method (stored on Donation record)
- Audit logging: create audit_log table or use versioning library to track all changes
- Query optimization: composite index on (clinic_id, status), (rescuer_id, status), (donor_id, status)
- API response: serialize using Pydantic model with proper datetime formatting

## Story Points: 5
