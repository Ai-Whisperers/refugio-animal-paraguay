# Exemplar: Good Feature

This is a well-written feature. Use it as a calibration reference when writing or reviewing features.

---

# [FEAT-4] Donation Submission Form (EUR + PYG)

## Parent Epic
[EPIC-2] Donor Management & EU Fundraising

## Overview
**Description**: Donors can submit one-time or recurring donations via a web form, paying with credit card (EUR) or receiving bank transfer instructions (PYG). The form collects minimal PII and presents GDPR consent clearly.

**User value**: Donors can contribute from anywhere in the world without needing to contact the shelter.

**Business value**: Converts website visitors into donors. Reduces staff time spent handling donation inquiries.

## User Stories
- [ ] [US-10] Anonymous donor can make a one-time EUR donation by card
- [ ] [US-11] Donor can choose a recurring monthly amount
- [ ] [US-12] Paraguayan donor can request bank transfer details for PYG donation
- [ ] [US-13] EU donor sees and accepts GDPR consent at checkout
- [ ] [US-14] Donor receives email confirmation after successful payment

## Acceptance Criteria (Feature Level)
The feature is complete when:
- [ ] EUR card payments process successfully via Stripe (test mode validated)
- [ ] PYG bank transfer instructions are displayed clearly after form submission
- [ ] GDPR consent is recorded with timestamp for all EU donors
- [ ] Confirmation emails arrive within 5 minutes of payment
- [ ] Form is accessible (WCAG 2.1 AA) and works on mobile
- [ ] No donor PII is logged in application logs

## Definition of Done
- [ ] All 5 user stories complete and validated in staging
- [ ] Stripe webhook handling tested (success, failure, chargeback)
- [ ] GDPR consent storage verified by data model review
- [ ] Email delivery tested with real SMTP (not mock) in staging
- [ ] Security review: no card data touches our servers (Stripe.js handles it)
- [ ] Product owner has made a test donation and confirmed UX
- [ ] Load test: form handles 50 concurrent submissions without errors

## Dependencies
- Depends on: Auth system — donors can optionally log in (but anonymous also supported)
- Depends on: Email service — for confirmation emails
- Blocks: FEAT-5 (donor portal) — needs donations to exist

## Risks
- Risk: Stripe's EU SCA (Strong Customer Authentication) adds friction → Mitigation: Enable Stripe's built-in SCA handling; test with EU test cards
- Risk: PYG exchange rate display may be stale → Mitigation: Show rate with "as of [date]" and link to central bank; don't promise a fixed rate
