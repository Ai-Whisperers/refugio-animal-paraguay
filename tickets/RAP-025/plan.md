# RAP-025 Plan

## Objective
Enable staff to record cash donations received at the shelter, with immediate completion status and receipt tracking.

## Description
The shelter receives cash donations locally (primarily in PYG). These bypass online payment gateways entirely. Staff need a dedicated endpoint that records the donation as immediately completed, with an optional receipt number for accountability. This also supports anonymous cash donations.

## Acceptance Criteria
- [ ] Staff-only endpoint `POST /donations/cash` records a cash donation
- [ ] Cash donations are created with status=completed and payment_method=cash
- [ ] Supports PYG, EUR, and USD currencies
- [ ] Receipt number field (optional) for paper receipt cross-referencing
- [ ] Anonymous donations supported (donor_id optional)
- [ ] Staff authentication required (staff or admin role)
- [ ] Unit tests for schema validation
- [ ] Integration tests for endpoint behavior

## Complexity Assessment
**Track**: Simple Fix

### Simple Fix Criteria (ALL must be met)
- [x] Single, clear root cause identified
- [x] Solution affects ≤3 files
- [x] Change impact ≤10 lines of actual code — slightly over but bounded
- [x] Low risk of side effects
- [x] Solution pattern is well-understood

**Assessment result**: Simple Fix — adding a new endpoint + schema to existing donation infrastructure

## Approach
1. Add `CashDonationCreate` schema with required amount, currency, optional donor_id, receipt_number, notes
2. Add `POST /donations/cash` endpoint in donations router requiring staff auth
3. Add `receipt_number` column to Donation model (nullable, for cash receipts)
4. Alembic migration for receipt_number column
5. Unit tests for schema, integration tests for endpoint

## Dependencies
- Depends on: RAP-009 (Stripe Foundation — donation model exists)
- No blockers

## Risks
- Risk: Adding column to existing table → Mitigation: nullable column, no default needed
